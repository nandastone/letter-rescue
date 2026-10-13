"""Compare the original theater sentence at a word-wrap boundary."""
from pathlib import Path
import argparse,hashlib,json,struct,sys
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
REFERENCE=ROOT/'testing/output/treehouse/theater-native-journey-e/state/storm.png'

def verify(html,output):
    output.mkdir(parents=True,exist_ok=False)
    ram=REFERENCE.with_suffix('.ram-0').read_bytes();y,x=struct.unpack_from('<hh',ram,0x323f0+0x2064)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),reference=str(REFERENCE),
                reference_sha256=hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),errors=[])
    with sync_playwright() as p:
        b=p.chromium.launch(channel='msedge',headless=True);page=b.new_page()
        page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto(html.resolve().as_uri())
        page.evaluate('''point=>{setScene('theater');theater.mixUp=theater.propsEnabled=true;theater.start();
            [0,0,2,3].forEach((v,c)=>theater.choose(c,v));advance(300);
            treehouseDemo.setPointer(...point);render();}''',[x,y])
        actual=Image.frombytes('RGBA',(320,200),bytes(page.evaluate('treehouseDemo.pixels()'))).convert('RGB');b.close()
    expected=Image.open(REFERENCE).convert('RGB');delta=ImageChops.difference(actual,expected)
    count=sum(a!=b for a,b in zip(actual.getdata(),expected.getdata()))
    actual.save(output/'storm.png');delta.save(output/'difference.png')
    report.update(passed=not report['errors'] and count==0,pixels=dict(storm=dict(exact=count==0,different_pixels=count,bounds=delta.getbbox())),
                  scope='Complete RGB comparison of a stable theater sentence with a separator just beyond the first-line width. Uses the real theater renderer; no timing or full-journey claim.')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2));return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output) else 1)
