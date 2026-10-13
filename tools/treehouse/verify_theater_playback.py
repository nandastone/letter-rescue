"""Check reconstructed theater display changes against the ordered native replay.

Original callbacks include partial drawing transfers. This reports unmatched
images and timing separately; it never treats a close image as an exact match.
"""
from pathlib import Path
import argparse
import hashlib
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(html,output):
    native=ROOT/'testing/output/treehouse/theater-night/frames.jsonl'
    frames=[json.loads(line) for line in native.read_text().splitlines()]
    frames=[f for f in frames if 5520<=f['run']<=6000]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0;')
        page.goto(html.resolve().as_uri())
        page.evaluate("setScene('theater');theater.start();[0,0,1,1].forEach((v,c)=>theater.choose(c,v));advance(200);treehouseDemo.setPointer(82,173);theater.play();")
        states=page.evaluate('''async()=>{const states=[];let last='';const start=tick;
          for(let i=0;i<1000;i++){
            render();const rgba=screen.image.data,rgb=new Uint8Array(192000);
            for(let j=0;j<64000;j++)rgb.set(rgba.subarray(j*4,j*4+3),j*3);
            const digest=await crypto.subtle.digest('SHA-256',rgb);
            const hash=Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('');
            if(hash!==last){states.push({tick:tick-start,phase:theater.phase,category:theater.presenting,sha256:hash});last=hash;}
            if(!theater.playing)break;advance(1);
          }return states;}''')
        complete=page.evaluate('!theater.playing&&theater.performances===1')
        browser.close()
    previous=5519
    for state in states:
        matches=[f for f in frames if f['rgb_sha256']==state['sha256']]
        ordered=next((f for f in matches if f['run']>previous),None)
        state['exact_native_image']=bool(matches)
        state['ordered_native_run']=ordered['run'] if ordered else None
        if ordered:previous=ordered['run']
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),completed=complete,
        comparison='Full RGB display changes, ordered matching; callback timing parity not established',
        total=len(states),exact=sum(s['exact_native_image'] for s in states),
        ordered_exact=sum(s['ordered_native_run'] is not None for s in states),states=states)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='states'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html',type=Path,default=ROOT/'testing/output/treehouse/continuation-build/index.html')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();verify(args.html,args.output)
