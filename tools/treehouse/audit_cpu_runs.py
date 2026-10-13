"""Identify decoder exits and callback costs from complete boundary observations."""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json


def audit(trace_path,control_path,queue_path,output):
    output.mkdir(parents=True,exist_ok=False);trace=json.loads(trace_path.read_text());control=json.loads(control_path.read_text());queue=json.loads(queue_path.read_text())
    if not control['passed'] or Path(control['candidate']).resolve()!=trace_path.parent.resolve():raise ValueError('No accepted CPU probe control')
    if not queue['passed'] or queue['pic_sha256']!=trace['pic']['sha256']:raise ValueError('PIC inputs differ from accepted continuous queue proof')
    path=trace_path.parent/trace['cpu_runs']['path']
    with path.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=trace['cpu_runs']['sha256']:raise ValueError('CPU trace digest differs')
    stack=[];decoders=Counter();exits=Counter();callbacks=Counter();functions=Counter();opcode_failures=[];budget_failures=[];callback_budget=Counter();matched=0;cpu_count=0;event_count=0;max_depth=0;instructions=0;strings=0;io=0;credits=0
    with path.open() as f:
        for ordinal,line in enumerate(f):
            e=json.loads(line);event_count+=1
            if e['kind'] in [1,3]:
                stack.append((e,ordinal));max_depth=max(max_depth,len(stack));continue
            if not stack:raise ValueError('CPU/callback end without beginning')
            begin,index=stack.pop()
            if e['kind']!=begin['kind']+1 or e['id']!=begin['id']:raise ValueError('CPU/callback boundary mismatch')
            if e['instructions']<begin['instructions'] or e['strings']<begin['strings']:raise ValueError('CPU counters went backwards')
            if e['kind']==2:
                cpu_count+=1;decoders[e['id']]+=1
                n=e['instructions']-begin['instructions'];s=e['strings']-begin['strings'];debit=e['io']-begin['io']
                instructions+=n;strings+=s;io+=debit
                credit=e.get('credits',0)-begin.get('credits',0);credits+=credit
                if e['result']>0:
                    exits['callback']+=1;code=e['opcode']
                    if not (code[0]==0xfe and (code[1]>>3)&7==7 and code[2]+256*code[3]==e['result']):opcode_failures.append(dict(ordinal=ordinal,result=e['result'],opcode=code,address=e['last_address']))
                elif e['cycles']<0:exits['negative-budget']+=1
                else:exits['other-zero-result']+=1
                exhausted=int(e['result']==0 and e['cycles']<0)
                expected=begin['cycles']+begin['left']-n-s-debit-exhausted+credit;actual=e['cycles']+e['left']
                if expected==actual:matched+=1
                elif len(budget_failures)<20:budget_failures.append(dict(ordinal=ordinal,begin_ordinal=index,decoder=e['id'],result=e['result'],expected=expected,actual=actual,instructions=n,strings=s,io=debit,last_address=e['last_address'],opcode=e['opcode'],begin=begin,end=e))
            else:
                callbacks[e['id']]+=1;functions[f'{e["id"]}:{begin["ax"]:04x}']+=1
                delta=begin['cycles']+begin['left']-e['cycles']-e['left'];debit=e['io']-begin['io'];guest=e['instructions']-begin['instructions']
                callback_budget['unchanged' if delta==0 and debit==0 and guest==0 else 'io-debit-only' if delta==debit and guest==0 else 'other']+=1
    if stack:raise ValueError('CPU/callback boundary left open')
    report=dict(passed=event_count==trace['cpu_runs']['events'] and not opcode_failures,full_cpu_scheduling_parity=False,events=event_count,cpu_runs=cpu_count,decoder_counts=dict(decoders),exit_counts=dict(exits),maximum_boundary_depth=max_depth,instructions=instructions,string_iterations=strings,stack_segment_credits=credits,io_debit=io,budget_formula_matches=matched,budget_formula_mismatches=cpu_count-matched,budget_failures=budget_failures,callback_counts=[dict(id=id,description=trace['cpu_runs']['callback_descriptions'].get(str(id)),calls=count) for id,count in callbacks.most_common()],callback_budget_categories=dict(callback_budget),common_callback_functions=functions.most_common(20),opcode_failures=opcode_failures,trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),cpu_sha256=trace['cpu_runs']['sha256'],queue_report_sha256=hashlib.sha256(queue_path.read_bytes()).hexdigest(),scope='Complete CPU decoder and callback boundary inventory, with observed instruction/string/IO and optional stack-credit counters. Positive decoder exits must match the actual FE /7 callback opcode. Budget formula comparison is diagnostic and does not turn observed instruction counts into independent game execution. Callback work, IRQ admission and generated CPU paths remain open.')
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({**report,'budget_failures':len(budget_failures)},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trace','control','queue','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();audit(a.trace,a.control,a.queue,a.output)
