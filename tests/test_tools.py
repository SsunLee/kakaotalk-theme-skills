"""Offline CLI integration tests; fixtures are synthetic, not Kakao samples."""
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / 'skills/kakaotalk-theme-builder/scripts/theme_tools.py'
PUBLISHER = ROOT / 'skills/kakaotalk-theme-publisher/scripts/release_tools.py'


def cli(script, *args, ok=True, env=None):
    result = subprocess.run([sys.executable, str(script), *map(str, args)],
                            stdin=subprocess.DEVNULL, capture_output=True,
                            encoding='utf-8', errors='replace', env=env,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    if ok and result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    if not ok and not result.returncode:
        raise AssertionError('Expected failure: ' + result.stdout)
    return result


def png(width=320, height=320):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    raw = (b'\x00' + b'\x80\x80\x80' * width) * height
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


class ToolsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='theme-skills-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.project = self.base / 'project with spaces'
        cli(BUILDER, 'init', '--project', self.project, '--slug', 'sample-theme',
            '--name', '테스트 테마', '--package', 'org.example.theme')
        self.data = json.loads((self.project / 'theme.json').read_text(encoding='utf-8'))
        self.data.update(author='Test Author', description='Synthetic test fixture')
        self.persist()
        (self.project / 'ios/KakaoTalkTheme.css').write_text("ManifestStyle { image: 'sample.png'; }", encoding='utf-8')
        (self.project / 'ios/Images/sample@2x.png').write_bytes(png())
        cli(BUILDER, 'pack-ios', '--project', self.project)
        with zipfile.ZipFile(self.project / self.data['files']['android'], 'w') as archive:
            archive.writestr('AndroidManifest.xml', b'synthetic')
            archive.writestr('classes.dex', b'synthetic')
        for path in self.data['previews']:
            (self.project / path).write_bytes(png())

    def persist(self):
        save(self.project / 'theme.json', self.data)

    def package(self):
        cli(BUILDER, 'package', '--project', self.project)
        return self.project / 'bundle-manifest.json'

    def prepare(self, platform='postype', price=0, visibility='subscribers'):
        manifest = self.project / 'bundle-manifest.json'
        if not manifest.exists():
            self.package()
        folder = self.base / ('release-' + platform)
        cli(PUBLISHER, 'prepare', '--bundle-manifest', manifest, '--out', folder,
            '--platform', platform, '--account', 'example-account', '--price', price,
            '--visibility', visibility)
        return folder

    def bind_attempt(self, folder):
        cli(PUBLISHER, 'bind', '--release', folder, '--remote-id', 'example-123',
            '--url', 'https://example.com/draft/123')
        cli(PUBLISHER, 'attempt', '--release', folder, '--authorization', 'Test upload instruction')

    def evidence(self, folder, outcome='published', **overrides):
        listing = json.loads((folder / 'listing.json').read_text(encoding='utf-8'))
        value = {k: listing[k] for k in ['platform', 'account', 'price', 'visibility']}
        value.update(remote_id='example-123', outcome=outcome, url='https://example.com/item/123',
                     observed_at='2026-01-01T00:00:00Z', note='Synthetic observation for test')
        value.update(overrides)
        path = self.base / 'evidence.json'
        save(path, value)
        return path

    def test_package_contents_and_honest_checks(self):
        report = json.loads(cli(BUILDER, 'check', '--project', self.project).stdout)
        self.assertEqual(report['checks']['apk_signature'], 'not_checked_by_this_command')
        manifest = json.loads(self.package().read_text(encoding='utf-8'))
        with zipfile.ZipFile(self.project / manifest['bundle']['path']) as archive:
            self.assertEqual(set(archive.namelist()), set(self.data['files'].values()) | set(self.data['guides']))
        self.assertFalse(manifest['review']['kakaotalk_tested'])
        cli(BUILDER, 'package', '--project', self.project, ok=False)

    def test_init_and_ios_no_overwrite(self):
        cli(BUILDER, 'init', '--project', self.project, '--slug', 'other',
            '--name', 'Other', '--package', 'org.example.other', ok=False)
        cli(BUILDER, 'pack-ios', '--project', self.project, ok=False)

    def test_missing_css_reference_is_rejected(self):
        (self.project / self.data['files']['ios']).unlink()
        (self.project / 'ios/Images/sample@2x.png').unlink()
        cli(BUILDER, 'pack-ios', '--project', self.project, ok=False)
        self.assertFalse((self.project / self.data['files']['ios']).exists())

    def test_path_traversal_is_rejected(self):
        self.data['files']['android'] = '../escape.apk'
        self.persist()
        cli(BUILDER, 'check', '--project', self.project, ok=False)

    def test_archive_traversal_is_rejected(self):
        with zipfile.ZipFile(self.project / self.data['files']['android'], 'a') as archive:
            archive.writestr('../secret.txt', 'invalid')
        cli(BUILDER, 'check', '--project', self.project, ok=False)

    def test_corrupt_archive_is_rejected(self):
        (self.project / self.data['files']['android']).write_bytes(b'not an apk')
        cli(BUILDER, 'check', '--project', self.project, ok=False)

    def test_missing_or_small_previews_are_rejected(self):
        preview = self.project / self.data['previews'][0]
        preview.write_bytes(png(10, 10))
        cli(BUILDER, 'check', '--project', self.project, ok=False)
        preview.unlink()
        cli(BUILDER, 'check', '--project', self.project, ok=False)

    def test_platform_assets_and_prices(self):
        for platform, price, visibility, role in [('littly', 1000, 'buyers', 'bundle'),
                                                    ('postype', 0, 'subscribers', 'ios'),
                                                    ('onestore', 1000, 'buyers', 'android')]:
            folder = self.prepare(platform, price, visibility)
            listing = json.loads((folder / 'listing.json').read_text(encoding='utf-8'))
            self.assertEqual((listing['price'], listing['visibility']), (price, visibility))
            self.assertIn(role, {x['role'] for x in listing['assets']})
            self.assertEqual(json.loads((folder / 'state.json').read_text())['status'], 'prepared')
        cli(PUBLISHER, 'prepare', '--bundle-manifest', self.project / 'bundle-manifest.json',
            '--out', self.base / 'bad', '--platform', 'postype', '--account', 'example',
            '--price', 1000, '--visibility', 'subscribers', ok=False)

    def test_changed_source_hash_is_rejected(self):
        self.package()
        (self.project / self.data['files']['ios']).write_bytes(b'changed')
        cli(PUBLISHER, 'prepare', '--bundle-manifest', self.project / 'bundle-manifest.json',
            '--out', self.base / 'release', '--platform', 'postype', '--account', 'example',
            '--price', 0, '--visibility', 'subscribers', ok=False)

    def test_duplicate_attempt_and_confirmation(self):
        folder = self.prepare()
        self.bind_attempt(folder)
        cli(PUBLISHER, 'attempt', '--release', folder, '--authorization', 'Repeat', ok=False)
        cli(PUBLISHER, 'confirm', '--release', folder, '--evidence', self.evidence(folder))
        state = json.loads((folder / 'state.json').read_text())
        self.assertEqual(state['status'], 'published')
        self.assertEqual(len(state['attempts']), 1)
        cli(PUBLISHER, 'attempt', '--release', folder, '--authorization', 'Repeat', ok=False)

    def test_wrong_evidence_and_changed_listing_rejected(self):
        folder = self.prepare()
        self.bind_attempt(folder)
        cli(PUBLISHER, 'confirm', '--release', folder, '--evidence', self.evidence(folder, price=1000), ok=False)
        listing = json.loads((folder / 'listing.json').read_text(encoding='utf-8'))
        listing['account'] = 'other'
        save(folder / 'listing.json', listing)
        cli(PUBLISHER, 'confirm', '--release', folder, '--evidence', self.evidence(folder), ok=False)

    def test_reconcile_requires_evidence_before_retry(self):
        folder = self.prepare()
        self.bind_attempt(folder)
        cli(PUBLISHER, 'reconcile', '--release', folder, '--outcome', 'not_submitted',
            '--evidence', self.evidence(folder, 'not_submitted'))
        cli(PUBLISHER, 'attempt', '--release', folder, '--authorization', 'Retry after observed non-submission')
        state = json.loads((folder / 'state.json').read_text())
        self.assertEqual(len(state['attempts']), 2)
        self.assertEqual(state['attempts'][0]['outcome'], 'not_submitted')

    def test_onestore_means_review_requested(self):
        folder = self.prepare('onestore', 1000, 'buyers')
        self.bind_attempt(folder)
        cli(PUBLISHER, 'confirm', '--release', folder, '--evidence', self.evidence(folder, 'published'), ok=False)
        cli(PUBLISHER, 'confirm', '--release', folder, '--evidence', self.evidence(folder, 'review_requested'))
        self.assertEqual(json.loads((folder / 'state.json').read_text())['status'], 'review_requested')

    def test_changed_upload_blocks_submission(self):
        folder = self.prepare()
        listing = json.loads((folder / 'listing.json').read_text(encoding='utf-8'))
        (folder / listing['assets'][0]['path']).write_bytes(b'changed')
        cli(PUBLISHER, 'bind', '--release', folder, '--remote-id', 'example-123',
            '--url', 'https://example.com/draft/123', ok=False)

    def test_release_lock_blocks_concurrent_mutation(self):
        folder = self.prepare()
        (folder / '.release.lock').write_text('123')
        cli(PUBLISHER, 'bind', '--release', folder, '--remote-id', 'example-123',
            '--url', 'https://example.com/draft/123', ok=False)
        self.assertTrue((folder / '.release.lock').exists())


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='theme-install-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.target = self.base / 'skills'
        self.script = ROOT / 'install.py'

    def test_dry_run_install_check_and_repeat(self):
        cli(self.script, '--dest', self.target, '--dry-run')
        self.assertFalse(self.target.exists())
        cli(self.script, '--dest', self.target)
        cli(self.script, '--dest', self.target, '--check')
        cli(self.script, '--dest', self.target)
        cli(self.script, '--dest', self.target, '--update')
        cli(self.script, '--dest', self.target, '--check')
        self.assertEqual(len(list((self.base / '.kakaotalk-theme-skill-backups').iterdir())), 2)

    def test_modified_install_preserved(self):
        cli(self.script, '--dest', self.target)
        file = self.target / 'kakaotalk-theme-builder/SKILL.md'
        file.write_text('my custom work', encoding='utf-8')
        cli(self.script, '--dest', self.target, '--update', ok=False)
        cli(self.script, '--dest', self.target, '--check', ok=False)
        self.assertEqual(file.read_text(), 'my custom work')

    def test_unmanaged_folder_preserved(self):
        existing = self.target / 'kakaotalk-theme-builder'
        existing.mkdir(parents=True)
        (existing / 'SKILL.md').write_text('custom')
        cli(self.script, '--dest', self.target, '--update', ok=False)
        self.assertFalse((self.target / 'kakaotalk-theme-publisher').exists())

    def test_project_and_selected_skill(self):
        cli(self.script, '--target', 'claude', '--project', self.base,
            '--skills', 'kakaotalk-theme-builder')
        self.assertTrue((self.base / '.claude/skills/kakaotalk-theme-builder/SKILL.md').is_file())
        self.assertFalse((self.base / '.claude/skills/kakaotalk-theme-publisher').exists())


if __name__ == '__main__':
    unittest.main()
