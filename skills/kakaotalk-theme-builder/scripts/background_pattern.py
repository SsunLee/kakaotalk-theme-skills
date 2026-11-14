#!/usr/bin/env python3
"""Cute patterned / illustrated backgrounds for KakaoTalk themes. Python 3.10+, requires Pillow.

KakaoTalk crops background images instead of tiling them, so every background is
rendered at full size per target (chat room, main tabs, passcode). A background is a
stack of layers (gradient, gingham, scattered hearts/stars/sparkles/flowers, ...),
or one of the ready-made cute presets. Sizes in the spec are pt.
"""
import argparse
import copy
import json
import math
import random
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:  # pragma: no cover
    sys.exit('Pillow is required: python -m pip install Pillow')

TARGETS = {
    'chatroom': [('ios/Images/chatroomBgImage@3x.png', 1125, 2250), ('ios/Images/chatroomBgImage@2x.png', 750, 1500),
                 ('android/src/main/theme/drawable-xxhdpi/theme_chatroom_background_image.png', 1440, 2880),
                 ('android/src/main/theme/drawable-sw600dp-xxhdpi/theme_chatroom_background_image.png', 1440, 2880)],
    'main': [('ios/Images/mainBgImage@3x.png', 1125, 2250), ('ios/Images/mainBgImage@2x.png', 750, 1500),
             ('android/src/main/theme/drawable-xxhdpi/theme_background_image.png', 1440, 2880),
             ('android/src/main/theme/drawable-sw600dp-xxhdpi/theme_background_image.png', 1440, 2880)],
    'passcode': [('ios/Images/passcodeBgImage@3x.png', 1125, 2250), ('ios/Images/passcodeBgImage@2x.png', 750, 1500),
                 ('android/src/main/theme/drawable-xxhdpi/theme_passcode_background_image.png', 1440, 1440),
                 ('android/src/main/theme/drawable-sw600dp-xxhdpi/theme_passcode_background_image.png', 1440, 1440)],
}
LAYERS = ['solid', 'gradient', 'checker', 'gingham', 'dots', 'grid', 'stripes', 'scatter', 'motif', 'image']
SHAPES = ['dot', 'ring', 'heart', 'star', 'sparkle', 'flower', 'cloud', 'moon']

