"""Compare the original catalog file-list walk with generated instruction work."""
from pathlib import Path
import argparse,hashlib,json,sys
from playwright.sync_api import sync_playwright
from memory_catalog import read_catalogs,read_files

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,catalog_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());work=trace['work']
    if not work or work['routine']!='resident:794C' or len(work['calls'])!=33:raise ValueError('Incomplete file-open work coverage')
    data=catalog_path.read_bytes();catalogs=read_catalogs(data,13253);files=read_files(data,13253);records={}
    for catalog in catalogs:
        for record in catalog['records']:records.setdefault((record['tag'],record['id']),catalog['handle'])
    reads=[];key=None
    for e in trace['events']:
        if e['label']=='resource.lookup':key=((e['ax']+65536*e['dx']).to_bytes(4,'big').strip(b'\0').decode('ascii'),e['cx'])
        elif e['label']=='resource.read':reads.append(dict(selected=records[key],time=e['milliseconds'],resource=list(key)))
    if len(reads)!=33:raise ValueError('Incomplete read observations')
    base=trace['location']['main_base']+0xd510;results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_script_tag(path=str(ROOT/'treehouse-demo/resource-work.js'))
        for i,(read,call) in enumerate(zip(reads,work['calls'])):
            if not read['time']<call['begin']< (reads[i+1]['time'] if i+1<len(reads) else float('inf')):raise ValueError('File-open call outside resource-read boundary')
            model=page.evaluate('a=>OriginalResourceWork.open(a)',dict(catalogs=files,selected=read['selected']))
            files=model.pop('catalogs')
            actual={str(r['address']-base):r['entries'] for r in work['counts'] if r['call']==call['ordinal']}
            differences={a:dict(expected=model['entries'].get(a,0),actual=actual.get(a,0)) for a in actual.keys()|model['entries'].keys() if actual.get(a,0)!=model['entries'].get(a,0)}
            results.append(dict(resource=read['resource'],ordinal=call['ordinal'],**model,differences=differences,passed=not differences))
        checks=page.evaluate('''()=>{
          const files=[{handle:10,fileHandle:0,filename:'C:A.DAT',volume:'DISK A'},
            {handle:20,fileHandle:6,filename:'C:B.DAT',volume:'DISK B'},
            {handle:30,fileHandle:7,filename:'D:C.DAT',volume:'DISK B'},
            {handle:40,fileHandle:8,filename:'C:D.DAT',volume:'DISK A'}];
          const cold=OriginalResourceWork.open({catalogs:files,selected:10,openResult:5});
          const hot=OriginalResourceWork.open({catalogs:cold.catalogs,selected:10});
          const builtin=OriginalResourceWork.open({catalogs:[],selected:0x2055});
          const empty=OriginalResourceWork.open({catalogs:[{...files[0],fileHandle:5,volume:''},files[1]],selected:10});
          return [
            {name:'cold open assigns the DOS file handle',passed:cold.opens.length===1&&cold.catalogs[0].fileHandle===5},
            {name:'different volume on same drive closes its file',passed:JSON.stringify(cold.closes)==='[6]'&&cold.catalogs[1].fileHandle===0},
            {name:'same volume and other drive remain open',passed:cold.catalogs[2].fileHandle===7&&cold.catalogs[3].fileHandle===8},
            {name:'warm lookup performs no DOS open or close',passed:!hot.opens.length&&!hot.closes.length},
            {name:'built-in catalog bypasses file list',passed:builtin.instructions===12&&!builtin.entries[0x7961]},
            {name:'empty volume closes another file on same drive',passed:JSON.stringify(empty.closes)==='[6]'&&empty.stringIterations===0}
          ];
        }''');browser.close()
    report=dict(passed=all(r['passed'] for r in results+checks),calls=results,checks=checks,
        model_sha256=hashlib.sha256((ROOT/'treehouse-demo/resource-work.js').read_bytes()).hexdigest(),
        trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),catalog_fixture_sha256=hashlib.sha256(data).hexdigest(),
        scope='Intrinsic 794C file-list walk. All 33 captured calls use already-open files. Cold-open, other-volume closing and built-in catalog paths have focused synthetic checks only. DOS handlers, handle-address callees and elapsed-time scheduling remain separate.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({**report,'calls':[r for r in results if not r['passed']],'exact_calls':sum(r['passed'] for r in results),'total_calls':len(results)},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trace',type=Path,required=True);p.add_argument('--catalog',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sys.exit(0 if verify(a.trace,a.catalog,a.output) else 1)
