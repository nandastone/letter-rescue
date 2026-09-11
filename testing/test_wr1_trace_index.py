import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from index_wr1_trace import build,window


class TraceIndexTests(unittest.TestCase):
    def test_exact_window_and_changed_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'native.jsonl'
            rows=[{'event':'instruction','ip':1092,'pic_ms':12.25,'launch_call':3,'state':[1,2,3]},
                  {'event':'frontend','call':4,'pic_ms':14.0},
                  {'event':'instruction','ip':3442,'pic_ms':15.5,'launch_call':4}]
            source.write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows))
            build(source)
            self.assertEqual(list(window(source,12,15)),rows[:2])
            self.assertEqual(list(window(source,12,16,['instruction'])),[rows[0],rows[2]])
            source.write_text(source.read_text()+'{}\n')
            with self.assertRaisesRegex(ValueError,'changed'):
                list(window(source,12,16))


if __name__=='__main__':unittest.main()
