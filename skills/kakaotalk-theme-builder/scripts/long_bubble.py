#!/usr/bin/env python3
"""Long-body ("길어지는 스타일") chat bubble helper. Python 3.10+, requires Pillow.

The bubble art is one character whose plain body segment stretches while the
head, tail, ears and paws stay fixed. One @3x master per variant is sliced into
iOS @3x/@2x images, Android xxhdpi nine-patches, a CSS snippet and a preview.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:  # pragma: no cover
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.write(
        'PILLOW_MISSING: 길어지는 스타일 말풍선 도구에는 이미지 처리 라이브러리 Pillow가 필요합니다.\n'
        '설치 명령: "' + sys.executable + '" -m pip install --user Pillow\n'
        'Pillow is required. Install it with the command above, then run this tool again.\n')
    sys.exit(3)

VARIANTS = ['send01', 'send02', 'receive01', 'receive02']
IOS_NAME = {'send01': 'chatroomBubbleSend01', 'send02': 'chatroomBubbleSend02',
            'receive01': 'chatroomBubbleReceive01', 'receive02': 'chatroomBubbleReceive02'}
AND_NAME = {'send01': 'theme_chatroom_bubble_me_01_image', 'send02': 'theme_chatroom_bubble_me_02_image',
            'receive01': 'theme_chatroom_bubble_you_01_image', 'receive02': 'theme_chatroom_bubble_you_02_image'}
SCENES = [['응'], ['네!'], ['오늘도 같이 놀자'], ['작은 친구들과 함께하는 하루'],
          ['편지를 가져왔어', '반가워'], ['오', '오', '오', '오', '오']]
FONTS = ['C:/Windows/Fonts/malgun.ttf', '/System/Library/Fonts/AppleSDGothicNeo.ttc',
         '/usr/share/fonts/truetype/nanum/NanumGothic.ttf', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']


def fail(msg):
    sys.exit(f'error: {msg}')


def load_spec(path):
    spec_path = Path(path).resolve()
    spec = json.loads(spec_path.read_text(encoding='utf-8'))
    if spec.get('scale', 3) != 3:
        fail('master art must be drawn at @3x (scale 3)')
    return spec_path.parent, spec


def variant_spec(base, spec, key):
    """Return (image, stretch, content, auto_note) for a variant, mirroring receive from send if asked."""
    images = spec.get('images', {})
    per = spec.get('per_image', {})
    mirror = spec.get('mirror_receive', False) and key.startswith('receive') and key not in images
    src_key = key.replace('receive', 'send') if mirror else key
    if src_key not in images:
        fail(f'images.{src_key} is missing')
    img = Image.open(base / images[src_key]).convert('RGBA')
    conf = {**{'stretch': spec.get('stretch'), 'content': spec.get('content')}, **per.get(src_key, {})}
    st, ct = conf['stretch'], dict(conf['content'])
    (x0, x1), (y0, y1) = st['x'], st['y']
    if mirror:
        w = img.width
        img = ImageOps.mirror(img)
        x0, x1 = w - 1 - x1, w - 1 - x0
        ct['left'], ct['right'] = ct['right'], ct['left']
    if key in per and mirror:
        fail(f'per_image.{key} cannot be used with a mirrored receive image; list images.{key} explicitly')
    return img, (x0, x1), (y0, y1), ct, mirror


def cap_point(lo, hi, size, axis):
    """Smallest pt cap whose 1pt stretch slice lies inside [lo, hi] (inclusive, @3x px)."""
    cap = math.ceil(lo / 3)
    if cap * 3 + 2 > hi or cap * 3 + 3 > size:
        fail(f'{axis} stretch range {lo}-{hi}px is too narrow; give at least 6px of plain body at @3x')
    return cap


def uniform_warnings(img, xr, yr, name):
    """Stretch slices must be featureless body; detail inside them would smear when stretched."""
    px, out = img.load(), []
    def diff(a, b):
        return max(abs(a[i] - b[i]) for i in range(4))
    bad_x = [x for x in range(xr[0] + 1, xr[1] + 1)
             if max(diff(px[x, y], px[xr[0], y]) for y in range(img.height)) > 24]
    bad_y = [y for y in range(yr[0] + 1, yr[1] + 1)
             if max(diff(px[x, y], px[x, yr[0]]) for x in range(img.width)) > 24]
    if bad_x:
        out.append(f'{name}: columns {bad_x[0]}-{bad_x[-1]} in the horizontal stretch range differ from column {xr[0]} (head/tail/paw detail inside the stretch zone)')
    if bad_y:
        out.append(f'{name}: rows {bad_y[0]}-{bad_y[-1]} in the vertical stretch range differ from row {yr[0]} (ears/paws/head inside the stretch zone)')
    if all(px[xr[0], y][3] == 0 for y in range(img.height)):
        out.append(f'{name}: horizontal stretch column is fully transparent; the bubble would split in two')
    return out


def darken(img, factor):
    r, g, b, a = img.split()
    rgb = Image.merge('RGB', (r, g, b)).point(lambda v: int(v * factor))
    return Image.merge('RGBA', (*rgb.split(), a))


def nine_patch(img, xr, yr, ct):
    w, h = img.size
    out = Image.new('RGBA', (w + 2, h + 2), (0, 0, 0, 0))
    out.paste(img, (1, 1))
    d = ImageDraw.Draw(out)
    black = (0, 0, 0, 255)
    d.line([(xr[0] + 1, 0), (xr[1] + 1, 0)], fill=black)
    d.line([(0, yr[0] + 1), (0, yr[1] + 1)], fill=black)
    d.line([(ct['left'] + 1, h + 1), (w - ct['right'], h + 1)], fill=black)
    d.line([(w + 1, ct['top'] + 1), (w + 1, h - ct['bottom'])], fill=black)
    return out


def build(args):
    base, spec = load_spec(args.spec)
    project = Path(args.project).resolve()
    ios_dir = project / 'ios' / 'Images'
    and_dir = project / 'android' / 'src' / 'main' / 'theme' / 'drawable-xxhdpi'
    qa_dir = project / 'qa'
    for d in (ios_dir, and_dir, qa_dir):
        d.mkdir(parents=True, exist_ok=True)
    report, warnings, css = {'variants': {}}, [], {}
    for key in VARIANTS:
        img, xr, yr, ct, mirrored = variant_spec(base, spec, key)
        w, h = img.size
        if w % 3 or h % 3:
            warnings.append(f'{key}: size {w}x{h} is not divisible by 3; @2x will be rounded')
        if not (ct['left'] <= xr[0] and w - ct['right'] > xr[1] and ct['top'] <= yr[0] and h - ct['bottom'] > yr[1]):
            warnings.append(f'{key}: the stretch range should lie inside the text area so text grows with the body')
        warnings += uniform_warnings(img, xr, yr, key)
        cx, cy = cap_point(*xr, w, 'horizontal'), cap_point(*yr, h, 'vertical')
        sel_key = f'{key}_selected'
        if sel_key in spec.get('images', {}):
            sel = Image.open(base / spec['images'][sel_key]).convert('RGBA')
            if sel.size != img.size:
                fail(f'{sel_key} must match {key} size {img.size}')
            sel_note = 'provided'
        else:
            sel_src = key.replace('receive', 'send') + '_selected'
            if mirrored and sel_src in spec.get('images', {}):
                sel, sel_note = ImageOps.mirror(Image.open(base / spec['images'][sel_src]).convert('RGBA')), 'mirrored'
            else:
                sel, sel_note = darken(img, spec.get('selected_darken', 0.85)), 'auto-darkened'
        name = IOS_NAME[key]
        for suffix, im in (('', img), ('Selected', sel)):
            im.save(ios_dir / f'{name}{suffix}@3x.png')
            im.resize((round(w * 2 / 3), round(h * 2 / 3)), Image.LANCZOS).save(ios_dir / f'{name}{suffix}@2x.png')
        nine_patch(img, xr, yr, ct).save(and_dir / f'{AND_NAME[key]}.9.png')
        inset = [round(ct[k] / 3) for k in ('top', 'left', 'bottom', 'right')]
        css[key] = {'cap': (cx, cy), 'inset': inset}
        report['variants'][key] = {'size_px@3x': [w, h], 'stretch_x': list(xr), 'stretch_y': list(yr),
                                   'content_px@3x': ct, 'ios_cap_pt': [cx, cy], 'ios_edgeinsets_pt': inset,
                                   'receive_mirrored_from_send': mirrored, 'selected': sel_note}
    snippet = css_snippet(css)
    (qa_dir / 'long-bubble-css.txt').write_text(snippet, encoding='utf-8')
    report['warnings'] = warnings
    report['note'] = 'Structural slicing only. Visual fit and real KakaoTalk rendering must be checked separately.'
    (qa_dir / 'long-bubble-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.apply_css:
        apply_css(project, css)
    print(snippet)
    for w_ in warnings:
        print('warning:', w_)
    print(f'wrote {ios_dir}, {and_dir}, {qa_dir / "long-bubble-report.json"}')
    return 1 if warnings and args.strict else 0


def css_lines(css, side):
    one, two = css[f'{side}01'], css[f'{side}02']
    name = 'Send' if side == 'send' else 'Receive'
    c1, c2 = '{}px {}px'.format(*one['cap']), '{}px {}px'.format(*two['cap'])
    return {
        '-ios-background-image': f"'chatroomBubble{name}01.png' {c1}",
        '-ios-selected-background-image': f"'chatroomBubble{name}01Selected.png' {c1}",
        '-ios-group-background-image': f"'chatroomBubble{name}02.png' {c2}",
        '-ios-group-selected-background-image': f"'chatroomBubble{name}02Selected.png' {c2}",
        '-ios-title-edgeinsets': '{}px {}px {}px {}px'.format(*one['inset']),
        '-ios-group-title-edgeinsets': '{}px {}px {}px {}px'.format(*two['inset']),
    }


def css_snippet(css):
    out = []
    for side, block in (('send', 'MessageCellStyle-Send'), ('receive', 'MessageCellStyle-Receive')):
        out.append(f'{block}\n{{')
        out += [f'    {k}: {v};' for k, v in css_lines(css, side).items()]
        out.append('    /* keep the existing text-color lines; edgeinsets are top, left, bottom, right */\n}\n')
    return '\n'.join(out)


def apply_css(project, css):
    files = [p for p in (project / 'ios' / 'KakaoTalkTheme.css', project / 'ios' / 'KakaoTalk.css') if p.exists()]
    if len(files) != 1:
        fail('--apply-css needs exactly one ios/KakaoTalkTheme.css or ios/KakaoTalk.css')
    path = files[0]
    text = path.read_text(encoding='utf-8')
    for side, block in (('send', 'MessageCellStyle-Send'), ('receive', 'MessageCellStyle-Receive')):
        m = re.search(rf'{block}\s*\{{(.*?)\}}', text, re.S)
        if not m:
            fail(f'{block} block not found in {path.name}')
        body = m.group(1)
        for prop, value in css_lines(css, side).items():
            pat = rf'(^[ \t]*){re.escape(prop)}\s*:[^;]*;'
            if re.search(pat, body, re.M):
                body = re.sub(pat, lambda mm: f'{mm.group(1)}{prop}: {value};', body, count=1, flags=re.M)
            else:
                body = f'\n    {prop}: {value};' + body
        text = text[:m.start(1)] + body + text[m.end(1):]
    path.write_text(text, encoding='utf-8')
    print(f'updated {path}')


def stretch_to(img, xr, yr, width, height):
    """Simulate 3x3 slicing: fixed corners, stretch the middle band to reach width/height."""
    w, h = img.size
    xs = [0, xr[0], xr[1] + 1, w]
    ys = [0, yr[0], yr[1] + 1, h]
    tw = [xs[1], max(1, width - xs[1] - (w - xs[2])), w - xs[2]]
    th = [ys[1], max(1, height - ys[1] - (h - ys[2])), h - ys[2]]
    out = Image.new('RGBA', (sum(tw), sum(th)), (0, 0, 0, 0))
    oy = 0
    for j in range(3):
        ox = 0
        for i in range(3):
            if tw[i] and th[j]:
                tile = img.crop((xs[i], ys[j], xs[i + 1], ys[j + 1])).resize((tw[i], th[j]), Image.NEAREST)
                out.paste(tile, (ox, oy))
            ox += tw[i]
        oy += th[j]
    return out


def find_font(size):
    for f in FONTS:
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def preview(args):
    base, spec = load_spec(args.spec)
    out_path = Path(args.out).resolve()
    colors = spec.get('text_color', {'send': '#222222', 'receive': '#222222'})
    bg = spec.get('preview_background', '#F2F2F2')
    rows = []
    for scale_name, pt in (('기본', 15), ('큰 글씨', 21)):
        font = find_font(pt * 3)
        for lines in SCENES:
            for side in ('send', 'receive'):
                key = f'{side}01'
                img, xr, yr, ct, _ = variant_spec(base, spec, key)
                line_h = round(pt * 3 * 1.35)
                tw = max(math.ceil(font.getlength(t)) for t in lines)
                th = line_h * len(lines)
                bw = max(img.width - (xr[1] - xr[0]), tw + ct['left'] + ct['right'])
                bh = max(img.height - (yr[1] - yr[0]), th + ct['top'] + ct['bottom'])
                bub = stretch_to(img, xr, yr, bw, bh)
                d = ImageDraw.Draw(bub)
                box_w = bub.width - ct['left'] - ct['right']
                box_h = bub.height - ct['top'] - ct['bottom']
                y = ct['top'] + (box_h - th) // 2
                for t in lines:
                    d.text((ct['left'] + (box_w - font.getlength(t)) / 2, y + (line_h - pt * 3) / 2 - 4), t,
                           font=font, fill=colors.get(side, '#222222'))
                    y += line_h
                if args.guides:
                    d.rectangle([ct['left'], ct['top'], bub.width - ct['right'] - 1, bub.height - ct['bottom'] - 1],
                                outline=(255, 0, 128, 200))
                rows.append((side, bub, scale_name))
    width, gap = 1170, 36
    height = sum(b.height + gap for _, b, _ in rows) + gap
    sheet = Image.new('RGBA', (width, height), bg)
    y = gap
    for side, bub, _ in rows:
        x = width - gap - bub.width if side == 'send' else gap
        sheet.alpha_composite(bub, (max(0, x), y))
        y += bub.height + gap
    sheet = sheet.resize((width // 3 * 2 // 2, height // 3 * 2 // 2), Image.LANCZOS) if args.small else sheet
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert('RGB').save(out_path)
    print(f'wrote {out_path} (simulated slicing, not a KakaoTalk capture)')
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    b = sub.add_parser('build', help='slice masters into iOS/Android bubble resources')
    b.add_argument('--spec', required=True)
    b.add_argument('--project', required=True)
    b.add_argument('--apply-css', action='store_true', help='update bubble lines in the project CSS')
    b.add_argument('--strict', action='store_true', help='exit 1 when warnings exist')
    v = sub.add_parser('preview', help='render the required comparison scenes')
    v.add_argument('--spec', required=True)
    v.add_argument('--out', required=True)
    v.add_argument('--guides', action='store_true', help='outline the text area')
    v.add_argument('--small', action='store_true', help='downscale for quick viewing')
    args = p.parse_args()
    return build(args) if args.command == 'build' else preview(args)


if __name__ == '__main__':
    sys.exit(main())
