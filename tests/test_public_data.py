import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import json

from engine.public_data import BASE, load, validate, render


class PublicDataTests(unittest.TestCase):
    def test_counts(self):
        result = validate()
        self.assertTrue(result['ok'], result['errors'])
        self.assertEqual(result['counts'], {
            'specs': 7, 'spell_records': 178, 'spell_ids': 176, 'tables': 23,
            'rows': 177, 'advanced_tips': 79, 'unresolved_spell_ids': 13})

    def test_render_deterministic(self):
        self.assertEqual(render(), render())
        output = render()
        self.assertEqual(output.count('<section data-guide'), 7)
        self.assertIn('실전 딜사이클 공략이 아닙니다', output)
        self.assertNotIn('<img', output)

    def test_approval_is_not_assumed(self):
        _, _, guides = load()
        for guide in guides:
            self.assertFalse(guide['publication']['automatic_publish_allowed'])
            for group in guide['rotation_groups']:
                for r in group['rules']:
                    self.assertEqual(r['review'], 'pending')
                    self.assertFalse(r['provenance']['external_source_verified'])

    def test_modified_review_state_rejected(self):
        with TemporaryDirectory() as tmp:
            from shutil import copytree
            copytree(BASE, Path(tmp)/'public')
            base = Path(tmp)/'public'
            path=base/'rules'/'fire.json'
            data=json.loads(path.read_text(encoding='utf8'))
            data['rotation_groups'][0]['rules'][0]['review']='approved'
            path.write_text(json.dumps(data,ensure_ascii=False),encoding='utf8')
            self.assertFalse(validate(base)['ok'])

    def test_full_copyrighted_text_absent(self):
        for path in BASE.rglob('*.json'):
            content=path.read_text(encoding='utf8')
            for forbidden in ('"intro_html"', '"text_ko"', '"evidence_ko"', '"raw_ko"', '"html"'):
                self.assertNotIn(forbidden,content,str(path))

if __name__ == '__main__':
    unittest.main()