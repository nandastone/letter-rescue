"""Rebuild registered-episode readable artwork layouts from verified shared pages.

See testing/wr2_wr3_implementation.md for native artwork/transcription evidence.
"""
from pathlib import Path
import json, copy

root = Path(__file__).resolve().parents[1]
base_text = json.loads((root/'data/wr1/clear_text_pages.json').read_text(encoding='utf-8'))
base_masks = json.loads((root/'data/wr1/clear_artwork.json').read_text(encoding='utf-8'))
colors = ['000000','0000aa','00aa00','00aaaa','aa0000','aa00aa','aaaa00','aa5500','aaaaaa','555555','5555ff','55ff55','55ffff','ff5555','ff55ff','ffff55','ffffff']

def label(rect, text, pixels=10, color='ffffff', align=None):
    result = dict(rect=rect, text=text, pixels=pixels, color=color)
    if align:
        result['align'] = align
    return result

def mask(rect, ink, background):
    return dict(rect=rect, ink=ink, background=background)

for ep in (2, 3):
    text = {k.replace('WR1.', f'WR{ep}.'): copy.deepcopy(v) for k,v in base_text.items() if k not in ('WR1.11','WR1.12')}
    masks = {k.replace('WR1.', f'WR{ep}.'): copy.deepcopy(v) for k,v in base_masks.items() if k not in ('WR1.11','WR1.12')}
    # Native title lettering is integrated with scenery. A clean blue panel
    # avoids residual bitmap lettering while retaining the lower landscape.
    text[f'WR{ep}.21'] = [label([18,8,284,122 if ep==2 else 100], 'Word\nRescue',34), label([140,163,170,22] if ep==2 else [120,120,174,23], f'Part {ep}',16,'aa0000')]
    masks[f'WR{ep}.21'] = [mask([0,0,320,140 if ep==2 else 115],colors,'0000aa'), mask([145,164,166,19] if ep==2 else [123,122,169,20],['aa0000','ff5555'],'ffffff' if ep==2 else 'ffff55')]
    if ep == 2:
        text['WR2.11'] = copy.deepcopy(base_text['WR1.12'])
        masks['WR2.11'] = copy.deepcopy(base_masks['WR1.12'])
    else:
        masks['WR3.21'].append(mask([5,172,72,24],colors,'000000'))
        stories = {
            'FSTORY1.WR': 'Look at those Gruzzles! Have they\nreturned to steal more words?\n\nNo! While they were stealing words\nthey learned to read.\n\n"Can we read your books?", the\nGruzzles asked.\nAnd...',
            'FSTORY2.WR': 'Benny said, "No problem"\nYou can read with us — as long as\nyou don\'t steal the words!\n\nSo the Gruzzles happily sat down\nto read and everything was peaceful\n\nUntil...',
            'FSTORY3.WR': 'Benny started teaching the\nchildren arithmetic.\n\nAnd you can guess what happened\nthen!\n\n(Watch for "Number Rescue" coming\nsoon...)',
        }
        for name, words in stories.items():
            text[name] = [label([54,12,214,90],words,9,'aa0000','left'),label([119,109,82,12],'Press a key',8)]
            masks[name] = [mask([51,10,218,93],['aa0000','ff5555'],'ffffff'),mask([119,109,82,12],['ffffff'],'aa0000')]
        text['FSTORY3.WR'].extend([label([70,127,37,12],'3 + 4 = 7',7,'0000aa'),label([93,143,46,12],'8 × 9 = 72',7,'0000aa')])
        masks['FSTORY3.WR'].extend([mask([70,128,34,9],['0000aa','aa00aa'],'55ffff'),mask([94,143,40,9],['0000aa'],'55ffff')])
    target = root/f'data/episodes/wr{ep}'
    target.mkdir(parents=True, exist_ok=True)
    (target/'clear_text_pages.json').write_text(json.dumps(text,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (target/'clear_artwork.json').write_text(json.dumps(masks,indent=2)+'\n',encoding='utf-8')
