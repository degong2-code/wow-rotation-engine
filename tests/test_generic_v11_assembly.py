"""Synthetic cross-specialization packaging regressions: no private HTML."""
import unittest
from engine.v2.generic_v11_assembly import repackage, Scanner, guides, h

IDS=('fire', 'frost', 'dk', 'hunter', 'bm', 'rogue', 'assassination')


def baseline():
    nav='<nav class="toc"><div class="tree">'+''.join(
        f'<button data-guide-button="{x}">{x}</button>' for x in IDS
    )+'</div>'+''.join(
        f'<div class="reader-toc" data-nav-guide="{x}"><a href="#{x}-overview">overview</a></div>'
        for x in IDS
    )+'</nav>'
    guidestr=''.join(
        f'<div id="guide-{x}" class="manual-view" data-guide="{x}">'
        f'<section id="{x}-overview"><p>Original V11 {x}</p></section></div>'
        for x in IDS
    )
    return ('<!DOCTYPE html><html><head><style>body{margin:0}</style></head>'
            '<body>'+nav+'<main>'+guidestr+'</main>'
            '<script>window.originalTooltips=true;</script>'
            '<script>const views={fire:true};</script></body></html>')


def authored(base, spec='newcase', heroes=('alpha', 'beta', 'gamma'),
             *, extra_script=True):
    s=base.replace('</div></nav>',
        ''.join(f'<button data-guide-button="{spec}" data-hero-button="{hero}">{hero}</button>'
                for hero in heroes)
        +'</div><div class="reader-toc" data-nav-guide="'+spec+'">'
         '<a href="#'+spec+'-overview">overview</a></div></nav>')
    guide=(f'<div id="guide-{spec}" class="manual-view v11-visual-contract" '
           f'data-guide="{spec}" data-hero="{heroes[0]}">'
           f'<section id="{spec}-overview"><h1>Original authored content</h1></section>'
           f'<section id="{spec}-rotation"><table><tr data-canonical-id="rule-1">'
           f'<td>1</td><td>행동</td><td>조건</td></tr></table></section></div>')
    s=s.replace('</main>',guide+'</main>')
    s=s.replace('</head>', '<style>.v11-visual-contract{color:inherit}</style></head>')
    s=s.replace('<script>const views={fire:true};</script>',
                '<script>const views={fire:true,'+spec+':true};</script>')
    if extra_script:
        s=s.replace('</body>','<script>window.visualExtension=true;</script></body>')
    return s


class GenericV11AssemblyTests(unittest.TestCase):
    def test_three_hero_variant_not_locked_to_arcane(self):
        original=baseline(); draft=authored(original)
        output,report=repackage(original,draft,expected_baseline_sha256=h(original))
        self.assertEqual(report['spec'],'newcase')
        self.assertEqual(set(guides(Scanner(output))),{*IDS,'newcase'})
        self.assertEqual(report['all_legacy_subtrees_byte_identical'],True)
        self.assertIn('data-canonical-id="rule-1"',output)
        self.assertIn('data-hero-button="gamma"',output)
        self.assertIn('window.visualExtension=true',output)
        self.assertIn('const chosenHero=',output)
        self.assertFalse(report['automatic_publish_allowed'])
        self.assertFalse(report['gameplay_meaning_verified'])

    def test_one_hero_variant_does_not_require_four_tables(self):
        original=baseline();draft=authored(original,'compact',heroes=('only',))
        output,report=repackage(original,draft,expected_baseline_sha256=h(original))
        self.assertEqual(report['spec'],'compact')
        self.assertEqual(output.count('data-hero-button="only"'),1)
        self.assertEqual(output.count('data-canonical-id="rule-1"'),1)

    def test_modified_v11_original_is_rejected(self):
        original=baseline();draft=authored(original)
        draft=draft.replace('Original V11 fire','Modified V11 fire')
        with self.assertRaisesRegex(ValueError,'legacy V11 guide subtree'):
            repackage(original,draft,expected_baseline_sha256=h(original))

    def test_pinned_baseline_digest_is_required(self):
        original=baseline();draft=authored(original)
        with self.assertRaisesRegex(ValueError,'baseline digest mismatch'):
            repackage(original,draft)

    def test_no_new_guide_is_rejected(self):
        original=baseline()
        with self.assertRaisesRegex(ValueError,'exactly one'):
            repackage(original,original,expected_baseline_sha256=h(original))

    def test_multiple_new_guides_are_rejected(self):
        original=baseline();draft=authored(original)
        draft=draft.replace('</main>',
            '<div class="manual-view" data-guide="second" id="guide-second"></div></main>')
        with self.assertRaisesRegex(ValueError,'exactly one'):
            repackage(original,draft,expected_baseline_sha256=h(original))

    def test_duplicate_ids_are_rejected(self):
        original=baseline();draft=authored(original)
        draft=draft.replace('<h1>Original authored content</h1>',
                             '<h1 id="guide-fire">Original authored content</h1>')
        with self.assertRaisesRegex(ValueError,'Duplicate document ids'):
            repackage(original,draft,expected_baseline_sha256=h(original))

    def test_cannot_package_modified_original_v11_styles(self):
        original=baseline();draft=authored(original)
        draft=draft.replace('body{margin:0}','body{margin:1}')
        with self.assertRaisesRegex(ValueError,'stylesheet was modified'):
            repackage(original,draft,expected_baseline_sha256=h(original))


if __name__=='__main__':unittest.main()