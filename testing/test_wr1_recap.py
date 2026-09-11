import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from prepare_wr1_boundaries import gameplay_instructions, STAGES
from prepare_wr1_recap import prepare


class RecapBoundaryTests(unittest.TestCase):
    def sequence(self):
        rows = [{'event':'instruction', 'ip':ip} for ip in STAGES[:2]]
        rows += [{'event':'lifecycle', 'ip':0x151c, 'pic_ms':1},
                 {'event':'lifecycle', 'ip':0x194f, 'pic_ms':2}]
        rows += [{'event':'instruction', 'ip':ip} for ip in STAGES]
        return rows

    def test_only_abandoned_admission_is_excluded(self):
        instructions, cutscenes = gameplay_instructions(self.sequence())
        self.assertEqual([r['ip'] for r in instructions], list(STAGES))
        self.assertEqual(len(cutscenes), 1)
        self.assertEqual(len(cutscenes[0]['admission']), 2)

    def test_missing_or_reordered_lifecycle_is_rejected(self):
        for index in range(4):
            rows = self.sequence()
            del rows[index]
            with self.assertRaises(ValueError):
                gameplay_instructions(rows)
        rows = self.sequence()
        rows.insert(3, {'event':'instruction', 'ip':STAGES[2]})
        with self.assertRaises(ValueError):
            gameplay_instructions(rows)

    def test_reference_rng_and_each_word_are_complete(self):
        fixture = json.loads((ROOT/'testing/fixtures/wr1_recap_stages.json').read_text())
        rng = fixture['begin']['rng']
        melts = []
        for draw in fixture['renders']:
            if draw['draw']['kind'] == 'dissolve':
                melts.append(draw['draw']['order'])
                for _ in range(80):
                    rng = (rng * 0x15a4e35 + 1) & 0xffffffff
            self.assertEqual(rng, draw['state']['rng'])
        self.assertEqual(melts, [word for word in range(7) for _ in range(20)])
        self.assertEqual(rng, fixture['end']['rng'])


if __name__ == '__main__':
    unittest.main()