# Cute presets. Colors are soft pastels; text_color is the date/name/time color checked for contrast.
PRESETS = {
    'pastel-polka': {'text_color': '#7A6A64', 'layers': [
        {'type': 'solid', 'color': '#FFF8F1'},
        {'type': 'dots', 'colors': ['#FFC9D6', '#FFE3A3', '#C3E4FF', '#D3EFCB'], 'cell': 28, 'dot': 4.6}]},
    'dreamy-sky': {'text_color': '#6E6A8A', 'layers': [
        {'type': 'gradient', 'colors': ['#FFE4EE', '#ECE3FF', '#DDEBFF']},
        {'type': 'scatter', 'seed': 7, 'spacing': 92, 'density': 0.55, 'shapes': [
            {'shape': 'cloud', 'colors': ['#FFFFFF'], 'size': [16, 26], 'weight': 2, 'opacity': 0.85}]},
        {'type': 'scatter', 'seed': 11, 'spacing': 26, 'shapes': [
            {'shape': 'sparkle', 'colors': ['#FFFFFF', '#FFF2B3'], 'size': [3, 6], 'weight': 3},
            {'shape': 'star', 'colors': ['#FFE79A', '#FFD1E0'], 'size': [2.5, 4.5], 'weight': 2},
            {'shape': 'dot', 'colors': ['#FFFFFF'], 'size': [0.8, 1.6], 'weight': 3}]}]},
    'candy-hearts': {'text_color': '#8A5E6B', 'layers': [
        {'type': 'solid', 'color': '#FFF1F5'},
        {'type': 'scatter', 'seed': 3, 'spacing': 30, 'shapes': [
            {'shape': 'heart', 'colors': ['#FFB3C7', '#FF9BB4', '#FFD3DE'], 'size': [4, 7.5], 'weight': 4, 'tilt': 25},
            {'shape': 'dot', 'colors': ['#FFD8B8', '#FFFFFF'], 'size': [1, 1.8], 'weight': 3},
            {'shape': 'sparkle', 'colors': ['#FFC1D1'], 'size': [2.5, 4], 'weight': 1}]}]},
    'flower-meadow': {'text_color': '#5F7357', 'layers': [
        {'type': 'solid', 'color': '#F4FAEC'},
        {'type': 'scatter', 'seed': 5, 'spacing': 30, 'shapes': [
            {'shape': 'flower', 'colors': ['#FFFFFF', '#FFD0DE', '#CFE0FF', '#FFF0A8'], 'center': '#FFD66B', 'size': [5, 8], 'weight': 4},
            {'shape': 'dot', 'colors': ['#CFE7B5', '#FFE3A3'], 'size': [1, 1.8], 'weight': 3}]}]},
    'starry-night': {'text_color': '#F4EEFF', 'layers': [
        {'type': 'gradient', 'colors': ['#2E3166', '#4B4384', '#6B5A9E']},
        {'type': 'scatter', 'seed': 9, 'spacing': 24, 'shapes': [
            {'shape': 'star', 'colors': ['#FFE99A', '#FFF6CF'], 'size': [2.5, 5], 'weight': 3},
            {'shape': 'sparkle', 'colors': ['#FFFFFF'], 'size': [2.5, 5], 'weight': 2},
            {'shape': 'dot', 'colors': ['#FFFFFF', '#CFC4FF'], 'size': [0.6, 1.3], 'weight': 5}]},
        {'type': 'scatter', 'seed': 2, 'spacing': 180, 'density': 0.3, 'shapes': [
            {'shape': 'moon', 'colors': ['#FFF0B5'], 'size': [10, 14], 'weight': 1}]}]},
    'picnic-hearts': {'text_color': '#8A5E6B', 'layers': [
        {'type': 'gingham', 'color': '#FFFFFF', 'color2': '#FFD9E2', 'cell': 14},
        {'type': 'scatter', 'seed': 4, 'spacing': 46, 'shapes': [
            {'shape': 'heart', 'colors': ['#FF8FAB', '#FFFFFF'], 'size': [4.5, 6.5], 'weight': 1, 'tilt': 15}]}]},
    'storybook-confetti': {'text_color': '#76665A', 'layers': [
        {'type': 'solid', 'color': '#FFFAF0'},
        {'type': 'scatter', 'seed': 12, 'spacing': 30, 'shapes': [
            {'shape': 'dot', 'colors': ['#F7B9C4', '#A9D6F5', '#F9DB8B', '#BFE3B4'], 'size': [2, 3.6], 'weight': 5},
            {'shape': 'star', 'colors': ['#F9DB8B'], 'size': [4, 6], 'weight': 1},
            {'shape': 'heart', 'colors': ['#F7B9C4'], 'size': [4, 6], 'weight': 1, 'tilt': 30},
            {'shape': 'ring', 'colors': ['#A9D6F5', '#BFE3B4'], 'size': [2.8, 4.2], 'weight': 1}]}]},
    'cream-check-sparkle': {'text_color': '#7C6650', 'layers': [
        {'type': 'checker', 'color': '#FFF9F0', 'color2': '#F8ECDB', 'cell': 20},
        {'type': 'scatter', 'seed': 6, 'spacing': 40, 'shapes': [
            {'shape': 'sparkle', 'colors': ['#E2B985', '#FFFFFF'], 'size': [4, 7], 'weight': 1}]}]},
}


def rgba(c, opacity=1.0):
    c = c.lstrip('#')
    if len(c) == 6:
        c += 'ff'
    v = [int(c[i:i + 2], 16) for i in (0, 2, 4, 6)]
    v[3] = round(v[3] * opacity)
    return tuple(v)


def mix(a, b, t):
    return tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(4))


# ---------- shapes (drawn on a supersampled layer) ----------

def poly_star(cx, cy, r, points, inner, rot):
    out = []
    for i in range(points * 2):
        rr = r if i % 2 == 0 else r * inner
        a = rot + math.pi * i / points - math.pi / 2
        out.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return out


