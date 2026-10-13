"""Locate pixel differences in missing frames; never used for acceptance."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
from PIL import Image,ImageDraw

def diagnose(journey,output,checkpoint=None):
    output.mkdir(parents=True,exist_ok=False)
    report=json.loads(journey.read_text(encoding='utf-8'));reference=Path(report['reference'])
    rows=[];examples=[]
    for interval in report['presentation_observations']:
        if checkpoint and interval['name']!=checkpoint:continue
        frames=list({f['sha256']:f for f in interval['browser_frames']}.values())
        pictures=[Image.open(journey.parent/f['image']).convert('RGB') for f in frames]
        arrays=np.array([np.asarray(p) for p in pictures])
        missing=sorted(interval['missing'],key=lambda f:f['tick'])
        local=[]
        for f in missing:
            native=Image.open(reference/f['image']).convert('RGB');a=np.asarray(native)
            counts=np.count_nonzero(np.any(arrays!=a,axis=3),axis=(1,2));i=int(counts.argmin())
            mask=np.any(arrays[i]!=a,axis=2);ys,xs=np.where(mask)
            bounds=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)] if len(xs) else None
            row=dict(checkpoint=interval['name'],native=f,nearest=frames[i],pixels=int(counts[i]),bounds=bounds)
            local.append(row)
            if len(examples)<40 and (checkpoint or len(local)<=2):
                diff=np.zeros_like(a);diff[mask]=[255,64,64]
                examples.append((row,native,pictures[i],Image.fromarray(diff)))
        rows.extend(local)
        print(interval['name'],[(r['native']['tick'],r['pixels'],r['bounds']) for r in local],flush=True)
    result=dict(demo_sha256=report['demo_sha256'],journey_sha256=hashlib.sha256(journey.read_bytes()).hexdigest(),scope=__doc__,differences=rows)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    for start in range(0,len(examples),8):
        group=examples[start:start+8];sheet=Image.new('RGB',(960,224*len(group)),(32,32,32));draw=ImageDraw.Draw(sheet)
        for i,(r,n,b,d) in enumerate(group):
            y=i*224;draw.text((5,y+4),f"{r['checkpoint']} native {r['native']['tick']} | browser {r['nearest']['tick']} | {r['pixels']} differing pixels",fill='white')
            for x,p in [(0,n),(320,b),(640,d)]:sheet.paste(p,(x,y+24))
        sheet.save(output/f'contact-{start//8}.png')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--journey',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--checkpoint');a=p.parse_args();diagnose(a.journey,a.output,a.checkpoint)
