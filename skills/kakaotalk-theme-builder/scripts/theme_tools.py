#!/usr/bin/env python3
"""Portable, offline KakaoTalk theme packaging helpers. Python 3.10+."""
import argparse
import hashlib
import json
import re
import struct
import sys
import zipfile
from pathlib import Path, PurePosixPath

PREVIEWS = ['01-cover.png', '02-lock.png', '03-installation.png', '04-tabs.png', '05-bubbles.png', '06-chat.png', '07-friends.png']


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def safe_path(root, relative):
    root = Path(root).resolve()
    relative = str(relative)
    p = PurePosixPath(relative)
    if not relative or '\\' in relative or ':' in relative or p.is_absolute() or '..' in p.parts:
        raise ValueError('Use a project-relative path: ' + relative)
    result = root.joinpath(*p.parts)
    for parent in [result, *result.parents]:
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError('Symlinks are not package inputs: ' + relative)
    if not result.resolve().is_relative_to(root):
        raise ValueError('Path escapes project: ' + relative)
    return result


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def inspect_zip(path, kind):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive entries: ' + str(path))
        for entry in archive.infolist():
            p = PurePosixPath(entry.filename)
            if p.is_absolute() or '..' in p.parts or '\\' in entry.filename or ':' in entry.filename:
                raise ValueError('Unsafe archive entry: ' + entry.filename)
            if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Symlink archive entry: ' + entry.filename)
        if archive.testzip() is not None:
            raise ValueError('Corrupt archive: ' + str(path))
        if kind == 'ios':
            css = [x for x in ['KakaoTalkTheme.css', 'KakaoTalk.css'] if x in names]
            if len(css) != 1 or not any(x.startswith('Images/') and x.lower().endswith('.png') for x in names):
                raise ValueError('iOS needs one root CSS and Images/*.png')
            text = archive.read(css[0]).decode('utf-8-sig')
            if 'ManifestStyle' not in text:
                raise ValueError('iOS CSS has no ManifestStyle')
            for name in re.findall(r"['\"]([^'\"]+\.png)['\"]", text):
                stem = name[:-4]
                candidates = ['Images/' + name, 'Images/' + stem + '@2x.png', 'Images/' + stem + '@3x.png']
                if not any(x in names for x in candidates):
                    raise ValueError('Missing iOS image: ' + name)
        if kind == 'android' and not {'AndroidManifest.xml', 'classes.dex'}.issubset(names):
            raise ValueError('APK needs AndroidManifest.xml and classes.dex')


def load_project(project):
    root = Path(project).resolve()
    data = read_json(root / 'theme.json')
    if data.get('schema_version') != 1:
        raise ValueError('Unsupported schema_version')
    if not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', data.get('slug', '')):
        raise ValueError('slug must be lowercase kebab-case')
    for field in ['name', 'author', 'description', 'version']:
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError('Fill theme.json field: ' + field)
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+', data.get('package', '')):
        raise ValueError('Set a unique reverse-domain package ID')
    platforms = data.get('platforms', [])
    if not platforms or len(platforms) != len(set(platforms)) or set(platforms) - {'ios', 'android'}:
        raise ValueError('platforms must contain ios and/or android without duplicates')
    return root, data


def validate(project):
    root, data = load_project(project)
    assets = []
    for kind in data['platforms']:
        relative = data.get('files', {}).get(kind)
        if not relative:
            raise ValueError('Missing file for ' + kind)
        path = safe_path(root, relative)
        extension = '.ktheme' if kind == 'ios' else '.apk'
        if path.suffix.lower() != extension or not path.is_file():
            raise ValueError('Missing native file: ' + str(path))
        inspect_zip(path, kind)
        assets.append({'role': kind, 'path': relative, 'sha256': sha256(path), 'bytes': path.stat().st_size})
    previews = data.get('previews', [])
    if len(previews) < 7 or len(set(previews)) != len(previews):
        raise ValueError('Provide at least seven distinct preview paths')
    for relative in previews:
        path = safe_path(root, relative)
        with path.open('rb') as f:
            header = f.read(24)
        if header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR':
            raise ValueError('Preview is not a PNG: ' + relative)
        width, height = struct.unpack('>II', header[16:24])
        if min(width, height) < 320:
            raise ValueError('Preview is too small: ' + relative)
        assets.append({'role': 'preview', 'path': relative, 'sha256': sha256(path), 'bytes': path.stat().st_size, 'width': width, 'height': height})
    guides = data.get('guides', [])
    if not guides:
        raise ValueError('Include an installation/use guide')
    for relative in guides:
        path = safe_path(root, relative)
        if path.suffix.lower() not in {'.txt', '.md'} or not path.read_text(encoding='utf-8-sig').strip():
            raise ValueError('Guide must be non-empty UTF-8 text: ' + relative)
        assets.append({'role': 'guide', 'path': relative, 'sha256': sha256(path), 'bytes': path.stat().st_size})
    paths = [x['path'] for x in assets]
    if len(paths) != len(set(paths)):
        raise ValueError('Asset paths must not overlap across roles')
    review = data.get('review', {})
    if review.get('preview_kind') not in {'rendered', 'device_capture', 'mixed'} or type(review.get('kakaotalk_tested')) is not bool:
        raise ValueError('Set review.preview_kind and boolean review.kakaotalk_tested')
    return {'schema_version': 1, 'theme': {k: data[k] for k in ['slug', 'name', 'author', 'description', 'version', 'package', 'platforms']}, 'assets': assets, 'review': review, 'checks': {'archive_structure': True, 'apk_signature': 'not_checked_by_this_command', 'visual_quality': 'requires_human_or_agent_review', 'kakaotalk_runtime': 'user_reported_not_automatically_verified'}}


