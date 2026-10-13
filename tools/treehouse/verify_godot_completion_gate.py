"""Exercise completion-gate rejection paths with explicitly synthetic fixtures."""
import argparse
import copy
import json
from pathlib import Path

from godot_completion import ROOT, SUITES, JOURNEYS, evaluate, fingerprint, reference, sources, web_files


def write(path, value):
    path.write_text(json.dumps(value,indent=2),encoding='utf-8')


def fixture(root):
    project=root/'treehouse-godot';(project/'scripts').mkdir(parents=True);(project/'data').mkdir()
    for name in ('project.godot','main.tscn','export_presets.cfg','scripts/game.gd','data/original.json'):
        (project/name).write_text('Synthetic gate fixture',encoding='utf-8')
    web=root/'web';web.mkdir()
    for name in ('index.html','index.js','index.pck','index.wasm'):
        (web/name).write_text('Synthetic '+name,encoding='utf-8')
    (root/'verifier.py').write_text('# Synthetic verifier',encoding='utf-8')
    (root/'desktop.exe').write_text('Synthetic desktop artifact',encoding='utf-8')
    files=web_files(web);inputs=sources(root)
    build=dict(passed=True,runtime='Godot',web_directory='web',web_files=files,
               build_sha256=fingerprint(files),source_files=inputs,source_sha256=fingerprint(inputs))
    write(root/'build.json',build)
    ledger=copy.deepcopy(json.loads((ROOT/'testing/treehouse/remaining-work.json').read_text(encoding='utf-8')))
    claims=[f"{i['id']}:{n}" for i in ledger['issues'] for n in range(1,len(i['acceptance'])+1)]
    for issue in ledger['issues']:issue['status']='closed'
    result=dict(passed=True,checks=[dict(name='synthetic',passed=True)],web_files=files,
                strict_timing_parity=True,unrepresented_native_displays=0,shifted_frames=0,excluded_frames=0,
                waveform_parity=True,event_timing_parity=True,complete_journey=True,ordinary_inputs=True,
                desktop_files={'desktop.exe':reference(root/'desktop.exe',root)['sha256']})
    write(root/'result.json',result)
    refs={}
    for scope in ('web','native_journey','strict_timing','native_audio','desktop'):
        envelope=dict(passed=True,scope=scope,claims=claims,result=reference(root/'result.json',root),
                      build_sha256=build['build_sha256'],source_sha256=build['source_sha256'],
                      verifier_files={'verifier.py':reference(root/'verifier.py',root)['sha256']},
                      execution=dict(exit_code=0,command=['synthetic-verifier']))
        write(root/f'{scope}.json',envelope);refs[scope]=reference(root/f'{scope}.json',root)
    delivery=dict(passed=True,build_sha256=build['build_sha256'],checks=[dict(name=n,served_sha256=h,passed=True) for n,h in files.items()])
    write(root/'delivery.json',delivery)
    index=dict(schema=2,runtime='Godot',build=reference(root/'build.json',root),requirements={},
               suites={n:refs['web'] for n in SUITES},native_journeys={n:refs['native_journey'] for n in JOURNEYS},
               strict_timing=refs['strict_timing'],native_audio=refs['native_audio'],desktop=refs['desktop'],full_clone_parity=True,
               delivery=reference(root/'delivery.json',root),known_failures=[])
    for issue in ledger['issues']:
        for n,text in enumerate(issue['acceptance'],1):
            index['requirements'][f"{issue['id']}:{n}"]=dict(text=text,reviewed=True,
                evidence=[reference(root/'result.json',root) if issue['id']=='TH-001' else refs['web']])
    return ledger,index