def draw_shape(d, kind, cx, cy, r, color, rot, extra):
    if kind == 'dot':
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    elif kind == 'ring':
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=max(1, round(r * 0.38)))
    elif kind == 'heart':
        pts = []
        for i in range(48):
            t = 2 * math.pi * i / 48
            x = 16 * math.sin(t) ** 3
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
            x, y = x * r / 16, y * r / 16
            pts.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)))
        d.polygon(pts, fill=color)
    elif kind == 'star':
        d.polygon(poly_star(cx, cy, r, 5, 0.48, rot), fill=color)
    elif kind == 'sparkle':
        d.polygon(poly_star(cx, cy, r, 4, 0.22, 0), fill=color)
    elif kind == 'flower':
        pr = r * 0.48
        for i in range(5):
            a = rot + 2 * math.pi * i / 5
            px, py = cx + r * 0.52 * math.cos(a), cy + r * 0.52 * math.sin(a)
            d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=color)
        cr = r * 0.32
        d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=extra.get('center', (255, 214, 107, 255)))
    elif kind == 'cloud':
        for dx, dy, s in ((-0.55, 0.12, 0.42), (-0.12, -0.18, 0.55), (0.38, -0.02, 0.45), (0.7, 0.2, 0.3)):
            rr = r * s
            d.ellipse([cx + dx * r - rr, cy + dy * r - rr, cx + dx * r + rr, cy + dy * r + rr], fill=color)
        # flat base as a capsule (rectangle + end circles); Pillow 9 rounded_rectangle fails on capsules
        hr, x0, x1, yc = r * 0.23, cx - r * 0.62, cx + r * 0.72, cy + r * 0.25
        d.rectangle([x0, yc - hr, x1, yc + hr], fill=color)
        for ex in (x0, x1):
            d.ellipse([ex - hr, yc - hr, ex + hr, yc + hr], fill=color)
    elif kind == 'moon':
        # crescent drawn on its own mask so it never cuts holes in neighbouring shapes
        s = max(2, math.ceil(r * 2))
        mask = Image.new('L', (s, s), 0)
        md = ImageDraw.Draw(mask)
        md.ellipse([0, 0, s - 1, s - 1], fill=color[3])
        md.ellipse([s * 0.28, -s * 0.03, s * 1.2, s * 0.9], fill=0)
        layer = d._image
        layer.paste(Image.new('RGBA', (s, s), color), (round(cx - r), round(cy - r)), mask)


