"""Explain the saved hard-impact divergence; reconstructed images are diagnostic only.

This does not modify game input, native fixtures, or the strict parity verdict.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('trace', 'native', 'clone-before', 'clone-after', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    native, before, after = [Image.open(p).convert('RGB') for p in
                             (args.native,args.clone_before,args.clone_after)]
    if any(im.size != (320,200) for im in (native,before,after)):
        raise ValueError('Expected original 320x200 images')
    composite = before.copy()
    composite.paste(after.crop((0,150,320,200)), (0,150))

    def different_pixels(a,b):
        channels = iter(bytes(x ^ y for x,y in zip(a.tobytes(),b.tobytes())))
        return sum(any(p) for p in zip(channels,channels,channels))

    report = {'scope':'diagnostic reconstruction only; never a parity pass',
              'sha256': {name:hashlib.sha256(path.read_bytes()).hexdigest()
                         for name,path in [('native',args.native),('clone_before',args.clone_before),('clone_after',args.clone_after)]},
              'pixels': {'native_vs_before':different_pixels(native,before),
                         'native_vs_after':different_pixels(native,after),
                         'native_vs_split_at_150':different_pixels(native,composite)},
              'irq_boundary': [], 'presentation': []}
    seen_impact = False
    end_time = 0.0
    raster = None
    trace_digest = hashlib.sha256()
    with args.trace.open('rb') as stream:
        for line in stream:
            trace_digest.update(line)
            row = json.loads(line)
            event, time = row['event'], row.get('pic_ms',0)
            if event == 'irq' and row.get('launch_call') in (914,915):
                report['irq_boundary'].append({k:row.get(k) for k in ('event','ip','launch_call','pic_ms','timer')})
            if event == 'frontend' and row['call'] == 915:
                report['irq_boundary'].append({k:row.get(k) for k in ('event','call','pic_ms','timer')})
            if event == 'instruction' and row['ip'] == 0x444 and row['launch_call'] == 915:
                report['irq_boundary'].append({k:row.get(k) for k in ('event','ip','launch_call','pic_ms','timer')})
            if event == 'instruction' and row['ip'] == 0x444 and row['launch_call'] == 938:
                seen_impact, end_time = True, time + 45
            if not seen_impact or time > end_time:
                continue
            keep = event == 'frontend' or (event == 'instruction' and row['ip'] in (0x444,0xd44))
            if event == 'graphics':
                keep = row['kind'] in ('renderer','display_page') or (
                    row['kind'] == 'masked_sprite' and row['args'][4] in (-18548,-27018))
                if row['kind'] == 'renderer' and not row['entry'] and row['launch_call'] == 939 and raster is None:
                    raster = row['vga_timing']
            if keep:
                report['presentation'].append({k:row[k] for k in
                    ('event','kind','entry','ip','call','launch_call','pic_ms','args','render_page','display_page') if k in row})
    report['sha256']['trace'] = trace_digest.hexdigest()
    if raster is None or raster['parts_lines'] != 50 or raster['lines_total'] != 200:
        raise ValueError('Expected the measured four-part VGA scanout')
    report['scanout'] = {'frame_start_ms':raster['frame_start'],
        'display_start_latch_ms':raster['frame_start']-raster['vtotal']+raster['vrstart'],
        'chunks':[{'rows':[50*i,50*i+49], 'time_ms':raster['frame_start']+(i+1)*raster['parts']} for i in range(4)]}
    (args.output/'diagnosis.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    composite.save(args.output/'reconstructed_scanout.png')
    print(json.dumps({'pixels':report['pixels'],'scanout':report['scanout']},indent=2))
    if report['pixels']['native_vs_split_at_150'] != 0:
        raise SystemExit('The two-render reconstruction did not explain this image')


if __name__ == '__main__':
    main()
