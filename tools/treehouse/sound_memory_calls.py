"""Resolve native sound-load boundaries to original data for offline comparison."""
from pathlib import Path
import hashlib,struct,zipfile
from build_demo import SOURCE_SHA
from memory_catalog import read_catalogs
from resources import parse_archive

ROOT=Path(__file__).resolve().parents[2]


def sound_calls(trace,initial_data):
    source=ROOT/'testing/output/treehouse/source/The_Treehouse_1991.zip'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('Unresearched source archive')
    resolved={};initial_sources={};ss=trace['heap'][0]['ss']
    with zipfile.ZipFile(source) as z:
        for catalog in read_catalogs(initial_data,ss):
            data=z.read(f'TheTreeh/{catalog["archive"]}.dat');records={(r['tag'],r['id']):r for r in parse_archive(data)}
            for entry in catalog['records']:
                if entry['tag']!='SND' or entry['id'] in resolved:continue
                r=records['SND',entry['id']]
                if entry['offset']!=r['checksum_offset'] or entry['length']!=r['size']:raise ValueError('Sound catalog differs from original DAT')
                key=f'{catalog["archive"]}:SND:{entry["id"]}'
                resolved[entry['id']]=dict(key=key,payload=list(data[r['payload_offset']:r['payload_offset']+r['size']]),directoryFlags=entry['flags'],catalogHandle=catalog['handle'])
                if entry['handle']:initial_sources[key]=entry['handle']
    minimum,maximum=struct.unpack_from('<HH',initial_data,ss*16+0x212e)
    begin=trace['heap'][0]['milliseconds'];end=trace['heap'][-1]['milliseconds'];calls=[];pending=None;resize_depth=0
    for e in trace['events']:
        label=e['label'];s=e['stack'];time=e['milliseconds']
        if label=='sound.load':
            if pending:raise ValueError('Nested sound load')
            pending=dict(type='sound',milliseconds=time,**resolved[s[2]],minimumRate=minimum,maximumRate=maximum,operations=[],farAllocations=0)
        elif label=='sound.load.return':
            if not pending or resize_depth:raise ValueError('Unpaired sound load')
            pending.update(end=time,expectedHandle=e['ax'])
            if begin<=pending['milliseconds'] and time<=end:calls.append(pending)
            pending=None
        elif pending:
            if label=='memory.handle.allocate':pending['operations'].append(dict(kind='handle.allocate',bytes=s[2]+65536*s[3]))
            elif label=='memory.reallocate':pending['operations'].append(dict(kind='handle.reallocate',bytes=s[2]+65536*s[3]))
            elif label=='resource.read':pending['operations'].append(dict(kind='resource.read',bytes=e['dx']+65536*e['cx']))
            elif label=='memory.resize':
                if not resize_depth:pending['operations'].append(dict(kind='handle.resize',bytes=e['ax']+65536*e['dx']))
                resize_depth+=1
            elif label=='memory.resize.return':resize_depth-=1
            elif label=='memory.far.allocate':pending['farAllocations']+=1
    if pending or resize_depth or not calls:raise ValueError('Incomplete sound memory coverage')
    return calls,initial_sources
