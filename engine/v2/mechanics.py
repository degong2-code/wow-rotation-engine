"""Evidence-aware V11 mechanics presentation primitives for new guides.

Links refer only to known spell registry keys. A mechanic relates to existing
rotation-row IDs, not to claimed external verification. No HTML from input is
trusted. The same V11 spell tooltip, sequence and comparison styles are used.
"""
from __future__ import annotations

from html import escape
import re

SPELL_TOKEN = re.compile(r'\[\[spell:([a-z0-9-]+)\]\]')
REVIEW = 'needs_manual_gameplay_review'


def rich(text: str, spells: dict, render_spell) -> str:
    """Explicit inline spell references; escape all other authored text."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Rich V11 text is empty')
    chunks = []
    position = 0
    for match in SPELL_TOKEN.finditer(text):
        prefix = text[position:match.start()]
        if '[[' in prefix or ']]' in prefix:
            raise ValueError('Malformed or nested V11 spell token')
        key = match.group(1)
        spell = spells.get(key)
        if spell is None:
            raise ValueError('Unknown V11 spell reference: ' + key)
        chunks.extend((escape(prefix, quote=True), render_spell(spell)))
        position = match.end()
    suffix = text[position:]
    if '[[' in suffix or ']]' in suffix:
        raise ValueError('Malformed V11 spell token')
    chunks.append(escape(suffix, quote=True))
    return ''.join(chunks)


def validate(mechanics: dict, draft: dict) -> dict:
    if not isinstance(mechanics, dict) or mechanics.get('schema_version') != 'v11-mechanics-v1':
        raise ValueError('V11 mechanism map required')
    if set(mechanics) != {'schema_version', 'flows', 'comparisons'}:
        raise ValueError('Unexpected V11 mechanism fields')
    flows = mechanics['flows']
    comparisons = mechanics['comparisons']
    if not isinstance(flows, list) or len(flows) < 3:
        raise ValueError('At least three fully explained V11 mechanics flows required')
    if not isinstance(comparisons, list) or len(comparisons) < 1:
        raise ValueError('At least one action/condition comparison required')
    spells = {spell['key']: spell for spell in draft['spells']}
    rules = {row['id'] for group in draft['rotation_groups'] for row in group['rows']}
    ids = set()
    linked_rules = set()
    spell_usage = set()

    def item_identity(item, prefix):
        if not isinstance(item, dict) or not re.fullmatch(r'[a-z0-9-]+', item.get('id', '')):
            raise ValueError('Missing safe V11 mechanism ID')
        if item['id'] in ids:
            raise ValueError('Duplicate V11 mechanism ID')
        ids.add(item['id'])
        if item.get('review') != REVIEW:
            raise ValueError('Unverified mechanics cannot be marked approved')
        related = item.get('related_rule_ids')
        if not isinstance(related, list) or not related or any(r not in rules for r in related):
            raise ValueError('Mechanics must link to existing rule IDs: ' + item['id'])
        linked_rules.update(related)
        for key in ('title', 'context', 'why', 'exception'):
            if not isinstance(item.get(key), str) or len(item[key].strip()) < 12:
                raise ValueError('Mechanics need specific context, rationale and exception: ' + item['id'])

    for item in flows:
        item_identity(item, 'flow')
        if item.get('section') not in ('basics', 'opener'):
            raise ValueError('Unsupported V11 flow section')
        steps = item.get('steps')
        if not isinstance(steps, list) or len(steps) < 3:
            raise ValueError('Mechanics flow requires three or more interpreted steps')
        if not any(step.get('kind') == 'spell' for step in steps):
            raise ValueError('Mechanics flow must link real identified spells')
        for step in steps:
            if not isinstance(step, dict) or step.get('kind') not in ('spell', 'state'):
                raise ValueError('Unknown flow step kind')
            if step['kind'] == 'spell':
                if step.get('key') not in spells:
                    raise ValueError('Unknown spell in V11 mechanics flow')
                spell_usage.add(step['key'])
            elif not isinstance(step.get('label'), str) or not step['label'].strip():
                raise ValueError('Missing flow state label')
            if not isinstance(step.get('meaning'), str) or not step['meaning'].strip():
                raise ValueError('Every action requires a concrete role or condition')
    for item in comparisons:
        item_identity(item, 'comparison')
        rows = item.get('rows')
        if not isinstance(rows, list) or len(rows) < 2:
            raise ValueError('Comparison requires two or more real situations')
        for row in rows:
            if not isinstance(row, dict) or not all(isinstance(row.get(k), str) and row[k].strip() for k in ('scenario', 'condition', 'action_key', 'reason')):
                raise ValueError('Comparison row requires scenario, action and rationale')
            if row['action_key'] not in spells:
                raise ValueError('Unknown comparison action spell')
            spell_usage.add(row['action_key'])
    if len(spell_usage) < 4:
        raise ValueError('Mechanics too sparse: fewer than four distinct spell links')
    return {
        'flows': len(flows), 'comparisons': len(comparisons),
        'linked_rule_count': len(linked_rules), 'distinct_spell_links': len(spell_usage),
        'external_evidence_verified': False,
    }


def render_flows(mechanics: dict, section: str, spells: dict, render_spell, note_for=None) -> str:
    output = []
    for index, item in enumerate((f for f in mechanics['flows'] if f['section'] == section), 1):
        seq = []
        for step in item['steps']:
            item_html = (render_spell(spells[step['key']]) if step['kind'] == 'spell'
                         else '<b>' + escape(step['label'], quote=True) + '</b>')
            seq.append(item_html)
        output.append(
            '<div class="mechanic-flow" data-mechanic-id="' + escape(item['id'], quote=True) + '">'
            '<h3>' + escape(item['title'], quote=True) + (' ' + note_for('mechanic', item['id']) if note_for else '') + '</h3>'
            '<p class="rule">' + escape(item['context'], quote=True) + '</p>'
            '<p class="sequence">' + ' <b>→</b> '.join(seq) + '</p>'
            '<ol class="steps compact">' + ''.join(
                '<li>' + (render_spell(spells[step['key']]) if step['kind'] == 'spell'
                          else '<b>' + escape(step['label'], quote=True) + '</b>')
                + ' — ' + escape(step['meaning'], quote=True) + '</li>'
                for step in item['steps']
            ) + '</ol>'
            '<p><b>왜 이 순서인가:</b> ' + escape(item['why'], quote=True) + '</p>'
            '<p class="tiny-rule"><b>주의:</b> ' + escape(item['exception'], quote=True) + '</p>'
            '</div>'
        )
    return ''.join(output)


def render_comparisons(mechanics: dict, spells: dict, render_spell, note_for=None) -> str:
    parts = []
    for item in mechanics['comparisons']:
        rows = ''.join(
            '<tr><td>' + escape(row['scenario'], quote=True) + '</td>'
            '<td>' + escape(row['condition'], quote=True) + '</td>'
            '<td>' + render_spell(spells[row['action_key']]) + '</td>'
            '<td>' + escape(row['reason'], quote=True) + '</td></tr>'
            for row in item['rows']
        )
        parts.append(
            '<div class="mechanic-comparison" data-mechanic-id="' + escape(item['id'], quote=True) + '">'
            '<h3>' + escape(item['title'], quote=True) + (' ' + note_for('mechanic', item['id']) if note_for else '') + '</h3>'
            '<p>' + escape(item['context'], quote=True) + '</p>'
            '<div class="table-scroll"><table class="comparison"><thead><tr>'
            '<th>상황</th><th>판단 조건</th><th>행동 후보</th><th>이유</th>'
            '</tr></thead><tbody>' + rows + '</tbody></table></div>'
            '<p><b>핵심 차이:</b> ' + escape(item['why'], quote=True) + '</p>'
            '<p class="tiny-rule"><b>예외:</b> ' + escape(item['exception'], quote=True) + '</p>'
            '</div>'
        )
    return ''.join(parts)
