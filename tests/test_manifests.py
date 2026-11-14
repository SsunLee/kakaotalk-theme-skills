"""Keep the Claude Code plugin/marketplace manifests consistent with the repository."""
import json
import unittest

from test_tools import ROOT

NAMES = ['kakaotalk-theme-builder', 'kakaotalk-theme-publisher']


class ManifestTest(unittest.TestCase):
    def test_versions_and_skill_layout(self):
        version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        plugin = json.loads((ROOT / '.claude-plugin/plugin.json').read_text(encoding='utf-8'))
        market = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text(encoding='utf-8'))
        self.assertEqual(plugin['version'], version)
        entry = next(p for p in market['plugins'] if p['name'] == plugin['name'])
        self.assertEqual(entry['source'], './')
        self.assertEqual(entry['version'], version)
        for name in NAMES:
            head = (ROOT / 'skills' / name / 'SKILL.md').read_text(encoding='utf-8').split('---')[1]
            self.assertIn('name: ' + name, head)


if __name__ == '__main__':
    unittest.main()
