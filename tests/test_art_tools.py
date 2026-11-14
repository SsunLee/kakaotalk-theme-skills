"""Offline tests for the Pillow-based art helpers (long bubbles, cute backgrounds).

Fixtures are drawn here; nothing comes from Kakao samples or real theme products.
Skipped when Pillow is not installed, because only these two helpers need it.
"""
import json
from pathlib import Path
import tempfile
import unittest

from test_tools import ROOT, cli

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    Image = None

SCRIPTS = ROOT / 'skills/kakaotalk-theme-builder/scripts'
LONG = SCRIPTS / 'long_bubble.py'
BG = SCRIPTS / 'background_pattern.py'
DARK = (25, 25, 25, 255)


def dims(path):
    with Image.open(path) as im:
        return im.size


def long_body(path, eyes_at=(28, 54)):
    """A plain long-body character: head left, tail right, paws below, plain middle body."""
    im = Image.new('RGBA', (216, 138), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(10, 30), (18, 4), (36, 24)], fill=DARK)
    d.rounded_rectangle([6, 24, 196, 120], radius=30, fill=DARK)
    for cx in eyes_at:
        d.ellipse([cx - 9, 44, cx + 9, 62], fill=(255, 255, 255, 255))
    d.ellipse([186, 96, 214, 118], fill=DARK)
    for x in (24, 60, 150, 176):
        d.ellipse([x - 10, 112, x + 10, 134], fill=DARK)
    im.save(path)


@unittest.skipIf(Image is None, 'Pillow is not installed')
class LongBubbleTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='long-bubble-test-')
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        (self.base / 'art').mkdir()
        long_body(self.base / 'art/send01@3x.png')
        long_body(self.base / 'art/send02@3x.png')
        self.spec = self.base / 'long-bubble.json'
        self.write_spec(x=[100, 120])
        self.project = self.base / 'project with spaces'

    def write_spec(self, x):
        self.spec.write_text(json.dumps({
            'scale': 3, 'stretch': {'x': x, 'y': [78, 90]},
            'content': {'left': 78, 'top': 36, 'right': 33, 'bottom': 30},
            'mirror_receive': True,
            'images': {'send01': 'art/send01@3x.png', 'send02': 'art/send02@3x.png'}}), encoding='utf-8')

    def test_build_outputs_ninepatch_and_css(self):
        out = cli(LONG, 'build', '--spec', self.spec, '--project', self.project, '--strict').stdout
        self.assertIn("'chatroomBubbleSend01.png' 34px 26px", out)
        self.assertIn('-ios-title-edgeinsets: 12px 26px 10px 11px', out)
        images = self.project / 'ios/Images'
        for name in ['Send01', 'Send02', 'Receive01', 'Receive02']:
            for suffix in ['', 'Selected']:
                self.assertEqual(dims(images / f'chatroomBubble{name}{suffix}@3x.png'), (216, 138))
                self.assertEqual(dims(images / f'chatroomBubble{name}{suffix}@2x.png'), (144, 92))
        with Image.open(self.project / 'android/src/main/theme/drawable-xxhdpi/theme_chatroom_bubble_me_01_image.9.png') as raw:
            nine = raw.convert('RGBA')
        self.assertEqual(nine.size, (218, 140))
        top = [x for x in range(nine.width) if nine.getpixel((x, 0)) == (0, 0, 0, 255)]
        self.assertEqual((top[0], top[-1]), (101, 121))
        report = json.loads((self.project / 'qa/long-bubble-report.json').read_text(encoding='utf-8'))
        self.assertTrue(report['variants']['receive01']['receive_mirrored_from_send'])
        self.assertEqual(report['variants']['receive01']['stretch_x'], [95, 115])
        self.assertEqual(report['warnings'], [])

    def test_detail_inside_stretch_zone_is_reported(self):
        self.write_spec(x=[40, 120])
        result = cli(LONG, 'build', '--spec', self.spec, '--project', self.project, '--strict', ok=False)
        self.assertIn('detail inside the stretch zone', result.stdout)

    def test_too_narrow_stretch_is_rejected(self):
        self.write_spec(x=[100, 103])
        result = cli(LONG, 'build', '--spec', self.spec, '--project', self.project, ok=False)
        self.assertIn('too narrow', result.stdout + result.stderr)

    def test_apply_css_keeps_text_colors(self):
        css = self.project / 'ios/KakaoTalkTheme.css'
        css.parent.mkdir(parents=True)
        css.write_text("MessageCellStyle-Send\n{\n    -ios-background-image: 'old.png' 1px 1px;\n    -ios-text-color: #ABCDEF;\n}\n"
                       "MessageCellStyle-Receive\n{\n    -ios-text-color: #123456;\n}\n", encoding='utf-8')
        cli(LONG, 'build', '--spec', self.spec, '--project', self.project, '--apply-css')
        text = css.read_text(encoding='utf-8')
        self.assertNotIn('old.png', text)
        self.assertIn("-ios-group-background-image: 'chatroomBubbleReceive02.png' 32px 26px;", text)
        self.assertIn('#ABCDEF', text)
        self.assertIn('#123456', text)

    def test_preview_renders(self):
        out = self.base / 'qa/preview.png'
        cli(LONG, 'preview', '--spec', self.spec, '--out', out, '--guides')
        self.assertGreater(dims(out)[1], 1000)


