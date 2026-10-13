"""Compare source-derived sound decoder work and PCM with pinned references."""
from pathlib import Path
import argparse,bisect,hashlib,json,sys,zipfile
from playwright.sync_api import sync_playwright
from build_demo import SOURCE_SHA
from resources import parse_archive
from sound import decode_sound_with_info

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());work=trace['work']
    if work['routine']!='resident:E964' or len(work['calls'])!=2:raise ValueError('Incomplete decoder execution coverage')
    source=ROOT/'testing/output/treehouse/source/The_Treehouse_1991.zip'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('Unresearched source')
    assets=[];native_assets={}
    with zipfile.ZipFile(source) as z:
        for name in ['digisnd','voices']:
            data=z.read(f'TheTreeh/{name}.dat')
            for r in parse_archive(data):
                if r['tag']!='SND':continue
                payload=data[r['payload_offset']:r['payload_offset']+r['size']];info,pcm=decode_sound_with_info(payload)
                if info.codec!=255:continue
                asset=dict(key=f'{name}:{r["id"]}',compressed=list(payload[10:]),expected_sha256=hashlib.sha256(pcm).hexdigest(),consumed_bytes=info.consumed_bytes-10,decode_cycles=info.decode_cycles)
                assets.append(asset)
                if name=='digisnd':native_assets[r['id']]=asset
    starts=[e for e in trace['events'] if e['label']=='sound.load'];times=[e['milliseconds'] for e in starts]
    selected=[native_assets[starts[bisect.bisect_right(times,c['begin'])-1]['stack'][2]] for c in work['calls']]
    if [s['key'] for s in selected]!=['digisnd:1011','digisnd:1006']:raise ValueError('Unexpected native decoder route')
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_script_tag(path=str(ROOT/'treehouse-demo/sound-work.js'))
        decoded=page.evaluate('a=>a.map(s=>{const r=OriginalSoundWork.decode(s.compressed);return {pcm:r.pcm,consumedBytes:r.consumedBytes,cycles:r.cycles};})',assets)
        models=page.evaluate('a=>a.map(s=>OriginalSoundWork.decode(s.compressed))',selected)
        focused=page.evaluate('''()=>{
          const one=OriginalSoundWork.decode([1,0,127]),flip=OriginalSoundWork.decode([2,0,127,0xe0]);
          let truncated=false,empty=false;try{OriginalSoundWork.decode([2,0,128]);}catch(e){truncated=true;}try{OriginalSoundWork.decode([0,0,128]);}catch(e){empty=true;}
          return [{name:'single sample needs no bit reads',passed:one.pcm.join(',')==='127'&&one.consumedBytes===3},{name:'width selector seven emits wrapped delta 128',passed:flip.pcm.join(',')==='127,255'},{name:'truncated and empty streams fail explicitly',passed:truncated&&empty}];
        }''');browser.close()
    inventory=[dict(key=a['key'],passed=hashlib.sha256(bytes(d['pcm'])).hexdigest()==a['expected_sha256'] and d['consumedBytes']==a['consumed_bytes'] and d['cycles']==a['decode_cycles']) for a,d in zip(assets,decoded)]
    base=trace['location']['main_base']+0xd510;counts={c['ordinal']:{} for c in work['calls']}
    for c in work['counts']:counts[c['call']][str(c['address']-base)]=c['entries']
    results=[]
    for call,asset,model in zip(work['calls'],selected,models):
        actual=counts[call['ordinal']];expected=model['entries']
        differences={a:dict(expected=expected.get(a,0),actual=actual.get(a,0)) for a in actual.keys()|expected.keys() if actual.get(a,0)!=expected.get(a,0)}
        results.append(dict(key=asset['key'],ordinal=call['ordinal'],instructions=model['instructions'],string_iterations=model['stringIterations'],differences=differences,passed=not differences))
    report=dict(passed=all(c['passed'] for c in inventory+results+focused),inventory=inventory,native_checks=results,focused_checks=focused,source_sha256=SOURCE_SHA,trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),model_sha256=hashlib.sha256((ROOT/'treehouse-demo/sound-work.js').read_bytes()).hexdigest(),python_decoder_sha256=hashlib.sha256((ROOT/'tools/treehouse/sound.py').read_bytes()).hexdigest(),tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='PCM, consumed bytes and intrinsic decoder cycles compared between independent Python and JavaScript implementations for all compressed digital assets; two original E964 instruction paths compared with native observations. Native PCM mixer output, preparation wrappers, interrupts and full runtime timing remain separate work.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({**report,'inventory':[c for c in inventory if not c['passed']],'matching_assets':sum(c['passed'] for c in inventory)},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.trace,a.output) else 1)