def init_project(project, slug, name, package):
    if not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', slug):
        raise ValueError('Invalid slug')
    root = Path(project).resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError('Choose an empty project folder')
    for sub in ['art', 'ios/Images', 'android/src/main', 'previews', 'dist', 'guides', 'qa']:
        (root / sub).mkdir(parents=True, exist_ok=True)
    data = {'schema_version': 1, 'slug': slug, 'name': name, 'author': '', 'description': '', 'package': package, 'version': '1.0.0', 'platforms': ['ios', 'android'], 'files': {'ios': f'dist/{slug}.ktheme', 'android': f'dist/{slug}.apk'}, 'previews': ['previews/' + x for x in PREVIEWS], 'guides': ['guides/installation.txt', 'guides/usage.txt'], 'review': {'preview_kind': 'rendered', 'kakaotalk_tested': False, 'notes': ''}}
    write_json(root / 'theme.json', data)
    (root / 'guides/installation.txt').write_text('아이폰: .ktheme 파일을 카카오톡의 나와의 채팅으로 공유한 뒤 열어 적용합니다.\n안드로이드: .apk 파일을 설치한 뒤 테마 앱 또는 카카오톡 테마 설정에서 적용합니다.\n이전 배경이 남으면 대화방 설정에서 테마 배경 적용을 선택합니다.\n', encoding='utf-8')
    (root / 'guides/usage.txt').write_text('사용 범위와 재배포 조건은 제작자가 작성해 주세요. 실제 기기에서 확인한 범위도 적어 주세요.\n', encoding='utf-8')
    print(json.dumps({'project': str(root), 'status': 'scaffold_only', 'next': 'Fill author/description, supply owned artwork and native projects; see the builder skill.'}, ensure_ascii=False))


def pack_ios(project):
    root, data = load_project(project)
    if 'ios' not in data['platforms']:
        raise ValueError('iOS is not selected')
    source = root / 'ios'
    target = safe_path(root, data['files']['ios'])
    if target.exists():
        raise ValueError('Output exists; choose a new versioned path in theme.json')
    css = [source / x for x in ['KakaoTalkTheme.css', 'KakaoTalk.css'] if (source / x).is_file()]
    if len(css) != 1:
        raise ValueError('Provide exactly one supported CSS file in ios/')
    files = css + sorted((source / 'Images').rglob('*.png'))
    for path in files:
        safe_path(root, path.relative_to(root).as_posix())
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + '.tmp')
    if temporary.exists():
        raise ValueError('Temporary output already exists')
    try:
        with zipfile.ZipFile(temporary, 'x', zipfile.ZIP_DEFLATED) as archive:
            for path in files:
                archive.write(path, path.relative_to(source).as_posix())
        inspect_zip(temporary, 'ios')
        temporary.rename(target)
    finally:
        temporary.unlink(missing_ok=True)
    print(json.dumps({'ios': str(target), 'sha256': sha256(target), 'runtime_verified': False}))


def package_project(project):
    report = validate(project)
    root = Path(project).resolve()
    target = root / 'dist' / (report['theme']['slug'] + '-bundle.zip')
    manifest = root / 'bundle-manifest.json'
    if target.exists() or manifest.exists():
        raise ValueError('Bundle exists; use a new project version instead of overwriting a release')
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED) as archive:
        for entry in report['assets']:
            if entry['role'] != 'preview':
                path = safe_path(root, entry['path'])
                archive.write(path, entry['path'])
    inspect_zip(target, 'bundle')
    report['bundle'] = {'path': target.relative_to(root).as_posix(), 'sha256': sha256(target), 'bytes': target.stat().st_size}
    write_json(manifest, report)
    print(json.dumps({'manifest': str(manifest), 'bundle': str(target), 'files': len(report['assets'])}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init', help='Create an empty project, not a finished theme')
    p.add_argument('--project', required=True)
    p.add_argument('--slug', required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--package', required=True)
    for command in ['pack-ios', 'check', 'package']:
        sub.add_parser(command).add_argument('--project', required=True)
    args = parser.parse_args()
    if args.command == 'init':
        init_project(args.project, args.slug, args.name, args.package)
    elif args.command == 'pack-ios':
        pack_ios(args.project)
    elif args.command == 'check':
        print(json.dumps(validate(args.project), ensure_ascii=False, indent=2))
    else:
        package_project(args.project)


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        main()
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(1)
