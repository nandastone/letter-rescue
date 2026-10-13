"""Compare Godot listening scores, key displays and complete note dispatch with JS.

Fixtures select each original song in both notation sizes, every piano pitch,
and all contents pages. Compares complete images and complete song event lists
and end ticks. Does not prove native presentation or device audio parity.
"""
import argparse,base64,hashlib,io,json,struct,subprocess
from pathlib import Path
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
from build_demo import ROOT


def verify(engine,output):
    output.mkdir(parents=True,exist_ok=False)
    cases=[dict(name=f'song-{mode}-{song}',mode=mode,song=song) for mode in range(2) for song in range(25)]
    cases += [dict(name=f'key-{mode}-{pitch}',mode=mode,song=20,pitch=pitch) for mode in range(2) for pitch in range(17)]
    cases += [dict(name=f'contents-{page}',mode=0,song=20,contents=page) for page in range(1,5)]
    tables=json.loads((ROOT/'treehouse-godot/data/original.json').read_text(encoding='utf-8'))['music']
    cases.append(dict(name='families',mode=0,song=20,category=-1))
    for category in range(7):
        for info in [category,*tables['followup']['members'][category]]:
            cases.append(dict(name=f'family-{category}-{info}',mode=0,song=20,category=category,info=info,instrument=info))
    native_groups={}
    for name,folder,state,category in [('native-families','ensemble','click-0',-1),('native-animals','ensemble','click-1',0),('native-home-made','homemade','click-0',1),('native-long','menus','click-1',None)]:
        reference=ROOT/'testing/output/treehouse/research-music-followup'/folder
        run=json.loads((reference/'run.json').read_text(encoding='utf-8'))
        ram=(reference/'state'/f'{state}.ram-0').read_bytes()
        y,x=struct.unpack_from('<hh',ram,run.get('main_image_base',544)+0x321d0+0x2064)
        native_groups[name]=dict(reference=str(reference/'state'/f'{state}.png'),cases=[])
        for frame in (range(17) if category is None else [-1]):
            c=dict(name=f'{name}-{frame}',mode=int(category is None),song=20,pointer=[x,y],idle=frame,instrument=11)
            if category is not None:c.update(category=category,info=max(0,category))
            cases.append(c);native_groups[name]['cases'].append(c['name'])
    (output/'cases.json').write_text(json.dumps(cases),encoding='utf-8')
    p=subprocess.run([str(engine),'--headless','--path',str(ROOT/'treehouse-godot'),'--script','testing/check_music.gd','--',str(output.resolve())],capture_output=True,text=True,encoding='utf-8',timeout=180)
    log=p.stdout+p.stderr
    (output/'godot.log').write_text(log,encoding='utf-8')
    if p.returncode or 'ERROR' in log:
        raise RuntimeError(log)
    actual=json.loads((output/'godot.json').read_text(encoding='utf-8'))
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page()
        page.add_init_script('requestAnimationFrame=()=>0')
        page.goto((ROOT/'testing/output/treehouse/playable/index.html').as_uri())
        expected=page.evaluate('''cases=>{
          audio.start=()=>null;audio.stop=()=>{};const results=[];pointerVisible=false;roomTravel=null;scene='music';
          for(const c of cases){
            playPitch=()=>null;
            held.clear();musicEditor.enabled=false;musicEditor.contents=c.contents||0;musicEditor.titleEntry=null;musicDialog=null;musicPrint=null;musicSelector.open=false;
            tick=0;longScore=!!c.mode;songId=c.song;instrument=c.instrument??currentMusicSong()[3];tempo=currentMusicSong()[2];songPlaying=false;songPosition=-1;repeatSong=false;audition=null;musicAuditionPitch=null;musicIdle.frame=c.idle??-1;pointerVisible=!!c.pointer;if(c.pointer)treehouseDemo.setPointer(...c.pointer);
            if(c.category!==undefined){musicSelector.show(c.category);musicSelector.info=c.info||0;musicSelector.fact=0;musicSelector.stillInstrument=-1;instrument=c.instrument??instrument;}
            if(c.pitch!==undefined)noteDown(c.pitch,'mouse');
            render();const canvas=document.createElement('canvas');canvas.width=320;canvas.height=200;canvas.getContext('2d').putImageData(screen.image,0,0);
            const png=canvas.toDataURL().split(',')[1],notes=[];
            playPitch=pitch=>{notes.push({tick,pitch,instrument});return null;};
            startSequence(songSequence(),'fixture');while(songPlaying&&tick<30000){tick++;advanceSong();}
            results.push({name:c.name,sequence:songSequence().map(e=>({pitch:e.pitch,source:e.sourceIndex,rest:e.rest,ticks:e.ticks})),notes,tick,png});
          }return results;
        }''',cases)
        browser.close()
    checks=[]
    for a,e in zip(actual,expected):
        expected_image=Image.open(io.BytesIO(base64.b64decode(e.pop('png')))).convert('RGB')
        image=Image.open(output/(a['name']+'.png')).convert('RGB')
        pixels=sum(x!=y for x,y in zip(image.getdata(),expected_image.getdata()))
        diff={k:dict(actual=a[k],expected=e[k]) for k in e if a[k]!=e[k]}
        if pixels:
            expected_image.save(output/(a['name']+'-js.png'))
            ImageChops.difference(image,expected_image).save(output/(a['name']+'-diff.png'))
        checks.append(dict(name=a['name'],different_pixels=pixels,differences=diff,passed=pixels==0 and not diff))
    for group in native_groups.values():
        native=Image.open(group['reference']).convert('RGB')
        group['matches']=[name for name in group['cases'] if Image.open(output/(name+'.png')).convert('RGB').tobytes()==native.tobytes()]
        group['passed']=bool(group['matches'])
    report=dict(passed=len(actual)==len(cases) and all(c['passed'] for c in checks) and all(g['passed'] for g in native_groups.values()),checks=checks,native=native_groups,scope=__doc__+' Four additional full native menu/score frames; long-score comparison permits the 17 authored idle-eye frames without asserting timing.',files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'treehouse-godot/scripts').glob('*.gd'))})
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(checks),failures=[dict(name=c['name'],pixels=c['different_pixels'],fields=list(c['differences'])) for c in checks if not c['passed']]),indent=2))
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.godot,a.output) else 1)
