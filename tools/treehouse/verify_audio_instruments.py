"""Compare all original instrument attack/sustain windows without gain fitting."""
from pathlib import Path
import argparse,json
from compare_instrument_audio import compare

REFERENCE=Path(__file__).resolve().parents[2]/'testing/output/treehouse/instrument-audio-native-all-b'

def verify(html,output):
    complete=compare(html,REFERENCE,output)
    path=output/'report.json';r=json.loads(path.read_text(encoding='utf-8'))
    windows=[w for c in r['cases'] for w in c['windows']]
    coverage={(c['instrument'],c['label']) for c in r['cases']}
    r['checks']=[dict(name='all 42 instruments, three notes each',passed=coverage=={(i,label) for i in range(42) for label in ['short','long','high']}),
        dict(name='all 336 original waveform windows are sample-exact',passed=len(windows)==336 and all(w['unscaled_rmse']==0 for w in windows))]
    r['passed']=complete and all(c['passed'] for c in r['checks'])
    r['scope']+=' Regression requires sample-exact equality in all 336 windows after one attack alignment per note. No per-window alignment or gain fitting. Stop/replacement/input scheduling and complete-game audio remain separate requirements.'
    path.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print('PASS' if r['passed'] else 'FAIL',len(windows),'waveform windows');return r['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(0 if verify(a.html,a.output) else 1)
