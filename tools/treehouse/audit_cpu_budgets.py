"""Inventory external budget transitions; classification is not execution parity."""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json


def audit(trace_path,queue_report_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());queue=json.loads(queue_report_path.read_text())
    if not queue['passed'] or queue['trace_sha256']!=hashlib.sha256(trace_path.read_bytes()).hexdigest():raise ValueError('No accepted queue replay')
    path=trace_path.parent/trace['pic']['path']
    with path.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=trace['pic']['sha256']:raise ValueError('PIC capture differs')
    previous=json.loads((trace_path.parent/trace['pic']['initial_path']).read_text())['state'];counts=Counter();examples={};next_kinds=Counter();operations=0
    with path.open() as f:
        for ordinal,line in enumerate(f):
            row=json.loads(line);state=row['before'];operations+=1
            if any(state[k]!=previous[k] for k in ['cycles','left','maximum']):
                if state['maximum']!=previous['maximum']:kind='maximum-changed'
                elif state['left']==previous['left'] and state['cycles']==-1:kind='budget-exhausted-to-minus-one'
                elif state['left']==previous['left'] and 0<=state['cycles']<previous['cycles']:kind='partial-budget-consumption'
                elif state['cycles']==0 and state['left']==previous['left']+previous['cycles']:kind='remaining-budget-returned'
                else:kind='other'
                counts[kind]+=1;next_kinds[row['kind']]+=1
                sample=examples.setdefault(kind,[])
                if len(sample)<4:sample.append(dict(ordinal=ordinal,next_kind=row['kind'],milliseconds=state['milliseconds'],before={k:previous[k] for k in ['cycles','left','maximum']},after={k:state[k] for k in ['cycles','left','maximum']}))
            previous=row['after']
    report=dict(passed=operations==trace['pic']['operations'] and sum(counts.values())==queue['externalBudgetInputs'],full_cpu_scheduling_parity=False,operations=operations,external_budget_changes=sum(counts.values()),categories=dict(counts),next_operation_kinds=dict(next_kinds),examples=examples,trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),queue_report_sha256=hashlib.sha256(queue_report_path.read_bytes()).hexdigest(),scope='Inventory of external CPU budget changes between verified PIC primitives. Numeric categories do not identify guest instructions or prove CPU execution costs. Partial-budget returns require CPU exit/callback observations before they can be generated independently.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','queue-report','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();audit(a.trace,a.queue_report,a.output)
