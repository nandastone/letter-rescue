"""Index large native JSONL traces for fast, exact time-window inspection.

The index stores byte offsets, never substitute observations. Queries read the
original lines and reject an index if the source size or modification time changed.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3

FIELDS = {key:re.compile(rb'"'+key.encode()+rb'":(?:"([^"\\]*)"|(-?[\d.]+))')
          for key in ('event','kind','ip','pic_ms','launch_call','call')}


def signature(path):
    info = path.stat()
    return [info.st_size, info.st_mtime_ns]


def index_path(trace):
    return Path(trace).with_suffix('.index.sqlite')


def build(trace):
    trace = Path(trace).resolve()
    destination = index_path(trace)
    if destination.exists():
        validate(trace, destination)
        return destination
    before = signature(trace)
    partial = destination.with_suffix('.building.sqlite')
    if partial.exists():
        raise ValueError(f'Incomplete index already exists: {partial}')
    db = sqlite3.connect(partial)
    db.execute('CREATE TABLE metadata (value TEXT NOT NULL)')
    db.execute('CREATE TABLE records (offset INTEGER, length INTEGER, event TEXT, kind TEXT, ip INTEGER, ms REAL, counter INTEGER)')
    digest = hashlib.sha256()
    batch = []
    offset = 0
    with trace.open('rb',buffering=16*1024*1024) as stream:
        for line in stream:
            digest.update(line)
            head = line[:1024]
            fields = {}
            for key, pattern in FIELDS.items():
                match = pattern.search(head)
                fields[key] = (match[1].decode() if match[1] is not None else float(match[2])) if match else None
            batch.append((offset,len(line),fields['event'],fields['kind'],fields['ip'],fields['pic_ms'],fields['launch_call'] or fields['call']))
            offset += len(line)
            if len(batch) == 10000:
                db.executemany('INSERT INTO records VALUES (?,?,?,?,?,?,?)',batch)
                batch.clear()
    db.executemany('INSERT INTO records VALUES (?,?,?,?,?,?,?)',batch)
    if signature(trace) != before:
        raise ValueError('Trace changed while indexing; partial index retained')
    db.execute('CREATE INDEX by_time ON records(ms)')
    db.execute('INSERT INTO metadata VALUES (?)',(json.dumps({'trace':str(trace),'signature':before,'sha256':digest.hexdigest()}),))
    db.commit()
    db.close()
    partial.rename(destination)
    return destination


def validate(trace, index):
    with closing(sqlite3.connect(f'{Path(index).resolve().as_uri()}?mode=ro',uri=True)) as db:
        metadata = json.loads(db.execute('SELECT value FROM metadata').fetchone()[0])
    if metadata['trace'] != str(Path(trace).resolve()) or metadata['signature'] != signature(Path(trace)):
        raise ValueError('Trace changed; keep the old index and build a fresh one for the changed source')
    return metadata


def window(trace, start_ms, end_ms, events=()):
    trace = Path(trace).resolve()
    index = index_path(trace)
    validate(trace,index)
    sql = 'SELECT offset,length FROM records WHERE ms>=? AND ms<=?'
    values = [start_ms,end_ms]
    if events:
        sql += ' AND event IN ('+','.join('?' for _ in events)+')'
        values.extend(events)
    sql += ' ORDER BY offset'
    with closing(sqlite3.connect(f'{index.as_uri()}?mode=ro',uri=True)) as db, trace.open('rb') as stream:
        for offset,length in db.execute(sql,values):
            stream.seek(offset)
            yield json.loads(stream.read(length))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace',type=Path)
    parser.add_argument('--start-ms',type=float)
    parser.add_argument('--end-ms',type=float)
    parser.add_argument('--event',action='append',default=[])
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    index = build(args.trace)
    if args.start_ms is None:
        print(index)
    else:
        if args.end_ms is None or args.output is None:
            parser.error('A window requires --end-ms and --output')
        rows = list(window(args.trace,args.start_ms,args.end_ms,args.event))
        args.output.write_text(json.dumps(rows,separators=(',',':'))+'\n')
        print(f'{len(rows)} exact native rows -> {args.output}')
