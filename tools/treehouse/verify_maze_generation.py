"""Replay original seeded maze transitions against the playable runtime."""
from pathlib import Path
import argparse,hashlib,json,struct
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'testing/output/treehouse'
def model(path):
 b=path.read_bytes();s=0x318b0;d=0x323f0;w=lambda at:struct.unpack_from('<H',b,s+at)[0]
 return dict(seed=struct.unpack_from('<I',b,d+0x5290)[0],hard=bool(w(0xa8)),streak=w(0xa10),excluded=w(0x9d6),supportedTypes=w(0x9e4),typeHistory=[w(0x9e0),w(0x9e2)],patternHistory=[[w(a),w(a+2)]for a in [0x996,0x99a,0x99e,0x9a2]],familyHistory=w(0x9a6),songs=[w(0x922+2*i)for i in range(6)],history=[i for i in range(24)if w(0x8f2+2*i)],secret=w(0x9ae),node=w(0x9d4),type=w(0x26),correct=w(0xa16),choices=[w(0xa1e+2*i)for i in range(4)])
def verify(html,output):
 output.mkdir(parents=True,exist_ok=False);report=dict(demo_sha256=hashlib.sha256(html.read_bytes()).hexdigest(),checks=[],traces=[],errors=[])
 with sync_playwright()as p:
  browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();page.add_init_script('requestAnimationFrame=()=>0');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(html.resolve().as_uri());page.evaluate("resident.ambientEnabled=false;setScene('maze');maze.cancel();window.finishMaze=()=>{let i=0;while(maze.busy&&i++<30000)advance();return !maze.busy;}")
  load='m=>{maze.cancel();Object.assign(maze,m);maze.history=new Set(m.history);maze.random=null;maze.started=true;maze.introduced=true;maze.roundReplaced=false;gameplayRandom.reset(m.seed);gameplayRandom.trace=[];}'
  snapshot='()=>({seed:gameplayRandom.seed,hard:maze.hard,excluded:maze.excluded,typeHistory:maze.typeHistory,patternHistory:maze.patternHistory,familyHistory:maze.familyHistory,type:maze.type,correct:maze.correct,choices:maze.choices,songs:maze.songs,secret:maze.secret,node:maze.node,trace:gameplayRandom.trace})'
  def compare(label,expected,keys):
   actual=page.evaluate(snapshot);passed=all(actual[k]==expected[k]for k in keys);report['checks'].append(dict(name=label,passed=passed));report['traces'].append(dict(name=label,keys=keys,expected={k:expected[k]for k in keys},actual=actual))
  keys=['seed','hard','excluded','typeHistory','patternHistory','familyHistory','type','correct','choices']
  folder=DATA/'research-music-maze/playthrough/state'
  for i in range(7):
   before=folder/(('wrong'if i==0 else'correct-'+str(i-1))+'.ram-0');after=folder/('correct-'+str(i)+'.ram-0');page.evaluate(load,model(before));page.evaluate('maze.streak++;if(maze.streak===2)maze.difficulty(true);maze.frogVoice();maze.challenge()');compare('native challenge '+str(i),model(after),keys)
  folder=DATA/'research-maze-completion/intro-capture/state';page.evaluate(load,model(folder/'intro-06.ram-0'));page.evaluate('maze.setupRound()');compare('native first easy challenge',model(folder/'intro-07.ram-0'),keys+['secret','node'])
  folder=DATA/'research-maze-generation/new-round/state';page.evaluate(load,model(folder/'before.ram-0'));page.evaluate("maze.phase='win';maze.frogPoint=[150,130];maze.run(maze.endControl(true));finishMaze()");compare('native win through new round',model(folder/'after.ram-0'),keys+['songs','secret','node'])
  report['checks'].append(dict(name='abandoned game retains six songs',passed=page.evaluate('()=>{const before=JSON.stringify(maze.songs);maze.reset();finishMaze();return before===JSON.stringify(maze.songs); }')))
  report['checks'].append(dict(name='difficulty updates shared preference',passed=page.evaluate('()=>{maze.difficulty(true);return gameSave.preferences.advanced;}')))
  report['passed']=not report['errors']and all(c['passed']for c in report['checks']);browser.close()
 (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items()if k!='traces'},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.html,a.output)