@unittest.skipIf(Image is None, 'Pillow is not installed')
class BackgroundTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='background-test-')
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.project = self.base / 'project'
        long_body(self.base / 'face.png')

    def run_spec(self, spec, *extra, ok=True):
        path = self.base / 'background.json'
        path.write_text(json.dumps(spec), encoding='utf-8')
        return cli(BG, '--spec', path, '--project', self.project, *extra, ok=ok)

    def test_every_preset_writes_all_targets(self):
        presets = cli(BG, '--list-presets').stdout.split()
        self.assertIn('dreamy-sky', presets)
        self.assertGreaterEqual(len(presets), 8)
        self.run_spec({'chatroom': {'preset': 'dreamy-sky'}, 'main': {'preset': 'candy-hearts'},
                       'passcode': {'preset': 'starry-night'}})
        sizes = {'ios/Images/chatroomBgImage@3x.png': (1125, 2250), 'ios/Images/mainBgImage@2x.png': (750, 1500),
                 'android/src/main/theme/drawable-xxhdpi/theme_passcode_background_image.png': (1440, 1440),
                 'android/src/main/theme/drawable-sw600dp-xxhdpi/theme_chatroom_background_image.png': (1440, 2880)}
        for rel, size in sizes.items():
            self.assertEqual(dims(self.project / rel), size)
        report = json.loads((self.project / 'qa/background-report.json').read_text(encoding='utf-8'))
        self.assertEqual(report['warnings'], [])

    def test_catalog_contains_every_preset(self):
        out = self.base / 'catalog.png'
        cli(BG, '--catalog', out)
        self.assertGreater(dims(out)[0], 1000)

    def test_low_contrast_text_warns(self):
        out = self.run_spec({'chatroom': {'preset': 'pastel-polka', 'text_color': '#FFFFFF'}}, '--preview-only').stdout
        self.assertIn('warning: chatroom', out)
        self.assertFalse((self.project / 'ios').exists())

    def test_character_stickers_and_legacy_pattern(self):
        self.run_spec({'chatroom': {'layers': [
            {'type': 'gradient', 'colors': ['#FFE4EE', '#DDEBFF']},
            {'type': 'scatter', 'seed': 1, 'spacing': 40, 'shapes': [
                {'shape': 'image:face.png', 'size': [7, 10], 'opacity': 0.2},
                {'shape': 'heart', 'colors': ['#FFB3C7'], 'size': [3, 5]}]}]},
            'main': {'pattern': 'gingham', 'color': '#FFFFFF', 'color2': '#FFD9E2', 'cell': 14}}, '--preview-only')
        self.assertTrue((self.project / 'qa/background-chatroom.png').is_file())
        self.assertTrue((self.project / 'qa/background-main.png').is_file())

    def test_unknown_preset_is_rejected(self):
        result = self.run_spec({'chatroom': {'preset': 'not-a-preset'}}, ok=False)
        self.assertIn('preset must be one of', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