def scatter_layer(layer, base, w, h, scale, ss=2):
    """Jittered-grid scatter anchored at the top-center so iOS and Android crops share one layout."""
    canvas = Image.new('RGBA', (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    k = scale * ss
    spacing = layer.get('spacing', 30)
    specs = layer['shapes']
    weights = [s.get('weight', 1) for s in specs]
    rng = random.Random(layer.get('seed', 1))
    half_w_pt, h_pt = 540 / 2, 1000  # fixed field wider than any phone; same seed -> same picture everywhere
    images = {}
    for row in range(int(h_pt // spacing) + 2):
        for col in range(int(-half_w_pt // spacing) - 1, int(half_w_pt // spacing) + 2):
            if rng.random() > layer.get('density', 0.9):
                rng.random(); rng.random(); rng.random(); rng.random(); rng.random()
                continue
            s = rng.choices(specs, weights)[0]
            jx, jy = rng.uniform(-0.38, 0.38), rng.uniform(-0.38, 0.38)
            off = 0.5 if row % 2 else 0
            x_pt = (col + off + jx) * spacing
            y_pt = (row + jy) * spacing
            size = rng.uniform(*s.get('size', [3, 5]))
            color = rgba(rng.choice(s.get('colors', ['#FFFFFF'])), s.get('opacity', 1))
            rot = math.radians(rng.uniform(-s.get('tilt', 180 if s['shape'] == 'star' else 0),
                                           s.get('tilt', 180 if s['shape'] == 'star' else 0)))
            cx, cy = (w / 2 / scale + x_pt) * k, y_pt * k
            if s['shape'].startswith('image:'):
                path = s['shape'][6:]
                if path not in images:
                    images[path] = Image.open(base / path).convert('RGBA')
                px = max(2, round(size * 2 * k))
                im = ImageOps.contain(images[path], (px, px), Image.LANCZOS)
                if s.get('opacity', 1) < 1:
                    im.putalpha(im.getchannel('A').point(lambda a, o=s['opacity']: int(a * o)))
                im = im.rotate(math.degrees(rot), expand=True, resample=Image.BICUBIC)
                canvas.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))
            else:
                if s['shape'] not in SHAPES:
                    sys.exit(f"error: shape must be one of {SHAPES} or image:<path>")
                extra = {'center': rgba(s['center'])} if 'center' in s else {}
                draw_shape(d, s['shape'], cx, cy, size * k, color, rot, extra)
    return canvas.resize((w, h), Image.LANCZOS)


# ---------- layers ----------

def render_layer(img, layer, base, scale):
    w, h = img.size
    kind = layer.get('type', 'solid')
    if kind not in LAYERS:
        sys.exit(f'error: layer type must be one of {LAYERS}')
    op = layer.get('opacity', 1)
    c1, c2 = rgba(layer.get('color', '#FFFFFF')), rgba(layer.get('color2', '#EEEEEE'))
    cell = max(2, round(layer.get('cell', 16) * scale))
    ox = (w // 2) % cell
    top = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(top)
    if kind == 'solid':
        top = Image.new('RGBA', (w, h), c1)
    elif kind == 'gradient':
        stops = [rgba(c) for c in layer.get('colors', ['#FFFFFF', '#EEEEEE'])]
        for y in range(h):
            t = y / max(1, h - 1) * (len(stops) - 1)
            i = min(int(t), len(stops) - 2)
            d.line([(0, y), (w, y)], fill=mix(stops[i], stops[i + 1], t - i))
    elif kind == 'checker':
        top = Image.new('RGBA', (w, h), c1)
        d = ImageDraw.Draw(top)
        for y in range(0, h, cell):
            for x in range(-ox, w, cell):
                if ((x + ox) // cell + y // cell) % 2:
                    d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=c2)
    elif kind == 'gingham':
        top = Image.new('RGBA', (w, h), c1)
        d = ImageDraw.Draw(top)
        band = mix(c1, c2, 0.5)
        for x in range(-ox, w, cell * 2):
            d.rectangle([x, 0, x + cell - 1, h], fill=band)
        for y in range(0, h, cell * 2):
            for x in range(-ox, w, cell * 2):
                d.rectangle([x + cell, y, x + 2 * cell - 1, y + cell - 1], fill=band)
                d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=c2)
    elif kind == 'dots':
        colors = [rgba(c) for c in layer.get('colors', [layer.get('color2', '#EEEEEE')])]
        ss = 2
        big = Image.new('RGBA', (w * ss, h * ss), (0, 0, 0, 0))
        bd = ImageDraw.Draw(big)
        r, step = layer.get('dot', 2.5) * scale * ss, cell * ss
        bx = (w * ss // 2) % step
        for row, y in enumerate(range(step // 2, h * ss + step, step)):
            shift = step // 2 if row % 2 else 0
            for col, x in enumerate(range(-bx + shift - step, w * ss + step, step)):
                bd.ellipse([x - r, y - r, x + r, y + r], fill=colors[(col + row * 2) % len(colors)])
        top = big.resize((w, h), Image.LANCZOS)
    elif kind == 'grid':
        lw = max(1, round(layer.get('line', 0.7) * scale))
        for x in range(-ox, w, cell):
            d.rectangle([x, 0, x + lw - 1, h], fill=c2)
        for y in range(0, h, cell):
            d.rectangle([0, y, w, y + lw - 1], fill=c2)
    elif kind == 'stripes':
        for x in range(-ox, w, cell * 2):
            d.rectangle([x, 0, x + cell - 1, h], fill=c2)
    elif kind == 'scatter':
        top = scatter_layer(layer, base, w, h, scale)
    elif kind == 'motif':
        motif = Image.open(base / layer['motif']).convert('RGBA')
        size = round(layer.get('motif_size', 24) * scale)
        motif = ImageOps.contain(motif, (size, size), Image.LANCZOS)
        motif.putalpha(motif.getchannel('A').point(lambda a: int(a * layer.get('motif_opacity', 0.35))))
        spacing = max(cell, size + round(4 * scale))
        alt = ImageOps.mirror(motif) if layer.get('motif_alternate_mirror', True) else motif
        for row, y in enumerate(range(0, h + spacing, spacing)):
            shift = spacing // 2 if row % 2 else 0
            for col, x in enumerate(range(-((w // 2) % spacing) + shift - spacing, w + spacing, spacing)):
                top.alpha_composite(alt if (row + col) % 2 else motif, (x, y))
    elif kind == 'image':
        art = Image.open(base / layer['image']).convert('RGBA')
        top = ImageOps.fit(art, (w, h), Image.LANCZOS, centering=(0.5, 0.0))
    if op < 1:
        top.putalpha(top.getchannel('A').point(lambda a: int(a * op)))
    return Image.alpha_composite(img, top)


def resolve(conf):
    """Accept a preset (with overrides), an explicit layer list, or a legacy single-pattern dict."""
    conf = copy.deepcopy(conf)
    if 'preset' in conf:
        if conf['preset'] not in PRESETS:
            sys.exit(f"error: preset must be one of {sorted(PRESETS)}")
        merged = copy.deepcopy(PRESETS[conf['preset']])
        merged.update({k: v for k, v in conf.items() if k != 'preset'})
        conf = merged
    if 'layers' not in conf:
        layer = dict(conf)
        layer['type'] = layer.pop('pattern', 'solid')
        conf = {'layers': [layer], **{k: conf[k] for k in ('text_color', 'soften', 'soften_color') if k in conf}}
    return conf


def render(conf, base, w, h, scale):
    conf = resolve(conf)
    img = Image.new('RGBA', (w, h), (255, 255, 255, 255))
    for layer in conf['layers']:
        img = render_layer(img, layer, base, scale)
    veil = conf.get('soften', 0)
    if veil:
        img = Image.alpha_composite(img, Image.new('RGBA', (w, h), rgba(conf.get('soften_color', '#FFFFFF'))[:3] + (int(255 * veil),)))
    return img


# ---------- checks / outputs ----------

def luminance(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def check(img, text_color):
    """Names, times and dates sit directly on the chat background; check the worst-case contrast
    against the background averaged over text-sized (about 12pt) areas, ignoring the extreme 2%."""
    small = img.convert('RGB').resize((img.width // 36, img.height // 36), Image.BOX)
    # 2nd/98th percentile so a single tiny star or heart does not decide the result
    blocks = sorted(small.getdata(), key=luminance)
    darkest, lightest = blocks[len(blocks) // 50], blocks[-1 - len(blocks) // 50]
    t = rgba(text_color)
    return {'text_color': text_color, 'worst_contrast': round(min(contrast(t, lightest), contrast(t, darkest)), 2)}


def catalog(out, base):
    font = None
    for f in ('C:/Windows/Fonts/malgunbd.ttf', 'C:/Windows/Fonts/malgun.ttf', '/System/Library/Fonts/AppleSDGothicNeo.ttc'):
        if Path(f).exists():
            font = ImageFont.truetype(f, 22)
            break
    tw, th, gap, cols = 300, 520, 24, 4
    names = list(PRESETS)
    rows = math.ceil(len(names) / cols)
    sheet = Image.new('RGB', (cols * (tw + gap) + gap, rows * (th + 50 + gap) + gap), '#FFFFFF')
    d = ImageDraw.Draw(sheet)
    for i, name in enumerate(names):
        x, y = gap + (i % cols) * (tw + gap), gap + (i // cols) * (th + 50 + gap)
        img = render({'preset': name}, base, 1125, 1950, 3).resize((tw, th), Image.LANCZOS)
        sheet.paste(img.convert('RGB'), (x, y))
        d.rounded_rectangle([x, y, x + tw - 1, y + th - 1], radius=10, outline='#DDDDDD', width=2)
        d.text((x + 4, y + th + 10), name, fill='#444444', font=font)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f'wrote {out}')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec', help='JSON with chatroom/main/passcode background settings')
    p.add_argument('--project')
    p.add_argument('--preview-only', action='store_true', help='only write qa/background-*.png samples')
    p.add_argument('--catalog', metavar='PNG', help='render every cute preset into one sheet and exit')
    p.add_argument('--list-presets', action='store_true')
    args = p.parse_args()
    if args.list_presets:
        print('\n'.join(PRESETS))
        return 0
    if args.catalog:
        catalog(args.catalog, Path.cwd())
        return 0
    if not (args.spec and args.project):
        p.error('--spec and --project are required')
    spec_path = Path(args.spec).resolve()
    spec, base = json.loads(spec_path.read_text(encoding='utf-8')), spec_path.parent
    project = Path(args.project).resolve()
    (project / 'qa').mkdir(parents=True, exist_ok=True)
    report, warnings = {}, []
    for target, outputs in TARGETS.items():
        conf = spec.get(target)
        if not conf:
            continue
        for rel, w, h in ([] if args.preview_only else outputs):
            out = project / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            render(conf, base, w, h, w / 375 if 'ios/' in rel else 3).convert('RGB').save(out)
        sample = render(conf, base, 1125, 2250, 3)
        sample.convert('RGB').resize((375, 750), Image.LANCZOS).save(project / 'qa' / f'background-{target}.png')
        result = check(sample, resolve(conf).get('text_color', '#333333'))
        report[target] = {'spec': conf, **result}
        if result['worst_contrast'] < 3:
            warnings.append(f"{target}: text {result['text_color']} reaches only {result['worst_contrast']}:1 on part of the background; "
                            'lower the pattern contrast, add "soften", or change text_color')
    report['warnings'] = warnings
    report['note'] = 'iOS crops top-center and Android scales to the screen; check the real devices separately.'
    (project / 'qa' / 'background-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    for w_ in warnings:
        print('warning:', w_)
    print(f'wrote backgrounds and {project / "qa" / "background-report.json"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
