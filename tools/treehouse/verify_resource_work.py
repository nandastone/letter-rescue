"""Compare DAT-derived resource-read work with native instruction observations."""
from pathlib import Path
import argparse,hashlib,json,sys,zipfile
from playwright.sync_api import sync_playwright
from resources import parse_archive
from memory_catalog import read_catalogs
from build_demo import SOURCE_SHA

ROOT=Path(__file__).resolve().parents[2]

def verify(trace_path,catalog_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());work=trace['work']
    if not work or work['routine']!='resident:7AEF' or len(work['calls'])!=33:raise ValueError('Incomplete read-work coverage')
    source=ROOT/'testing/output/treehouse/source/The_Treehouse_1991.zip'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('Unresearched original archive')
    catalogs=read_catalogs(catalog_path.read_bytes(),13253);records={}
    with zipfile.ZipFile(source) as z:
        for catalog in catalogs:
            data=z.read(f'TheTreeh/{catalog["archive"]}.dat')
            for r in parse_archive(data):
                key=(r['tag'],r['id'])
                if key not in records:records[key]=dict(key=f'{catalog["archive"]}:{r["tag"]}:{r["id"]}',payload=list(data[r['payload_offset']:r['payload_offset']+r['size']]),checksum=r['checksum'],directoryFlags=int(r['flags_hex'][:2],16))
    reads=[];key=None
    for e in trace['events']:
        if e['label']=='resource.lookup':key=((e['ax']+65536*e['dx']).to_bytes(4,'big').strip(b'\0').decode('ascii'),e['cx'])
        elif e['label']=='resource.read':
            r=records[key]
            if len(r['payload'])!=e['dx']+65536*e['cx']:raise ValueError('Native read length differs from DAT')
            reads.append(dict(record=r,time=e['milliseconds']))
    if len(reads)!=33:raise ValueError('Incomplete read-entry observations')
    base=trace['location']['main_base']+0xd510;results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_script_tag(path=str(ROOT/'treehouse-demo/resource-work.js'))
        for read,call in zip(reads,work['calls']):
            if read['time']!=call['begin']:raise ValueError('Read call boundary differs')
            model=page.evaluate('a=>OriginalResourceWork.read(a)',read['record'])
            actual={str(r['address']-base):r['entries'] for r in work['counts'] if r['call']==call['ordinal']}
            differences={a:dict(expected=model['entries'].get(a,0),actual=actual.get(a,0)) for a in actual.keys()|model['entries'].keys() if actual.get(a,0)!=model['entries'].get(a,0)}
            results.append(dict(key=read['record']['key'],ordinal=call['ordinal'],**model,differences=differences,passed=not differences))
        checks=page.evaluate('''()=>{
          const read=n=>OriginalResourceWork.read({payload:new Uint8Array(n),checksum:255});
          const empty=OriginalResourceWork.read({payload:[],checksum:0}),large=read(65536),ram=OriginalResourceWork.read({payload:[1,2],checksum:0,directoryFlags:0x10});
          let rejected=false;try{OriginalResourceWork.read({payload:[1],checksum:255});}catch(e){rejected=true;}
          return [
            {name:'zero-byte payload skips checksum loop after zero-byte read',passed:JSON.stringify(empty.reads)==='[1,0]'&&empty.stringIterations===0&&!empty.entries[0x7ba7]},
            {name:'large payload is split into FFF0-byte DOS reads',passed:JSON.stringify(large.reads)==='[1,65520,16]'&&large.stringIterations===65536&&large.entries[0x7b80]===65536},
            {name:'memory-backed resource delegates copy without file I/O',passed:ram.reads.length===0&&ram.memoryCopyBytes===2&&ram.entries[0x7b1b]===1&&!ram.entries[0x7b23]},
            {name:'bad source checksum is rejected',passed:rejected}
          ];
        }''');browser.close()
    report=dict(calls=results,checks=checks,passed=all(c['passed'] for c in results+checks),model_sha256=hashlib.sha256((ROOT/'treehouse-demo/resource-work.js').read_bytes()).hexdigest(),source_sha256=SOURCE_SHA,trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),catalog_fixture_sha256=hashlib.sha256(catalog_path.read_bytes()).hexdigest(),scope='Intrinsic 7AEF instruction paths and checksum iterations from original resource bytes. Initial catalog order is an explicit offline fixture. DOS handlers, file opening, external memory copy and elapsed-time scheduling are separate work.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({**report,'calls':[r for r in results if not r['passed']],'exact_calls':sum(r['passed'] for r in results),'total_calls':len(results)},indent=2));return report['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trace',type=Path,required=True);p.add_argument('--catalog',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.trace,a.catalog,a.output) else 1)
