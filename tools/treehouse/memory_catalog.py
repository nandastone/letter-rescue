"""Read the original loaded archive directory from an offline physical RAM fixture."""
import struct
from pathlib import PureWindowsPath

def read_files(data,ss):
    """File-list state rooted at 204C; distinct from lookup priority at 204E."""
    def word(p):return struct.unpack_from('<H',data,p)[0]
    handle=word(ss*16+0x204c);seen=set();files=[]
    while handle:
        if handle in seen:raise ValueError('Cyclic file list')
        seen.add(handle);state,segment=struct.unpack_from('<HH',data,ss*16+handle)
        if state&0x200:raise ValueError('File descriptor in EMS')
        p=16*segment+(state&15)+6
        files.append(dict(handle=handle,fileHandle=word(p+2),
            volume=data[p+4:p+16].split(b'\0',1)[0].decode('ascii'),
            filename=data[p+16:p+80].split(b'\0',1)[0].decode('ascii')))
        handle=word(p)
    return files


def read_catalogs(data,ss):
    def word(p):return struct.unpack_from('<H',data,p)[0]
    handle=word(ss*16+0x204e);seen=set();catalogs=[]
    while handle:
        if handle in seen:raise ValueError('Cyclic archive list')
        seen.add(handle);state,segment=struct.unpack_from('<HH',data,ss*16+handle)
        if state&0x200:raise ValueError('Archive directory in EMS')
        p=16*segment+(state&15)+6
        filename=data[p+16:p+80].split(b'\0',1)[0].decode('ascii')
        archive=PureWindowsPath(filename).stem.lower();records=[];types=[]
        for i in range(word(p+80)):
            tag,relative=struct.unpack_from('<IH',data,p+82+i*6)
            tag=tag.to_bytes(4,'big').strip(b'\0').decode('ascii')
            table=p+80+relative
            ids=[]
            for j in range(word(table)):
                row=table+2+j*11;id,offset,length=struct.unpack_from('<HIH',data,row)
                ids.append(id)
                records.append(dict(tag=tag,id=id,offset=offset,length=length,flags=data[row+8],handle=word(row+9)))
            types.append(dict(tag=tag,relative=relative,ids=ids))
        catalogs.append(dict(handle=handle,state=state,segment=segment,archive=archive,records=records,types=types));handle=word(p)
    return catalogs
