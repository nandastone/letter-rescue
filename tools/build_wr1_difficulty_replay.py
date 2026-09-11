"""Select difficulty and a drip map through WR1's own menus, with no RAM edits."""
import argparse
import struct
import json
from pathlib import Path
from bsv_replay import frame_start, read_replay


def build(data, difficulty, character='girl', count=1500, route=(), route_start=620, slime_windows=(), level=14):
    header, frames = read_replay(data)
    if len(frames) != 770 or difficulty not in ('medium','hard'):
        raise ValueError('Require the controlled 770-frame replay and medium/hard')
    if any(not route_start <= start < end <= count for start, end in slime_windows):
        raise ValueError('Slime windows must lie within the gameplay route')
    if not 1 <= level <= 15 or any(digit not in '1234' for digit in str(level)):
        raise ValueError('This keyboard mapping supports level digits 1..4 only')
    # Use polled Generic Keyboard controls: BSV callback-only keys do not reach
    # this core's active controller mapping. Escape, D, down(s), Enter, Escape.
    result = bytearray(data[:frame_start(data,header)])
    for index in range(count):
        source = frames[min(index,len(frames)-1)]
        keys = source['key_events'] if index < 350 else []
        inputs = [dict(e) for e in source['input_events']]
        if character == 'boy' and 248 <= index < 258:
            for e in inputs:
                if e['port']==0 and e['device']==1 and e['id']==7:
                    e['value'] = int(index < 253)
        if index >= 350:
            for e in inputs:
                e['value'] = 0
            # Z+L level selector on Generic Keyboard port2; digits1/4 and Enter.
            inputs += [{'port':2,'device':1,'idx':0,'id':6,'value':int(520<=index<526)},
                       {'port':2,'device':1,'idx':0,'id':9,'value':int(420<=index<424)},
                       {'port':2,'device':5,'idx':1,'id':0,'value':32767 if 520<=index<526 else 0}]
            buttons = {2:400<=index<404 or 490<=index<494,
                       5:440<=index<444 or (difficulty=='hard' and 450<=index<454),
                       3:470<=index<474 or 544<=index<548}
            for digit in '1234':
                buttons[9+int(digit)] = any(char == digit and 530+6*i <= index < 533+6*i
                                           for i,char in enumerate(str(level)))
            if index >= route_start:
                step = int((index-route_start+.5)/(12428*8/1193182*70.086304))
                action = route[step] if step < len(route) else {}
                buttons.update({4:action.get('up',False),5:action.get('down',False),
                                6:action.get('left',False),7:action.get('right',False),
                                9:any(start <= index < end for start,end in slime_windows)})
            for e in inputs:
                if e['port']==0 and e['device']==1 and e['id'] in buttons:
                    e['value'] = int(buttons[e['id']])
        result += struct.pack('<IB',0,len(keys))
        for e in keys:
            result += struct.pack('<BBHII',e['down'],0,e['mod'],e['code'],e['character'])
        result += struct.pack('<H',len(inputs))
        for e in inputs:
            result += struct.pack('<BBBBHh',e['port'],e['device'],e['idx'],0,e['id'],e['value'])
        result += b'f'
    struct.pack_into('<I',result,24,count)
    read_replay(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--difficulty',choices=['medium','hard'],required=True)
    parser.add_argument('--character',choices=['boy','girl'],default='girl')
    parser.add_argument('--frames',type=int,default=1500)
    parser.add_argument('--level',type=int,default=14)
    parser.add_argument('--route',type=Path)
    parser.add_argument('--route-start',type=int,default=620)
    parser.add_argument('--slime-window',type=int,nargs=2,action='append',default=[],metavar=('START','END'),
                        help='Press slime during this half-open source-frame interval; repeatable')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    route = json.loads(args.route.read_text())['actions'] if args.route else ()
    args.output.write_bytes(build(args.source.read_bytes(),args.difficulty,args.character,args.frames,route,args.route_start,args.slime_window,args.level))


if __name__ == '__main__':
    main()
