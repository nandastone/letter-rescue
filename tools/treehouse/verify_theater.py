"""Exercise reconstructed theater and compare complete frames to native captures."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
CASES=[
    ("intro","demo-theater","theater",""),
    ("editor","theater-edit","editor","theater.start();treehouseDemo.advance(250);"),
    ("actors","theater-edit","actors","theater.showChoices(0);"),
    ("baby","theater-baby","baby","theater.choose(0,0);treehouseDemo.advance(250);"),
    ("actions","theater-baby","actions","theater.showChoices(1);"),
    ("bubbles","theater-places","bubbles","theater.choose(1,0);treehouseDemo.advance(200);"),
    ("places","theater-places","places","theater.showChoices(2);"),
    ("jungle","theater-night","jungle","theater.choose(2,1);treehouseDemo.advance(250);"),
    ("times","theater-night","times","theater.showChoices(3);"),
    ("night","theater-night","night","theater.choose(3,1);treehouseDemo.advance(200);"),
]


def verify(html:Path, output:Path)->dict:
    output.mkdir(parents=True,exist_ok=False)
    report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),pixels={},checks=[],errors=[])
    with sync_playwright()as playwright:
        browser=playwright.chromium.launch(channel="msedge",headless=True)
        page=browser.new_page(viewport={"width":1360,"height":960})
        page.on("pageerror",lambda error:report["errors"].append(str(error)))
        page.add_init_script("window.requestAnimationFrame=()=>0;")
        page.goto(html.resolve().as_uri())
        page.evaluate("treehouseDemo.setScene('theater');")
        for name,folder,snapshot,code in CASES:
            reference=ROOT/"testing/output/treehouse"/folder
            run=json.loads((reference/"run.json").read_text())
            ram=(reference/"state"/f"{snapshot}.ram-0").read_bytes()
            y,x=struct.unpack_from("<HH",ram,run["main_image_base"]+0x321d0+0x2064)
            page.evaluate(code+f"treehouseDemo.setPointer({x},{y});treehouseDemo.render();")
            image=Image.frombytes("RGBA",(320,200),bytes(page.evaluate("treehouseDemo.pixels()"))).convert("RGB")
            original=Image.open(reference/"state"/f"{snapshot}.png").convert("RGB")
            delta=ImageChops.difference(image,original)
            count=sum(a!=b for a,b in zip(image.getdata(),original.getdata()))
            image.save(output/f"{name}.png");delta.save(output/f"{name}-difference.png")
            report["pixels"][name]=dict(different_pixels=count,total_pixels=64000,exact=count==0,bounds=delta.getbbox())
        page.screenshot(path=str(output/"theater-browser.png"),full_page=True)

        def check(condition:bool,name:str)->None:
            report["checks"].append(dict(name=name,passed=bool(condition)))
            if not condition:raise AssertionError(name)

        page.evaluate("setScene('inside');")
        page.get_by_role("button",name="Put on a play",exact=True).click()
        page.evaluate("advance(1500)")
        page.get_by_role("button",name="Options",exact=True).click()
        page.locator("#mix-up").check()
        page.locator("#props").check()
        page.get_by_role("button",name="Start the theater",exact=True).click()
        check(page.evaluate("theater.mixUp&&theater.propsEnabled&&!theater.options"),"Readable options start the theater")
        for category,value in enumerate([0,0,1,1]):
            page.locator(f"#theater-part-{category}").select_option(str(value))
        check(page.locator("#fact").inner_text()=="The baby blows bubbles in the jungle at night.","Readable selections form the sentence")
        page.get_by_role("button",name="Perform my sentence",exact=True).click()
        check(page.evaluate("theater.playing&&audio.context.state==='running'&&audio.active.size>0"),"Perform button plays original narration")
        page.evaluate("treehouseDemo.advance(1600);treehouseDemo.render();")
        check(page.evaluate("!theater.playing&&theater.performances===1"),"Readable controls complete a performance")
        page.evaluate("theater.mixUp=false;theater.propsEnabled=false;theater.choose(2,-1);theater.choose(3,-1);")
        for actor in range(8):
            for action in range(8):
                result=page.evaluate("""([actor,action])=>{
                    theater.choose(0,actor);theater.choose(1,action);
                    const before=theater.performances,started=theater.play();
                    for(let i=0;i<1600;i++){treehouseDemo.advance(1);if(i%4===0)treehouseDemo.render();}
                    return started&&!theater.playing&&theater.performances===before+1;
                }""",[actor,action])
                check(result,f"Actor {actor}, action {action}: original script completes")
        for place in range(6):
            for time in range(4):
                result=page.evaluate("""([place,time])=>{
                    theater.choose(2,place);theater.choose(3,time);
                    for(let i=0;i<250;i++){treehouseDemo.advance(1);treehouseDemo.render();}
                    return theater.weatherStart===null;
                }""",[place,time])
                check(result,f"Place {place}, time {time}: palette and weather render")
        check(page.evaluate("theater.choose(0,-1);theater.validation()===3&&!theater.play()"),"Missing subject is rejected")
        check(page.evaluate("theater.choose(0,0);theater.choose(1,-1);theater.validation()===4&&!theater.play()"),"Missing action is rejected")
        check(page.evaluate("theater.choose(1,0);theater.order=[1,0,2,3];theater.validation()===5&&!theater.play()"),"Action before subject is rejected")
        check(page.evaluate("theater.order=[0,2,1,3];theater.validation()===6&&!theater.play()"),"Separated subject and action are rejected")
        check(page.evaluate("theater.order=[3,0,1,2];theater.validation()===0"),"Time before subject is accepted")
        check(page.evaluate("theater.order=[0,1,2,3];theater.choose(2,-1);theater.choose(3,-1);theater.validation()===0"),"Where and when are optional")
        page.evaluate("theater.propsEnabled=true;theater.choose(2,0);theater.showChoices(4);theater.choose(4,0);treehouseDemo.render();")
        check(page.evaluate("theater.props[0].length===1"),"Decoration can be added")
        check(page.evaluate("theater.beginDrag(161,116);theater.moveDrag(200,130);theater.drag=null;theater.props[0][0].x===199"),"Decoration can be dragged")
        page.evaluate("for(let i=0;i<25;i++)theater.addProp(0)")
        check(page.evaluate("theater.props[0].length===20"),"Original twenty-decoration limit is enforced")
        page.evaluate("theater.removeLastProp()")
        check(page.evaluate("theater.props[0].length===19"),"Decoration can be removed")
        check(page.evaluate("theater.choose(2,1);theater.props[1].length===0"),"Decorations are stored per place")
        page.evaluate("theater.choose(2,0);theater.category=-1;treehouseDemo.render();")
        page.set_viewport_size({"width":390,"height":844})
        page.screenshot(path=str(output/"theater-mobile.png"),full_page=True)
        check(page.evaluate("document.documentElement.scrollWidth<=innerWidth"),"Theater mobile layout fits")
        page.get_by_role("button",name="Back",exact=True).click()
        check(page.evaluate("scene==='theater'&&!!theater.presentation?.leaving"),"Back starts the original curtain close")
        page.evaluate("treehouseDemo.advance(32)")
        check(page.evaluate("treehouseDemo.state.scene==='inside'"),"Back leaves the activity")
        check(not report["errors"],"No browser exceptions")
        check(all(item["exact"]for item in report["pixels"].values()),"All ten native theater reference screens match every pixel")
        browser.close()
    report["behavior_passed"]=all(item["passed"]for item in report["checks"])
    report["all_reference_frames_exact"]=all(item["exact"]for item in report["pixels"].values())
    (output/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html",type=Path,default=ROOT/"testing/output/treehouse/playable/index.html")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=verify(args.html,args.output)
    print(json.dumps(dict(checks=len(result["checks"]),passed=result["behavior_passed"],pixels=result["pixels"],errors=result["errors"]),indent=2))
