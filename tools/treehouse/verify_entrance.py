"""Compare each independently rendered entrance pose with captured DOS frames.

This checks image membership, not callback alignment or timing parity.
"""
import argparse
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]


def verify(html, output):
    native = ROOT / "testing/output/treehouse/entry-verified-a/frames.jsonl"
    refs = {r["rgb_sha256"] for r in map(json.loads, native.read_text().splitlines()[1831:2460])}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        page.add_init_script("requestAnimationFrame=()=>0;")
        page.goto(html.resolve().as_uri())
        page.evaluate("exterior.credit=2;treehouseDemo.enter('boy')")
        states = page.evaluate("""async()=>{
          const out=[];let previous='';
          for(let i=0;i<1600&&entering;i++){
            render();const key=animations.map(a=>a.id+':'+a.frameUpdates).join(',');
            if(key!==previous){
              const rgba=screen.image.data,rgb=new Uint8Array(64000*3);
              for(let p=0;p<64000;p++)rgb.set(rgba.subarray(p*4,p*4+3),p*3);
              const digest=await crypto.subtle.digest('SHA-256',rgb);
              out.push({tick,key,sha256:Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('')});
              previous=key;
            }
            advance(1);
          }
          return out;
        }""")
        reached_inside = page.evaluate("scene==='inside'")
        browser.close()
    for state in states:
        state["exact_native_image"] = state["sha256"] in refs
    report = dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),
                  comparison="Full RGB image membership; not timing parity", states=states,
                  exact=sum(s["exact_native_image"] for s in states), total=len(states),
                  reached_inside=reached_inside)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='states'}, indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html',type=Path,default=ROOT/'testing/output/treehouse/playable/index.html')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    verify(args.html,args.output)
