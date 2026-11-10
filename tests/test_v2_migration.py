"""Copyright-safe V2 parity tests using invented actions, not source guide text."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from engine.v2.html_spans import SpanParser, find_class
from engine.v2.rules import extract_guide, digest
from engine.v2.diff_rules import diff_documents
from engine.v2.validate_rules import validate_directory
from engine.v2.contracts import evaluate

SCHEMA = Path(__file__).resolve().parents[1] / 'engine' / 'v2' / 'schemas' / 'rotation-rules.schema.json'
BASELINE = 'a' * 64


def guide_fixture():
    priority = ('<section id="synthetic-priority"><h2>우선순위</h2>'
                '<h3>단일 1~2명</h3><table><thead><tr><th>순위</th><th>행동</th><th>조건</th>'
                '</tr></thead><tbody><tr><td>1</td><td>가상 기술</td>'
                '<td>연계 점수 6점 이상</td></tr></tbody></table></section>')
    adv = ('<section id="synthetic-advanced"><h2>고급 운용</h2>'
           '<h3>가상 원칙</h3><p>합성 데이터 원칙입니다.</p></section>')
    return {'id': 'synthetic', 'class_ko': '시험용 직업', 'spec_ko': '시험용 전문화',
            'initial_hero': 'test_hero', 'hero_options': [{'id': 'test_hero'}],
            'glossary_index': [{'spell_id': 999999, 'name_ko': '가상 기술'}],
            'sections': [{'id': 'synthetic-priority', 'title_ko': '우선순위',
                          'source_sha256': digest(priority), 'html': priority},
                         {'id': 'synthetic-advanced', 'title_ko': '고급 운용',
                          'source_sha256': digest(adv), 'html': adv}]}


class V2MigrationTests(unittest.TestCase):
    def test_html_span_recovery(self):
        source = '<div class="manual-view"><section id="one">x</section></div>'
        spans = SpanParser(source).spans
        self.assertEqual(len(find_class(spans, 'div', 'manual-view')), 1)
        self.assertEqual([x.full(source) for x in spans if x.tag == 'section'],
                         ['<section id="one">x</section>'])

    def test_priority_and_advanced_extraction(self):
        doc = extract_guide(guide_fixture(), BASELINE)
        self.assertEqual(len(doc['rotation_groups']), 1)
        self.assertEqual(len(doc['rotation_groups'][0]['rules']), 1)
        self.assertEqual(len(doc['advanced_guidance']), 1)
        rule = doc['rotation_groups'][0]['rules'][0]
        self.assertEqual(rule['action']['spell_id'], 999999)
        self.assertEqual(rule['condition']['predicates'][0]['value'], 6)
        self.assertEqual(rule['review']['state'], 'pending')
        self.assertFalse(rule['evidence']['original_wowhead_passage_verified'])
        self.assertEqual(doc['publication']['status'], 'blocked_pending_review')

    def test_source_checked_is_not_assumed(self):
        doc = extract_guide(guide_fixture(), BASELINE)
        row = doc['rotation_groups'][0]['rules'][0]
        self.assertEqual(row['condition']['formalization'], 'partial_syntax_only_not_executable')
        self.assertFalse(row['evidence']['original_wowhead_passage_verified'])

    def test_priority_change_requires_review(self):
        old = extract_guide(guide_fixture(), BASELINE)
        new = deepcopy(old)
        new['rotation_groups'][0]['rules'][0]['condition']['raw_ko'] = '임의로 변경'
        changes = diff_documents(old, new)
        self.assertEqual(changes[0]['severity'], 'high')
        self.assertFalse(changes[0]['automatic_publish_allowed'])

    def test_advanced_change_requires_review(self):
        old = extract_guide(guide_fixture(), BASELINE)
        new = deepcopy(old)
        new['advanced_guidance'][0]['text_ko'] += ' 변경'
        changes = diff_documents(old, new)
        self.assertEqual(changes[0]['severity'], 'medium')

    def test_deleted_rule_is_critical(self):
        old = extract_guide(guide_fixture(), BASELINE)
        new = deepcopy(old)
        new['rotation_groups'][0]['rules'] = []
        changes = diff_documents(old, new)
        self.assertEqual(changes[0]['severity'], 'critical')

    def test_tristate_missing_context(self):
        expr = {'all': [{'field': 'hero', 'op': 'eq', 'value': 'test_hero'},
                        {'field': 'buff:example', 'op': 'gte', 'value': 6}]}
        self.assertIsNone(evaluate(expr, {'hero': 'test_hero'}))
        self.assertFalse(evaluate(expr, {'hero': 'not_it'}))
        self.assertTrue(evaluate(expr, {'hero': 'test_hero', 'buffs': {'example': 6}}))

    def test_validate_from_synthetic_source(self):
        guide = guide_fixture()
        doc = extract_guide(guide, BASELINE)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for folder in ('schemas', 'content/guides', 'content/rules'):
                (root / folder).mkdir(parents=True, exist_ok=True)
            (root / 'schemas/rotation-rules.schema.json').write_bytes(SCHEMA.read_bytes())
            (root / 'content/registry.json').write_text(json.dumps({
                'import_source_sha256': BASELINE,
                'guides': [{'id': 'synthetic', 'file': 'guides/synthetic.json'}]
            }), encoding='utf-8')
            (root / 'content/guides/synthetic.json').write_text(json.dumps(guide), encoding='utf-8')
            path = root / 'content/rules/synthetic.json'
            path.write_text(json.dumps(doc), encoding='utf-8')
            result = validate_directory(root)
            self.assertEqual(result['status'], 'PASS', result['errors'])
            self.assertEqual(result['stats']['priority_row_count'], 1)
            self.assertEqual(result['stats']['advanced_item_count'], 1)
            doc['rotation_groups'][0]['rules'][0]['condition']['raw_ko'] = '근거 없는 변경'
            path.write_text(json.dumps(doc), encoding='utf-8')
            result = validate_directory(root)
            self.assertEqual(result['status'], 'FAIL')
            self.assertTrue(any('differs from source HTML' in e for e in result['errors']))


if __name__ == '__main__':
    unittest.main()
