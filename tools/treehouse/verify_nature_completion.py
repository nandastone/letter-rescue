"""Nature question animation boundaries and post-win native full frames."""
from pathlib import Path
from io import BytesIO
import argparse,base64,hashlib,json,struct
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False);report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],pixels={},errors=[])
    with sync_playwright()as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri());page.evaluate("resident.ambientEnabled=false;setScene('nature');nature.mode='quiz'")
        def model(path):
            r=path.with_suffix('.ram-0').read_bytes();u=lambda at:struct.unpack_from('<H',r,at)[0];cards=struct.unpack_from('<16H',r,0x318b6);py,px=struct.unpack_from('<hh',r,0x34454)
            return dict(cards=[cards[:8],cards[8:]],secret=list(struct.unpack_from('<2H',r,0x32242)),player=u(0x37640),asked=list(struct.unpack_from('<2H',r,0x376cc)),remaining=list(struct.unpack_from('<2H',r,0x376de)),available=[i for i in range(8)if u(0x37692+2*i)],pointer=[px,py])
        def compare(name,path):
            page.evaluate('render()');image=Image.open(BytesIO(base64.b64decode(page.locator('#game').evaluate('c=>c.toDataURL()').split(',')[1]))).convert('RGB');ref=Image.open(path.with_suffix('.png')).convert('RGB');delta=ImageChops.difference(image,ref);n=sum(a!=b for a,b in zip(image.getdata(),ref.getdata()));report['pixels'][name]=dict(exact=n==0,different_pixels=n,bounds=delta.getbbox());image.save(output/f'{name}.png');delta.save(output/f'{name}-difference.png')
        for count in [10,11,12]:
            path=DATA/f'research-nature-audit/question-native-c/state/count-{count}';m=model(path);m['count']=count
            reached=page.evaluate('''m=>{nature.quiz=new NatureQuiz(nature,{character:()=>character,speak:()=>0});const q=nature.quiz;Object.assign(q,m,{phase:'question',options:false,selectedAttribute:1});q.run(q.question(1));for(let t=1;t<2000&&q.actorScript&&q.actorScript.frameUpdates<m.count;t++)q.update(t);treehouseDemo.setPointer(400,400,false);return q.actorScript?.frameUpdates===m.count;}''',m)
            report['checks'].append(dict(name=f'question reaches original display {count}',passed=reached));compare(f'question-{count}',path)
        for name,relative in [('second-animal','research-nature-completion/capture-a/state/second-animal'),('robot-inspected','research-nature-audit/postwin-native/state/robot-card-inspected'),('wrong-guess','research-nature-completion/capture-a/state/wrong-guess')]:
            path=DATA/relative;m=model(path);won=name!='wrong-guess'
            page.evaluate('''m=>{nature.quiz=new NatureQuiz(nature,{character:()=>character,speak:()=>0});const q=nature.quiz;Object.assign(q,m,{phase:m.won?'won':'answered',options:false,winner:m.won?0:-1,winStage:m.won?'done':null,revealed:m.won?3:0,visibleQuestions:[],selected:m.inspect?0:-1});treehouseDemo.setPointer(...m.pointer);}''',{**m,'won':won,'inspect':name=='robot-inspected'})
            compare(name,path)
        report['passed']=not report['errors']and all(c['passed']for c in report['checks'])and all(v['exact']for v in report['pixels'].values());browser.close()
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
