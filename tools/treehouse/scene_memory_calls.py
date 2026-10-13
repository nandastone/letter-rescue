"""Identify native scene boundaries for comparing generated memory operations."""
import hashlib,struct,zipfile
from pathlib import Path
from resources import parse_archive
from build_demo import SOURCE_SHA

ROOT=Path(__file__).resolve().parents[2]

def scene_calls(trace,shapes,script_catalogs=None):
    source=ROOT/'testing/output/treehouse/source/The_Treehouse_1991.zip'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('Unresearched original archive')
    with zipfile.ZipFile(source) as z:data=z.read('TheTreeh/th.dat')
    resources={(r['tag'],r['id']):data[r['payload_offset']:r['payload_offset']+r['size']] for r in parse_archive(data)}
    phases=[];objects={};wrapper=None;current=None;surface=None;backup=None;disposal=None;preload=None
    scripts={};script=None;script_free=None;catalogs=script_catalogs or []
    shape_by_time={s['milliseconds']:s for s in shapes}
    def add(kind,begin,end,obj,**kw):phases.append(dict(type='scene',kind=kind,milliseconds=begin,end=end,object=obj,**kw))
    for e in trace['events']:
        label=e['label'];s=e['stack'];time=e['milliseconds']
        if catalogs and label=='resource.find':
            tag=(s[3]+65536*s[4]).to_bytes(4,'big').strip(b'\0').decode('ascii');id=s[2]
            if tag!='SCR':raise ValueError('Unresearched direct scene resource')
            catalog,entry=next((c,r) for c in catalogs for r in c['records'] if r['tag']==tag and r['id']==id)
            if catalog['archive']!='th':raise ValueError('Unresearched script archive')
            script=dict(begin=time,key=f'th:{id}',arguments=dict(payload=list(resources[tag,id]),catalogHandle=catalog['handle'],cachedHandle=entry['handle']))
        elif catalogs and label=='resource.find.return':
            if not script:raise ValueError('Unpaired script load')
            pointer=e['ax']+16*e['dx'];scripts[pointer]=script
            add('script-load',script['begin'],time,0,arguments=script['arguments'],expectedPointer=pointer,key=script['key']);script=None
        elif catalogs and label=='memory.raw.free' and s[2]+16*s[3] in scripts:
            pointer=s[2]+16*s[3];script_free=dict(begin=time,pointer=pointer,key=scripts.pop(pointer)['key'])
        elif catalogs and label=='memory.raw.free.return' and script_free:
            add('script-free',script_free['begin'],time,0,pointer=script_free['pointer'],key=script_free['key']);script_free=None
        elif label=='wrapper.begin':wrapper=dict(script=s[10]+s[9],palette=s[10])
        elif label=='scr.allocate':
            first_id,count=struct.unpack_from('<HH',resources[('SHPL',wrapper['palette'])])
            if s[4]!=1 or s[3]!=count:raise ValueError('Constructor shape range differs from original palette')
            current=dict(begin=time,firstId=first_id,first=1,last=count,bounds=list(struct.unpack_from('<4h',resources[('SCR',wrapper['script'])])),saveBackground=bool(s[2]))
        elif label=='scr.object.allocated':
            if not current:raise ValueError('Unpaired object allocation')
            current['object']=e['ax'];objects[e['ax']]=current
            add('object',current['begin'],time,e['ax'],arguments={k:current[k] for k in ['first','last','bounds','saveBackground']})
        elif label=='scr.preload' and current:preload=s[0]
        elif label=='scr.preload.return':preload=None
        elif label=='shape.load' and current and preload is not None:
            shape=shape_by_time[time];relative=int(shape['key'].split(':')[1])-current['firstId']+1
            if relative!=preload:raise ValueError('Preload differs from palette-relative index')
            shape.update(sceneObject=current['object'],relative=relative)
        elif label=='surface.allocate' and current:surface=dict(begin=time)
        elif label=='memory.near.allocate.return' and surface:surface['rows']=e['ax']
        elif label=='memory.raw.allocate' and current and not surface and 'surface' in current:backup=dict(begin=time)
        elif label=='memory.raw.allocate.return':
            if surface:surface['pointer']=e['ax']+16*e['dx']
            elif backup:backup['pointer']=e['ax']+16*e['dx']
        elif label=='surface.allocate.return' and surface:
            add('surface',surface['begin'],time,current['object'],expectedPointer=surface['pointer'],expectedRows=surface['rows'])
            current['surface']=surface['pointer'];surface=None
        elif label=='scr.backup.allocated':
            if not backup or not current:raise ValueError('Unpaired backup allocation')
            add('backup',backup['begin'],time,current['object'],expectedPointer=backup['pointer']);backup=None
        elif label=='scr.allocate.return':current=None
        elif label=='scr.free' and s[2] in objects:disposal=dict(begin=time,object=s[2])
        elif label=='scr.free.return' and disposal:
            add('dispose',disposal['begin'],time,disposal['object']);objects.pop(disposal['object']);disposal=None
    if any([current,surface,backup,disposal,script,script_free,scripts]) or len(phases)!=(12 if catalogs else 8) or objects:raise ValueError('Incomplete two-animation lifecycle coverage')
    return phases
