"""Original instrument sustain rate and bounded waveform regression."""
from pathlib import Path
import argparse, json
from compare_instrument_audio import compare

REFERENCE=Path(__file__).resolve().parents[2]/'testing/output/treehouse/instrument-audio-native-a'


def verify(html,output):
    complete=compare(html,REFERENCE,output)
    path=output/'report.json';report=json.loads(path.read_text(encoding='utf-8'));checks=[]
    for case in report['cases']:
        label=f"{case['instrument']} {case['label']}";h=case['native_header'];v=case['rendered']
        hardware=int(1000000//(1000000//h[1]));effective=int(hardware*16384//48000)*48000/16384
        checks.append(dict(name=label+' reference mixer rate',passed=abs(v['outputRate']-effective)<.002))
        checks.append(dict(name=label+' original sample and loop bounds',passed=v['count']==h[3] and v['loop']==bool(h[0]&128) and (not v['loop'] or abs(v['loopStart']*v['pcmRate']-h[4])<.001 and abs(v['loopEnd']*v['pcmRate']-(h[5] or h[3]))<.001)))
        for w in case['windows']:
            ok=(w['browser_rms']==0) if w['native_rms']==0 else w['correlation'] is not None and w['correlation']>.99 and abs(w['level']-1)<.05
            checks.append(dict(name=f"{label} sustain window {w['start_seconds']} s",passed=ok))
    report.update(checks=checks,passed=complete and len(report['cases'])==12 and all(c['passed'] for c in checks))
    report['scope']+=' Regression acceptance covers these twelve notes at correlation >0.99 and level within 5%, using one attack alignment for the entire held note. It does not establish full waveform, stop-decay or scheduling parity.'
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS' if report['passed'] else 'FAIL',len(checks),'checks')
    return report['passed']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output) else 1)
