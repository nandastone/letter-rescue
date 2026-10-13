"""Compare DAT-driven catalog binary searches with every native lookup call."""
from pathlib import Path
import argparse,hashlib,json,struct,sys,zipfile
from playwright.sync_api import sync_playwright
from memory_catalog import read_catalogs
from build_demo import SOURCE_SHA

ROOT=Path(__file__).resolve().parents[2]


def verify(trace_path,catalog_path,output,with_address=False):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());work=trace['work']
    if not work or work['routine']!=('resident:7BC9+6628' if with_address else 'resident:7BC9') or len(work['calls'])!=2496:raise ValueError('Incomplete lookup work coverage')
    source=ROOT/'testing/output/treehouse/source/The_Treehouse_1991.zip'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('Unresearched archive')
    catalogs=read_catalogs(catalog_path.read_bytes(),13253)
    with zipfile.ZipFile(source) as z:
        for catalog in catalogs:
            data=z.read(f'TheTreeh/{catalog["archive"]}.dat');directory=struct.unpack_from('<I',data)[0];types=[]
            for i in range(struct.unpack_from('<H',data,directory)[0]):
                tag,relative=struct.unpack_from('<IH',data,directory+2+i*6);table=directory+relative
                ids=[struct.unpack_from('<H',data,table+2+11*j)[0] for j in range(struct.unpack_from('<H',data,table)[0])]
                types.append(dict(tag=tag.to_bytes(4,'big').strip(b'\0').decode('ascii'),relative=relative,ids=ids))
            if types!=catalog['types']:raise ValueError('RAM lookup table differs from pinned DAT')
            del catalog['records']
    lookups=[];pending=None
    for e in trace['events']:
        if e['label']=='resource.lookup':
            if pending:raise ValueError('Nested lookup')
            pending=dict(tag=(e['ax']+65536*e['dx']).to_bytes(4,'big').strip(b'\0').decode('ascii'),id=e['cx'],time=e['milliseconds'])
        elif e['label']=='resource.entry':
            if not pending:raise ValueError('Resource entry without lookup')
            lookups.append(dict(**pending,entry=e));pending=None
    if pending or len(lookups)!=2496:raise ValueError('Incomplete lookup boundaries')
    base=trace['location']['main_base']+0xd510;counts={c['ordinal']:{} for c in work['calls']}
    for c in work['counts']:counts[c['call']][str(c['address']-base)]=c['entries']
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_script_tag(path=str(ROOT/'treehouse-demo/resource-work.js'))
        models=page.evaluate('''a=>a.lookups.map(q=>{
          const model=OriginalResourceWork.lookup({...q,catalogs:a.catalogs});
          if(a.withAddress)for(const id of model.handleCalls){
            const call=OriginalResourceWork.handleAddress(a.catalogs.find(c=>c.handle===id));
            if(!call.address)throw new Error('Catalog is not resident');
            for(const [address,count] of Object.entries(call.entries))model.entries[address]=(model.entries[address]||0)+count;
            model.instructions+=call.instructions;model.cycles+=call.cycles;
          }
          return model;
        })''',dict(catalogs=catalogs,lookups=[dict(tag=q['tag'],id=q['id']) for q in lookups],withAddress=with_address))
        checks=page.evaluate('''()=>{
          const types=[{tag:'ABCA',relative:2,ids:[65535,1,300]},{tag:'ABCB',relative:40,ids:[]},{tag:'ZZZZ',relative:50,ids:[4]}];
          const catalogs=[{handle:10,types:[]},{handle:20,types},{handle:30,types}];
          const f=(tag,id)=>OriginalResourceWork.lookup({catalogs,tag,id});
          const first=f('ABCA',1),negative=f('ABCA',65535),large=f('ZZZZ',4),empty=f('ABCB',0),missing=f('ABCA',3),unknown=f('MISS',0),font=f('FONT',0),cursor=f('CURS',0);
          return [
            {name:'lookup preserves catalog priority and skips empty catalogs',passed:first.result.catalogHandle===20&&first.result.index===1},
            {name:'IDs use the original signed word comparison',passed:negative.result.index===0&&negative.entries[0x7c65]>0},
            {name:'type search reaches both word-comparison paths',passed:large.result.tag==='ZZZZ'&&large.entries[0x7c72]>0&&first.entries[0x7c6d]>0},
            {name:'empty resource table continues to the next catalog',passed:empty.result===null&&empty.entries[0x7c22]===2},
            {name:'missing ID exhausts both catalogs',passed:missing.result===null&&missing.entries[0x7c36]>2},
            {name:'unknown tag returns no resource',passed:unknown.result===null},
            {name:'built-in font and cursor use original fallback entries',passed:font.result.builtin&&font.result.entryOffset===14&&cursor.result.entryOffset===29}
          ];
        }''')
        if with_address:
            checks.extend(page.evaluate('''()=>{
              const f=OriginalResourceWork.handleAddress;
              const active=f({handle:100,state:0x11f3,segment:200}),empty=f({handle:0}),discarded=f({handle:100,state:0x1000,segment:0}),ems=f({handle:100,state:0x200,segment:200});
              return [
                {name:'resident address includes the six-byte block header',passed:active.address===3209&&active.ax===9&&active.dx===200},
                {name:'null handle returns zero',passed:empty.address===0&&!empty.entries[0x6632]},
                {name:'discarded handle returns zero',passed:discarded.address===0&&!discarded.entries[0x6643]},
                {name:'non-materializing address query returns zero for EMS',passed:ems.address===0&&ems.entries[0x664c]===1}
              ];
            }'''))
        browser.close()
    results=[]
    for query,call,model in zip(lookups,work['calls'],models):
        if query['time']!=call['begin'] or call['end']>query['entry']['milliseconds']:raise ValueError('Lookup boundary differs')
        actual=counts[call['ordinal']];differences={a:dict(expected=model['entries'].get(a,0),actual=actual.get(a,0)) for a in actual.keys()|model['entries'].keys() if actual.get(a,0)!=model['entries'].get(a,0)}
        result=model['result'];observed_offset=query['entry']['di']-(0 if result and result.get('builtin') else query['entry']['si'])
        offset_equal=result is not None and result['entryOffset']==observed_offset
        results.append(dict(tag=query['tag'],id=query['id'],ordinal=call['ordinal'],**model,differences=differences,entry_offset_equal=offset_equal,passed=not differences and offset_equal))
    report=dict(passed=all(r['passed'] for r in results+checks),calls=results,checks=checks,
        exact_calls=sum(r['passed'] for r in results),total_calls=len(results),
        model_sha256=hashlib.sha256((ROOT/'treehouse-demo/resource-work.js').read_bytes()).hexdigest(),source_sha256=SOURCE_SHA,
        trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),catalog_fixture_sha256=hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
        includes_handle_address_work=with_address,
        scope='7BC9 lookup work and returned directory offsets across all captured calls, using pinned DAT tables and explicit offline initial catalog priority. Optional 6628 work is generated for each visited resident catalog. Full scheduling remains separate. Synthetic checks cover missing/empty tables, signed IDs and built-in fallback.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({**report,'calls':[r for r in results if not r['passed']][:10]},indent=2));return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trace',type=Path,required=True);p.add_argument('--catalog',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--with-address',action='store_true');a=p.parse_args();sys.exit(0 if verify(a.trace,a.catalog,a.output,a.with_address) else 1)
