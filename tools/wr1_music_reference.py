"""WR1 embedded CMF sequencer, EXE1f56b..1f858; emits events, not audio."""
import copy
import struct


FIELDS = ('counter','beats','division','format','repeat','playing','data_offset','tracks')
PARAMETERS = (2,2,2,2,1,1,2,0)


class Music:
    def __init__(self, data, initial):
        if data[:4] != b'CTMF' or initial['format'] != 1:
            raise ValueError('This model requires the observed CMF driver mode')
        self.data = data
        self.state = {k:copy.deepcopy(initial[k]) for k in FIELDS}
        self.restarted = False

    def byte(self, cursor):
        return self.data[(cursor-self.state['data_offset']) & 0xffff]

    def vlq(self, cursor):
        value = 0
        while True:
            byte = self.byte(cursor)
            cursor = (cursor+1) & 0xffff
            value = ((value << 7) | (byte & 127)) & 0xffffffff
            if byte < 128:
                return value,cursor

    def restart(self):
        self.restarted = True
        s = self.state
        s['counter'] = s['beats'] = 0
        s['division'] = struct.unpack_from('<H',self.data,10)[0]
        cursor = (s['data_offset']+struct.unpack_from('<H',self.data,8)[0]) & 0xffff
        delay,cursor = self.vlq(cursor)
        # Initialization resets active slots, but preserves running-status bytes.
        status = s['tracks'][0]['status'] if s['tracks'] else 0
        s['tracks'] = [dict(active=1,delay=delay,cursor=cursor,status=status)]
        s['playing'] = 1

    def tick(self):
        self.restarted = False
        s,events = self.state,[]
        if not s['playing']:
            return events
        s['counter'] = (s['counter']+1) & 0xffff
        if s['counter'] >= s['division']:
            s['counter'] = 0
            s['beats'] = (s['beats']+1) & 0xffff
        for track in s['tracks']:
            if not track['active']:
                continue
            delay = track['delay']
            # Preserve the original word-sum comparison, including its wrap.
            if ((delay & 0xffff)+(delay >> 16)) & 0xffff > 1:
                track['delay'] = (delay-1) & 0xffffffff
                continue
            cursor = track['cursor']
            while True:
                status = self.byte(cursor)
                cursor = (cursor+1) & 0xffff
                if status == 255:
                    kind = self.byte(cursor)
                    cursor = (cursor+1) & 0xffff
                    if kind == 47:
                        track['active'] = 0
                        if not any(t['active'] for t in s['tracks']):
                            if s['repeat']:
                                self.restart()
                            else:
                                s['playing'] = 0
                            return events
                        break
                    size = self.byte(cursor)
                    cursor = (cursor+1) & 0xffff
                    payload = [self.byte((cursor+i)&0xffff) for i in range(size)]
                    events.append(dict(status=255,kind=kind,data=payload))
                    cursor = (cursor+size) & 0xffff
                else:
                    if status < 128:
                        cursor = (cursor-1) & 0xffff
                        status = track['status']
                    else:
                        track['status'] = status
                    size = PARAMETERS[(status>>4)-8]
                    payload = [self.byte((cursor+i)&0xffff) for i in range(size)]
                    events.append(dict(status=status,data=payload))
                    cursor = (cursor+size) & 0xffff
                delay,cursor = self.vlq(cursor)
                if delay:
                    track['delay'],track['cursor'] = delay,cursor
                    break
        return events
