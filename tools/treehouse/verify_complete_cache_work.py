"""Whole resident resource work; IRQ placement remains an explicit fixture."""
from pathlib import Path
import argparse, hashlib, json, struct, sys, zipfile
from playwright.sync_api import sync_playwright
from verify_memory_lifetimes import shape_calls
from sound_memory_calls import sound_calls
from memory_catalog import read_catalogs, read_files
from resources import parse_archive
from build_demo import SOURCE_SHA

ROOT=Path(__file__).resolve().parents[2]
MODELS=['memory-work.js','resource-work.js','memory-wrapper-work.js','resource-cache-work.js','timer-work.js']


def verify(memory_path,scene_path,trace_path,timer_path,timer_report_path,output):
    output.mkdir(parents=True,exist_ok=False)
    memory,scene,trace,timer,timer_report=[json.loads(p.read_text()) for p in [memory_path,scene_path,trace_path,timer_path,timer_report_path]]
    if not memory['passed'] or memory['trace_sha256']!=hashlib.sha256(scene_path.read_bytes()).hexdigest():raise ValueError('Unaccepted generated memory')
    for f,digest in memory['models'].items():
        if hashlib.sha256((ROOT/'treehouse-demo'/f).read_bytes()).hexdigest()!=digest:raise ValueError('Stale generated model')
    if not timer_report['passed'] or timer_report['trace_sha256']!=hashlib.sha256(timer_path.read_bytes()).hexdigest() or timer_report['model_sha256']!=hashlib.sha256((ROOT/'treehouse-demo/timer-work.js').read_bytes()).hexdigest():raise ValueError('Unaccepted timer model')
    if any(scene[k]!=other[k] for other in [trace,timer] for k in ['events','boundaries','actions']):raise ValueError('Observer runs differ')
    work=trace['work']
    if work['routine']!='resident:7A66+all' or len(work['calls'])!=2494:raise ValueError('Incomplete resident resource profile')
    initial=(scene_path.parent/scene['heap'][0]['path']).read_bytes()
    catalogs=read_catalogs(initial,13253);files=read_files(initial,13253)
    file_states=[dict(handle=f['handle'],state=struct.unpack_from('<H',initial,13253*16+f['handle'])[0],segment=struct.unpack_from('<H',initial,13253*16+f['handle']+2)[0]) for f in files]
    source=ROOT/'testing/output/treehouse/source/The_Treehouse_1991.zip'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('Unresearched source')
    resources={}
    with zipfile.ZipFile(source) as z:
        for catalog in catalogs:
            data=z.read(f'TheTreeh/{catalog["archive"]}.dat')
            for r in parse_archive(data):
                key=f'{catalog["archive"]}:{r["tag"]}:{r["id"]}'
                resources[key]=dict(selected=catalog['handle'],resource=dict(payload=list(data[r['payload_offset']:r['payload_offset']+r['size']]),checksum=r['checksum'],directoryFlags=int(r['flags_hex'][:2],16)))
    # Lookup identity is used only to join each generated load to its pinned DAT.
    identities={};identity=None
    for e in trace['events']:
        if e['label']=='resource.lookup':identity=((e['ax']+65536*e['dx']).to_bytes(4,'big').strip(b'\0').decode('ascii'),e['cx'])
        if e['label']=='resource.read':
            matches=[c for c in work['calls'] if c['begin']<=e['milliseconds']<=c['end']]
            if len(matches)==1:
                record=next((f'{c["archive"]}:{identity[0]}:{identity[1]}' for c in catalogs if any(r['tag']==identity[0] and r['id']==identity[1] for r in c['records'])),None)
                if record is None:raise ValueError('Unknown resource identity')
                identities[matches[0]['ordinal']]=record
    shapes,_=shape_calls(scene,initial);sounds,_=sound_calls(scene,initial);selected=[]
    for phase,check in list(zip(shapes,memory['shapeChecks']))+list(zip(sounds,memory['soundChecks'])):
        if phase['key']!=check['key'] or not check['passed']:raise ValueError('Generated phase differs')
        calls=[c for c in work['calls'] if phase['milliseconds']<=c['begin'] and c['end']<=phase['end']]
        if len(calls)!=1:raise ValueError('Expected one cache call')
        call=calls[0];s=check['sourceWork'];row=dict(key=phase['key'],call=call,input=s['input'],action=s['action'])
        if s['action']=='load':
            near=next(c for c in memory['nearChecks'] if c['contextTime']==phase['milliseconds'])
            far=next(c for c in memory['allocationChecks'] if c['contextTime']==phase['milliseconds'])
            record=resources[identities[call['ordinal']]]
            if near['bytes']!=4 or far['bytes']!=len(record['resource']['payload']) or far['bytes']!=check['operations'][0]['bytes'] or record['resource']['directoryFlags']!=s['input']['directoryFlags']:raise ValueError('Generated allocation differs from DAT')
            row['cold']=dict(allocation=dict(handle=near['pointer'],blockAddress=far['address']),nearWork=near['work'],farWork=far['work'],catalogs=files,catalogStates=file_states,**record)
        elif s['action']!='cached':raise ValueError('Unreconstructed reload path')
        interrupts=[]
        for irq,state in zip(timer['work']['calls'],timer['work']['timer_states']):
            if call['begin']<=irq['begin'] and irq['end']<=call['end']:
                w=state['before'];interrupts.append(dict(ordinal=irq['ordinal'],state=dict(ticks=w[0]+65536*w[1],countdowns=w[2:6],biosStep=w[6]+65536*w[7],biosPhase=w[8])))
            elif irq['begin']<call['end'] and irq['end']>call['begin']:raise ValueError('Partially overlapping IRQ fixture')
        row['interrupts']=interrupts;selected.append(row)
    if len(selected)!=2478 or sum(s['action']=='load' for s in selected)!=29:raise ValueError('Incomplete generated cache coverage')
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        for f in MODELS:page.add_script_tag(path=str(ROOT/'treehouse-demo'/f))
        generated=page.evaluate('''rows=>rows.map(row=>{
          const base=row.action==='cached'?OriginalResourceCacheWork.resident(row.input):OriginalResourceCacheWork.cold(row.input,row.cold);
          const irqs=row.interrupts.map(i=>new OriginalTimerWork(i.state).tick());
          return {base,complete:OriginalResourceCacheWork.combine([base,...irqs]),irqInstructions:irqs.reduce((a,w)=>a+w.instructions,0)};
        })''',selected);browser.close()
    base=trace['location']['main_base']+0xd510;counts={c['ordinal']:{} for c in work['calls']};returns={r['call']:r['ax'] for r in work['results']}
    for c in work['counts']:counts[c['call']][str(c['address']-base)]=c['entries']
    results=[]
    for row,model in zip(selected,generated):
        ordinal=row['call']['ordinal'];actual=counts[ordinal];expected=model['complete']['entries']
        differences={a:dict(expected=expected.get(a,0),actual=actual.get(a,0)) for a in actual.keys()|expected.keys() if actual.get(a,0)!=expected.get(a,0)}
        input_equal=[row['input']['cachedHandle'],row['input']['state'],row['input']['segment']]==row['call']['header'];return_equal=model['base']['handle']==returns[ordinal]
        results.append(dict(key=row['key'],ordinal=ordinal,action=row['action'],instructions=model['complete']['instructions'],irq_instructions=model['irqInstructions'],irq_fixture_ordinals=[i['ordinal'] for i in row['interrupts']],differences=differences,input_equal=input_equal,return_equal=return_equal,passed=not differences and input_equal and return_equal))
    report=dict(passed=all(r['passed'] for r in results),full_scheduling_parity=False,matching_calls=sum(r['passed'] for r in results),cold_calls=sum(r['action']=='load' for r in results),instructions=sum(r['instructions'] for r in results),irq_fixture_calls=[r['ordinal'] for r in results if r['irq_fixture_ordinals']],calls=results,models={f:hashlib.sha256((ROOT/'treehouse-demo'/f).read_bytes()).hexdigest() for f in MODELS},memory_report_sha256=hashlib.sha256(memory_path.read_bytes()).hexdigest(),trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),timer_trace_sha256=hashlib.sha256(timer_path.read_bytes()).hexdigest(),timer_report_sha256=hashlib.sha256(timer_report_path.read_bytes()).hexdigest(),source_sha256=SOURCE_SHA,scope='Every resident instruction for 2478 generated source-cache calls, including 29 complete cold paths. Allocation work derives from continuous generated memory; read bytes from pinned DAT; file-list/initial handle state from an offline fixture. IRQ inclusion and before-state are explicit observed fixtures, not independently scheduled. BIOS/DOS work outside resident code, other 16 calls, startup and live integration remain open. The earlier fixture-free two-interrupt failure remains valid.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({**report,'calls':[r for r in results if not r['passed']]},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['memory','scene','trace','timer','timer-report','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if verify(a.memory,a.scene,a.trace,a.timer,a.timer_report,a.output) else 1)
