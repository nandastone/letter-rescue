"""Append bounded menu controls to the established WR1 startup recording."""
import argparse
import json
from pathlib import Path
import struct
from bsv_replay import frame_start, read_replay

BUTTONS = {'escape': 2, 'enter': 3, 'up': 4, 'down': 5, 'left': 6, 'right': 7, 'space':9, 'ctrl':0, 'alt':8}
LETTERS = {'q':4,'a':5,'z':6,'x':7,'g':2,'h':3,'d':9,'f':1,'c':0,'s':8,'w':10,'e':11,'r':12,'t':13,'v':14,'b':15}
ANALOG = {'j':(0,-32767),'l':(0,32767),'i':(1,-32767),'k':(1,32767)}
# Raw callback records are retained for acquisition experiments. The null-host-
# driver configuration may not deliver them; verify the reached native screens.
KEYBOARD = {'n':110,'y':121}

def build(source, actions, count, prefix=350):
    header, frames = read_replay(source)
    if len(frames) < prefix or count <= prefix:
        raise ValueError('Startup prefix must fit inside source and output')
    for action in actions:
        if action['key'] not in BUTTONS | LETTERS | ANALOG | KEYBOARD or not prefix <= action['frame'] < count - 4:
            raise ValueError('Unsupported control or frame outside the post-startup range')
    result = bytearray(source[:frame_start(source, header)])
    for index in range(count):
        original = frames[min(index, len(frames)-1)]
        keys = original['key_events'] if index < prefix else []
        inputs = [dict(e) for e in original['input_events']]
        if index >= prefix:
            active = [a for a in actions if a['frame'] <= index < a['frame'] + a.get('duration',4)]
            held = {BUTTONS[a['key']] for a in active if a['key'] in BUTTONS}
            for entry in inputs:
                entry['value'] = int(entry['id'] in held) if entry['port'] == 0 and entry['device'] == 1 else 0
            inputs += [dict(port=2,device=1,idx=0,id=button,value=int(any(a['key']==letter for a in active)))
                       for letter,button in LETTERS.items()]
            inputs += [dict(port=2,device=5,idx=1,id=axis,value=sum(ANALOG[a['key']][1] for a in active if a['key'] in ANALOG and ANALOG[a['key']][0]==axis)) for axis in range(2)]
            for action in actions:
                if action['key'] in KEYBOARD and index in (action['frame'],action['frame']+4):
                    code=KEYBOARD[action['key']]
                    keys.append(dict(down=int(index==action['frame']),mod=0,code=code,character=code))
        result += struct.pack('<IB', 0, len(keys))
        for e in keys:
            result += struct.pack('<BBHII', e['down'], 0, e['mod'], e['code'], e['character'])
        result += struct.pack('<H', len(inputs))
        for e in inputs:
            result += struct.pack('<BBBBHh', e['port'], e['device'], e['idx'], 0, e['id'], e['value'])
        result += b'f'
    struct.pack_into('<I', result, 24, count)
    read_replay(result)
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('controls', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    plan = json.loads(args.controls.read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(build(args.source.read_bytes(), plan['actions'], plan['frames'], plan.get('prefix', 350)))
