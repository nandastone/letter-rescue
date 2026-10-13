"""Inventory work between completed polls without treating samples as execution."""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json,sys


def audit(trace_path,control_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());control=json.loads(control_path.read_text());meta=trace['polling']
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted same-DLL control')
    for key,digest in [('path','sha256'),('gap_path','gap_sha256')]:
        with (trace_path.parent/meta[key]).open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=meta[digest]:raise ValueError('Gap observations differ')
    gaps={};histogram_rows=0
    with (trace_path.parent/meta['gap_path']).open() as f:
        for line in f:
            ordinal,address,entries=json.loads(line);counts=gaps.setdefault(ordinal,{})
            if address in counts or entries<=0:raise ValueError('Invalid gap histogram entry')
            counts[address]=entries;histogram_rows+=1
    previous=None;calls=0;callers=Counter();variants=Counter();first={};large=[];failures=[];complete_prefixes=0
    with (trace_path.parent/meta['path']).open() as f:
        for line in f:
            row=json.loads(line);calls+=1;c=row['cpu_before'];gap=row['gap_count'];key=(gap,row['gap_hash'])
            if row['ordinal']!=calls-1:raise ValueError('Polling ordinals differ')
            expected=c['context'][0]-(previous['cpu_after']['context'][0]+1 if previous else 0)
            if expected!=gap:failures.append(dict(ordinal=row['ordinal'],error='CPU instruction delta',expected=expected,actual=gap))
            if len(row['gap_addresses'])!=min(gap,256):raise ValueError('Gap prefix length differs')
            if gap<=256:
                complete_prefixes+=1;h=2166136261
                for address in row['gap_addresses']:
                    for shift in range(0,32,8):h=((h^((address>>shift)&255))*16777619)&0xffffffff
                if h!=row['gap_hash']:failures.append(dict(ordinal=row['ordinal'],error='Gap prefix hash'))
            if gap>meta['gap_threshold']:
                histogram=gaps.get(row['ordinal'],{})
                if sum(histogram.values())!=gap:failures.append(dict(ordinal=row['ordinal'],error='Gap histogram sum'))
                large.append(dict(ordinal=row['ordinal'],instructions=gap,addresses=len(histogram),start=previous['end'] if previous else None,end=row['begin'],hotspots=Counter(histogram).most_common(30)))
            callers[tuple(c['stack'][:2])]+=1;variants[key]+=1
            first.setdefault(key,dict(ordinal=row['ordinal'],caller=c['stack'][:2],prefix=row['gap_addresses']))
            previous=row
    large.sort(key=lambda r:r['instructions'],reverse=True)
    if large:
        largest=large[0]
        largest['enclosing_events']=[dict(label=e['label'],milliseconds=e['milliseconds'],stack=e['stack']) for e in trace['events'] if largest['start']<=e['milliseconds']<=largest['end'] and e['label'] in ['wrapper.begin','wrapper.prepared','question.begin','question.scr','question.scr.done','answer.wait']]
    report=dict(passed=not failures and calls==meta['calls'] and histogram_rows==meta['gap_rows'],full_cpu_scheduling_parity=False,calls=calls,complete_instruction_prefixes=complete_prefixes,histogram_rows=histogram_rows,callers=[dict(return_address=list(k),calls=v) for k,v in callers.most_common()],variants=[dict(instructions=key[0],path_hash=key[1],calls=count,**first[key]) for key,count in variants.most_common()],large_gaps=large,failures=failures,trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),scope='Read-only inventory and internal consistency: every gap count agrees with independent CPU counters; complete prefixes agree with ordered hashes; every completed gap above threshold has a matching full histogram. Prefixes above 256 instructions are explicitly truncated. No histogram, frequency or recorded address list is browser execution input.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ['variants','large_gaps']},indent=2));print('Largest gaps:',[(r['ordinal'],r['instructions']) for r in large[:4]]);return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','control','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(0 if audit(a.trace,a.control,a.output) else 1)
