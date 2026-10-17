#!/usr/bin/env python3
"""Offline release staging and durable one-attempt journal. Does not upload."""
import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

PLATFORMS = ['littly', 'postype', 'onestore']


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def save(path, data):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('x', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    temp.replace(path)


@contextmanager
def lock(folder):
    path = Path(folder) / '.release.lock'
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise ValueError('Release is locked. Reconcile the previous process before removing its lock.') from None
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        path.unlink(missing_ok=True)


def inside(root, relative):
    root = Path(root).resolve()
    p = PurePosixPath(str(relative))
    if not str(relative) or p.is_absolute() or '..' in p.parts or '\\' in str(relative) or ':' in str(relative):
        raise ValueError('Unsafe relative path: ' + str(relative))
    path = root.joinpath(*p.parts)
    for item in [path, *path.parents]:
        if item == root:
            break
        if item.is_symlink():
            raise ValueError('Symlink is not a release input')
    if not path.resolve().is_relative_to(root):
        raise ValueError('Path escapes project')
    return path


def check_files(folder, listing):
    for item in listing['assets']:
        path = inside(folder, item['path'])
        if digest(path) != item['sha256']:
            raise ValueError('Release file changed: ' + item['path'])
    return True


def prepare(args):
    if args.price < 0:
        raise ValueError('Price cannot be negative')
    if args.visibility in {'public', 'subscribers'} and args.price != 0:
        raise ValueError('A free visibility needs price 0; use buyers for paid content')
    if args.visibility == 'buyers' and args.price <= 0:
        raise ValueError('Buyers-only requires a positive price')
    if args.platform != 'postype' and args.visibility == 'subscribers':
        raise ValueError('Subscriber-only is supported here for Postype only')
    manifest_path = Path(args.bundle_manifest).resolve()
    bundle = read(manifest_path)
    if bundle.get('schema_version') != 1:
        raise ValueError('Unsupported bundle manifest')
    project = manifest_path.parent
    selected = [x for x in bundle['assets'] if x['role'] == 'preview']
    roles = {x['role'] for x in bundle['assets']}
    if len(selected) < 7:
        raise ValueError('Seven previews are required')
    if args.platform == 'littly':
        selected.append({'role': 'bundle', **bundle['bundle']})
    elif args.platform == 'postype':
        selected += [x for x in bundle['assets'] if x['role'] in {'ios', 'android', 'guide'}]
        if not roles.intersection({'ios', 'android'}):
            raise ValueError('A native file is required')
    else:
        if 'android' not in roles:
            raise ValueError('ONE store requires Android')
        selected += [x for x in bundle['assets'] if x['role'] == 'android']
    for item in selected:
        if digest(inside(project, item['path'])) != item['sha256']:
            raise ValueError('Source hash mismatch: ' + item['path'])
    target = Path(args.out).resolve()
    if target == project or target in project.parents:
        raise ValueError('Choose a separate release folder')
    if target.exists() and any(target.iterdir()):
        raise ValueError('Release folder exists; resume it instead of creating a duplicate')
    target.mkdir(parents=True, exist_ok=True)
    assets = []
    for index, item in enumerate(selected):
        source = inside(project, item['path'])
        relative = 'uploads/' + str(index + 1).zfill(2) + '-' + source.name
        output = inside(target, relative)
        output.parent.mkdir(exist_ok=True)
        shutil.copy2(source, output)
        assets.append({'role': item['role'], 'path': relative, 'sha256': item['sha256']})
    listing = {'schema_version': 1, 'platform': args.platform, 'account': args.account, 'theme': bundle['theme'], 'price': args.price, 'currency': 'POINT' if args.platform == 'postype' else 'KRW', 'visibility': args.visibility, 'assets': assets, 'review': bundle['review'], 'prepared_at': now()}
    save(target / 'listing.json', listing)
    save(target / 'state.json', {'status': 'prepared', 'remote_id': None, 'url': None, 'attempts': [], 'events': [{'at': now(), 'action': 'prepared'}]})
    theme = bundle['theme']
    access = '구독자 전용 무료' if args.visibility == 'subscribers' else ('무료' if args.price == 0 else str(args.price) + ('P' if args.platform == 'postype' else '원'))
    body = '# ' + theme['name'] + '\n\n' + theme['description'] + '\n\n' + access + ' · 테마 한 종류\n\n'
    if args.platform == 'onestore':
        body += 'Android 전용 카카오톡 테마입니다. iPhone에서는 사용할 수 없습니다.\n\n'
    else:
        supported = ['아이폰' if x == 'ios' else '안드로이드' for x in theme['platforms']]
        body += '·'.join(supported) + '용 설치 파일을 제공합니다.\n\n'
        for item in assets:
            if item['role'] == 'preview':
                body += '![테마 미리보기](' + item['path'] + ')\n\n'
    if bundle['review']['preview_kind'] == 'rendered':
        body += '미리보기는 테마 리소스로 만든 예시입니다.\n\n'
    if not bundle['review'].get('kakaotalk_tested'):
        body += '실제 카카오톡 내부 적용은 아직 확인하지 않았습니다.\n\n'
    body += '기기와 카카오톡 버전에 따라 표시가 달라질 수 있습니다. 카카오톡 암호 화면은 휴대전화 자체의 잠금화면과 다릅니다.\n\n'
    body += '설치 방법과 사용 범위는 첨부된 제작자 안내서를 확인해 주세요.\n'
    (target / 'description.md').write_text(body, encoding='utf-8')
    checklist = '# 등록 전 확인\n\n- 본인 계정과 상품 중복 여부를 실제 화면에서 확인합니다.\n- listing.json의 가격·공개 범위와 파일을 대조합니다.\n- description.md를 검토하고 이미지 생성 방식·사용권·문의처를 사실대로 보완합니다.\n- 유료 상품에는 해당 플랫폼의 최신 구매·환불 안내를 확인해 추가합니다. 무료 글에 유료 환불 안내를 넣지 않습니다.\n- 원스토어는 실제 앱 실행 캡처, 아이콘, 대표 그래픽, 현재 심사 요건과 이용등급을 별도로 준비합니다. 이 폴더의 rendered 미리보기를 실기기 캡처라고 표기하지 않습니다.\n- 원격 초안이 만들어지면 bind로 상품 ID를 기록합니다.\n- 사용자 요청 범위를 확인하고 attempt를 기록한 뒤 최종 버튼을 한 번 누릅니다.\n- 성공이나 불명확한 결과는 증거 JSON으로 confirm 또는 reconcile합니다.\n\n이 도구는 웹사이트에 접속하거나 업로드하지 않습니다. 파일 준비와 재시도 방지 기록을 담당합니다.\n'
    (target / 'CHECKLIST.md').write_text(checklist, encoding='utf-8')
    print(json.dumps({'status': 'prepared_not_uploaded', 'folder': str(target), 'assets': len(assets)}, ensure_ascii=False))


def evidence(folder, path, listing, state, outcome):
    value = read(path)
    for key in ['platform', 'account', 'price', 'visibility']:
        if value.get(key) != listing[key]:
            raise ValueError('Evidence does not match listing field: ' + key)
    if value.get('remote_id') != state['remote_id'] or value.get('outcome') != outcome:
        raise ValueError('Evidence ID or outcome mismatch')
    if not value.get('observed_at') or not value.get('note') or not value.get('url', '').startswith('https://'):
        raise ValueError('Evidence needs observed_at, note and an https URL')
    dest = Path(folder) / ('evidence-' + str(time.time_ns()) + '.json')
    save(dest, value)
    return dest.name, value


def transition(args):
    folder = Path(args.release).resolve()
    with lock(folder):
        listing = read(folder / 'listing.json')
        state = read(folder / 'state.json')
        check_files(folder, listing)
        event = {'at': now(), 'action': args.command}
        if args.command == 'bind':
            if state['status'] not in {'prepared', 'draft_uploaded'}:
                raise ValueError('Cannot bind a submitted or ambiguous release')
            if state['remote_id'] not in {None, args.remote_id}:
                raise ValueError('A different remote ID is already bound')
            if not args.url.startswith('https://'):
                raise ValueError('Use the observed https product/editor URL')
            state.update(status='draft_uploaded', remote_id=args.remote_id, url=args.url)
            event['remote_id'] = args.remote_id
        elif args.command == 'attempt':
            if state['status'] != 'draft_uploaded' or not state['remote_id']:
                raise ValueError('Bind an inspected remote draft first; reconcile any prior attempt')
            if not args.authorization.strip():
                raise ValueError('Reference the user instruction authorizing this destination and settings')
            item = {'at': now(), 'authorization': args.authorization, 'remote_id': state['remote_id'], 'listing_sha256': digest(folder / 'listing.json'), 'outcome': 'unknown'}
            state['attempts'].append(item)
            state['status'] = 'submit_attempted'
        else:
            if state['status'] != 'submit_attempted':
                raise ValueError('An unconfirmed recorded attempt is required')
            if state['attempts'][-1]['listing_sha256'] != digest(folder / 'listing.json'):
                raise ValueError('Listing settings changed after the attempt')
            success = 'review_requested' if listing['platform'] == 'onestore' else 'published'
            outcome = success if args.command == 'confirm' else args.outcome
            if outcome not in {success, 'not_submitted'}:
                raise ValueError('Invalid outcome for this platform')
            file, value = evidence(folder, args.evidence, listing, state, outcome)
            state['attempts'][-1].update(outcome=outcome, evidence=file)
            state.update(status=success if outcome == success else 'draft_uploaded', url=value['url'])
            event.update(evidence=file, outcome=outcome)
        state['events'].append(event)
        save(folder / 'state.json', state)
    print(json.dumps(state, ensure_ascii=False, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--bundle-manifest', required=True)
    prep.add_argument('--out', required=True)
    prep.add_argument('--platform', choices=PLATFORMS, required=True)
    prep.add_argument('--account', required=True)
    prep.add_argument('--price', type=int, required=True)
    prep.add_argument('--visibility', choices=['public', 'subscribers', 'buyers'], required=True)
    for name in ['status', 'bind', 'attempt', 'confirm', 'reconcile']:
        item = sub.add_parser(name)
        item.add_argument('--release', required=True)
        if name == 'bind':
            item.add_argument('--remote-id', required=True)
            item.add_argument('--url', required=True)
        if name == 'attempt':
            item.add_argument('--authorization', required=True)
        if name in {'confirm', 'reconcile'}:
            item.add_argument('--evidence', required=True)
        if name == 'reconcile':
            item.add_argument('--outcome', choices=['published', 'review_requested', 'not_submitted'], required=True)
    args = p.parse_args()
    if args.command == 'prepare':
        prepare(args)
    elif args.command == 'status':
        listing = read(Path(args.release) / 'listing.json')
        check_files(args.release, listing)
        print(json.dumps({'files_unchanged': True, 'state': read(Path(args.release) / 'state.json')}, ensure_ascii=False, indent=2))
    else:
        transition(args)


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        main()
    except (ValueError, OSError, KeyError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(1)
