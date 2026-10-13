"""Full-image editor/print comparisons with recovered JS and native print sheets.

Explicit isolated fixtures cover all 16 note/rest durations, both notation
spellings and score sizes, dragged-note color, seven contents pages, title caret,
and every confirmation face phase. This is rendering/sequence evidence, not a
claim about all input paths, elapsed timing, persistence or device sound.
"""
import argparse,base64,hashlib,io,json,struct,subprocess
from pathlib import Path
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
from build_demo import ROOT


def verify(engine,output):
    output.mkdir(parents=True,exist_ok=False)
    cases=[]
    def raw(mode,d=4,flag=0):
        song=[0]*65;song[mode]=30 if mode else 8;song[2:5]=[3,9,flag]
        for i in range(30):song[5+2*i:7+2*i]=[(i%17)|(flag<<7),d]
        return song
    for mode in range(2):
        for d in range(16):
            for flag in range(2):
                for printing in [False,True]:
                    cases.append(dict(name=f'score-{mode}-{d}-{flag}-{int(printing)}',mode=mode,raw=raw(mode,d,flag),duration=d%8,**{'print':printing}))
        for pitch in range(17):
            r=raw(mode);r[5]=pitch
            cases.append(dict(name=f'drag-{mode}-{pitch}',mode=mode,raw=r,drag=0))
        for page in range(1,8):cases.append(dict(name=f'contents-{mode}-{page}',mode=mode,raw=raw(mode),contents=page))
        for tick in [0,6]:cases.append(dict(name=f'title-{mode}-{tick}',mode=mode,raw=raw(mode),tick=tick,title_entry='My tune'))
        cases.append(dict(name=f'eraser-{mode}',mode=mode,raw=raw(mode),eraser=True,pointer=[150,55]))
    for character in ['boy','girl']:
        for message in ['copy','erase','erase_all','random','print']:
            for phase in range(4):cases.append(dict(name=f'dialog-{character}-{message}-{phase}',mode=0,raw=raw(0),character=character,dialog=message,tick=phase*12))
    native={}
    for folder,name in [('capture-a','long-print'),('capture-short','after-20'),('capture-compose','after-20')]:
        root=ROOT/'testing/output/treehouse/research-print'/folder
        state=json.loads((root/'run.json').read_text())['states'][name]
        ram=(root/'state'/f'{name}.ram-0').read_bytes()
        y,x=struct.unpack_from('<hh',ram,0x323f0+0x2064)
        label='native-'+folder
        c=dict(name=label,mode=int(state['advanced']),enabled=bool(state['composing']),song_id=int(state['selection'][:2],16),raw=state['header']+[v for pair in state['notes'] for v in pair],pointer=[x,y],busy=name=='after-20',**{'print':True})
        if c['enabled']:c['title']=state['title']
        cases.append(c);native[label]=str(root/'state'/f'{name}.png')
    (output/'cases.json').write_text(json.dumps(cases),encoding='utf-8')
    p=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/check_music_editor.gd','--',str(output.resolve())],capture_output=True,text=True,encoding='utf-8',timeout=120)
    log=p.stdout+p.stderr;(output/'godot.log').write_text(log,encoding='utf-8')
    if p.returncode or 'ERROR' in log:raise RuntimeError(log)
    actual=json.loads((output/'godot.json').read_text(encoding='utf-8'))
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0')
        page.goto((ROOT/'testing/output/treehouse/playable/index.html').as_uri())
        expected=page.evaluate('''cases=>{
          audio.start=()=>null;audio.stop=()=>{};const results=[];pointerVisible=false;roomTravel=null;scene='music';
          const messages={copy:'Copy song to your book?',erase:'Erase the whole song?',erase_all:'Erase ALL songs?',random:'Create new song?',print:'Print song?'};
          for(const c of cases){
            Object.assign(musicEditor,new MusicEditor(store));musicEditor.enabled=c.enabled??true;musicEditor.advanced=!!c.mode;
            musicEditor.index=[0,0];musicEditor.books[c.mode][0]=[...c.raw];
            if(c.title)musicEditor.titles[c.mode][0]=musicEditor.encodeTitle(c.title);
            musicEditor.duration[c.mode]=c.duration??4;musicEditor.position=c.position??0;
            musicEditor.eraser=!!c.eraser;
            musicEditor.contents=c.contents||0;musicEditor.drag=c.drag===undefined?null:{kind:'note',index:c.drag};
            musicEditor.titleEntry=c.title_entry===undefined?null:{old:musicEditor.title,value:c.title_entry,start:0};
            tick=c.tick||0;character=c.character||'boy';musicDialog=c.dialog?{message:messages[c.dialog],start:0}:null;musicPrint=null;musicSelector.open=false;
            held.clear();longScore=!!c.mode;songId=c.song_id??20;
            if(!musicEditor.enabled)listeningBooks.songs[c.mode][songId]=[...c.raw];
            instrument=c.raw[3];tempo=c.raw[2];songPlaying=false;songPosition=-1;repeatSong=false;audition=null;musicAuditionPitch=null;musicIdle.frame=-1;
            if(c.print)musicEditor.drawPrint(screen,currentMusicSong(),currentMusicTitle(),instrument,songId);else musicRoom();
            if(c.pointer){const data=c.eraser?bytes(ORIGINAL.raw['th:CURS:2']):c.busy?bytes(ORIGINAL.raw['th:CURS:1']):ORIGINAL.cursor,x=c.pointer[0]-s16(data,2),y=c.pointer[1]-s16(data),foreground=c.eraser?store.palette('modules',2200).rgba[12]:0xff55ffff;for(let row=0;row<16;row++)for(let col=0;col<16;col++)if(!(u16(data,4+row*2)&(0x8000>>>col)))screen.rect(x+col,y+row,1,1,(u16(data,36+row*2)&(0x8000>>>col))?foreground:0xff000000);}
            const canvas=document.createElement('canvas');canvas.width=320;canvas.height=200;canvas.getContext('2d').putImageData(screen.image,0,0);
            results.push({name:c.name,png:canvas.toDataURL().split(',')[1],sequence:songSequence().map(e=>({pitch:e.pitch,source:e.sourceIndex,rest:e.rest,ticks:e.ticks}))});
          }return results;
        }''',cases)
        browser.close()
    checks=[]
    for a,e in zip(actual,expected):
        image=Image.open(output/(a['name']+'.png')).convert('RGB')
        reference=Image.open(io.BytesIO(base64.b64decode(e.pop('png')))).convert('RGB')
        pixels=sum(a!=b for a,b in zip(image.getdata(),reference.getdata()))
        differences={k:dict(actual=a[k],expected=e[k]) for k in e if a[k]!=e[k]}
        if pixels:
            reference.save(output/(a['name']+'-js.png'));ImageChops.difference(image,reference).save(output/(a['name']+'-diff.png'))
        checks.append(dict(name=a['name'],different_pixels=pixels,differences=differences,passed=not pixels and not differences))
    natives={name:Image.open(output/(name+'.png')).convert('RGB').tobytes()==Image.open(path).convert('RGB').tobytes() for name,path in native.items()}
    report=dict(passed=len(actual)==len(cases) and all(c['passed'] for c in checks) and all(natives.values()),checks=checks,native=natives,scope=__doc__,files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'treehouse-godot/scripts').glob('*.gd'))})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(checks),native=natives,failures=[dict(name=c['name'],pixels=c['different_pixels'],fields=list(c['differences'])) for c in checks if not c['passed']]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output) else 1)