def verify(output):
    output.mkdir(parents=True,exist_ok=False)
    checks=[]
    def case(name, mutate=lambda root,ledger,index:None, expected=False):
        root=output/f'case-{len(checks):02}';root.mkdir()
        ledger,index=fixture(root)
        mutate(root,ledger,index)
        write(root/'ledger.json',ledger);write(root/'index.json',index)
        result=evaluate(root/'ledger.json',root/'index.json',root)
        write(root/'gate.json',result)
        checks.append(dict(name=name,passed=result['passed']==expected,expected_gate_passed=expected,actual_gate_passed=result['passed']))
    def update_proof(root,index,name,change):
        path=root/f'{name}.json';value=json.loads(path.read_text(encoding='utf-8'));change(value);write(path,value)
        old={'path':f'{name}.json'};new=reference(path,root)
        def replace(obj):
            if isinstance(obj,dict):
                if obj.get('path')==old['path']:obj.update(new)
                else:
                    for child in obj.values():replace(child)
            elif isinstance(obj,list):
                for child in obj:replace(child)
        replace(index)
    case('complete synthetic evidence can pass',expected=True)
    case('top-level passed flag alone cannot pass',lambda r,l,i:(i.clear(),i.update(passed=True)))
    case('legacy runtime cannot pass',lambda r,l,i:i.update(runtime='JavaScript'))
    case('changed PCK rejected',lambda r,l,i:(r/'web/index.pck').write_text('changed',encoding='utf-8'))
    case('unlisted export file rejected',lambda r,l,i:(r/'web/extra.js').write_text('extra',encoding='utf-8'))
    case('unlisted nested export file rejected',lambda r,l,i:((r/'web/nested').mkdir(),(r/'web/nested/extra.js').write_text('extra',encoding='utf-8')))
    case('changed runtime source rejected',lambda r,l,i:(r/'treehouse-godot/scripts/game.gd').write_text('changed',encoding='utf-8'))
    case('new runtime source rejected',lambda r,l,i:(r/'treehouse-godot/scripts/extra.gd').write_text('extra',encoding='utf-8'))
    case('missing requirement rejected',lambda r,l,i:i['requirements'].pop('TH-010:1'))
    case('changed requirement text rejected',lambda r,l,i:i['requirements']['TH-010:1'].update(text='narrower goal'))
    case('unreviewed coverage rejected',lambda r,l,i:i['requirements']['TH-010:1'].update(reviewed=False))
    case('missing requirement proof rejected',lambda r,l,i:i['requirements']['TH-010:1'].update(evidence=[]))
    case('open issue rejected',lambda r,l,i:l['issues'][1].update(status='open'))
    case('missing regression suite rejected',lambda r,l,i:i['suites'].pop('board'))
    case('missing native journey rejected',lambda r,l,i:i['native_journeys'].pop('money_loss'))
    case('missing desktop coverage rejected',lambda r,l,i:i.pop('desktop'))
    case('changed desktop artifact rejected',lambda r,l,i:(r/'desktop.exe').write_text('changed',encoding='utf-8'))
    case('known failure rejected',lambda r,l,i:i.update(known_failures=[dict(reason='unresolved')]))
    case('missing full audit rejected',lambda r,l,i:i.update(full_clone_parity=False))
    case('stale build binding rejected',lambda r,l,i:update_proof(r,i,'web',lambda v:v.update(build_sha256='old')))
    case('stale source binding rejected',lambda r,l,i:update_proof(r,i,'web',lambda v:v.update(source_sha256='old')))
    case('component tests cannot replace Web integration',lambda r,l,i:update_proof(r,i,'web',lambda v:v.update(scope='component')))
    case('missing declared claim rejected',lambda r,l,i:update_proof(r,i,'web',lambda v:v.update(claims=[])))
    case('failed execution rejected',lambda r,l,i:update_proof(r,i,'web',lambda v:v['execution'].update(exit_code=1)))
    case('changed verifier rejected',lambda r,l,i:(r/'verifier.py').write_text('# changed',encoding='utf-8'))
    case('tampered result rejected',lambda r,l,i:(r/'result.json').write_text('{}',encoding='utf-8'))
    case('delivery subset rejected',lambda r,l,i:update_proof(r,i,'delivery',lambda v:v.update(checks=v['checks'][:1])))
    case('delivery wrong file rejected',lambda r,l,i:update_proof(r,i,'delivery',lambda v:v['checks'][0].update(served_sha256='wrong')))
    def result_case(name,change):
        def mutate(root,ledger,index):
            path=root/'result.json';value=json.loads(path.read_text(encoding='utf-8'));change(value);write(path,value)
            for scope in ('web','native_journey','strict_timing','native_audio','desktop'):
                update_proof(root,index,scope,lambda v:v.update(result=reference(path,root)))
            for row in index['requirements'].values():
                for proof in row['evidence']:
                    if proof.get('path')=='result.json':proof.update(reference(path,root))
        case(name,mutate)
    result_case('nested failed check rejected despite passed flag',lambda v:v['checks'][0].update(passed=False))
    result_case('error list rejected',lambda v:v.update(errors=['failure']))
    result_case('wrong exercised export rejected',lambda v:v.update(web_files={'index.html':'wrong'}))
    result_case('incomplete native journey rejected',lambda v:v.update(complete_journey=False))
    result_case('injected native journey rejected',lambda v:v.update(ordinary_inputs=False))
    result_case('missing native displays rejected',lambda v:v.update(unrepresented_native_displays=1))
    result_case('shifted frames rejected',lambda v:v.update(shifted_frames=1))
    result_case('excluded frames rejected',lambda v:v.update(excluded_frames=1))
    result_case('unverified waveform rejected',lambda v:v.update(waveform_parity=False))
    result_case('unverified sound timing rejected',lambda v:v.update(event_timing_parity=False))
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,
                scope='Synthetic gate mechanics only. These fixtures are not game fidelity evidence.')
    write(output/'report.json',report)
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),failures=[c for c in checks if not c['passed']])))
    return report['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();raise SystemExit(0 if verify(args.output.resolve()) else 1)
