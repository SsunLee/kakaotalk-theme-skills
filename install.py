#!/usr/bin/env python3
"""Install the two skills locally. No network, credentials or package installation."""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAMES = ['kakaotalk-theme-builder', 'kakaotalk-theme-publisher']
RECEIPT = '.install-receipt.json'


def hashes(folder):
    result = {}
    for path in sorted(Path(folder).rglob('*')):
        if path.is_symlink():
            raise ValueError('Skill files may not be symlinks: ' + str(path))
        if path.is_file() and path.name != RECEIPT:
            if '__pycache__' in path.parts or path.suffix == '.pyc':
                continue
            result[path.relative_to(folder).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def target_root(args):
    if args.dest:
        return Path(args.dest).expanduser().resolve()
    base = Path(args.project).expanduser().resolve() if args.project else Path.home()
    return base / ('.agents' if args.target == 'codex' else '.claude') / 'skills'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target', choices=['codex', 'claude'], default='codex')
    place = p.add_mutually_exclusive_group()
    place.add_argument('--project', help='Install for this project instead of the current user')
    place.add_argument('--dest', help='Explicit skills directory; useful for other compatible hosts')
    p.add_argument('--skills', nargs='+', choices=NAMES, default=NAMES)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--check', action='store_true')
    p.add_argument('--update', action='store_true', help='Update only unmodified copies installed by this script; retain backups')
    args = p.parse_args()
    base = target_root(args)
    names = list(dict.fromkeys(args.skills))
    plans = []
    # Validate every destination before changing any of them.
    for name in names:
        source = ROOT / 'skills' / name
        if not (source / 'SKILL.md').is_file():
            raise ValueError('Missing bundled skill: ' + name)
        original = hashes(source)
        target = base / name
        if target.is_symlink():
            raise ValueError('Refusing to replace a symlink: ' + str(target))
        if target.exists():
            installed = hashes(target)
            if args.check:
                if installed != original:
                    raise ValueError('Installed content differs: ' + name)
            elif not args.update:
                if installed == original:
                    plans.append((name, source, target, original, 'unchanged'))
                    continue
                raise ValueError('Existing skill differs. Inspect it, then use --update if appropriate: ' + name)
            else:
                receipt = target / RECEIPT
                if not receipt.is_file():
                    raise ValueError('Existing skill was not installed by this script: ' + name)
                saved = json.loads(receipt.read_text(encoding='utf-8'))
                if saved.get('source') != 'SsunLee/kakaotalk-theme-skills' or saved.get('files') != installed:
                    raise ValueError('Local modifications detected. Save your edits before updating: ' + name)
        elif args.check:
            raise ValueError('Skill is not installed: ' + name)
        plans.append((name, source, target, original, 'update' if target.exists() else 'install'))
    if args.check:
        print(json.dumps({'status': 'verified', 'skills': names, 'destination': str(base)}, ensure_ascii=False))
        return
    if args.dry_run:
        print(json.dumps({'dry_run': True, 'destination': str(base), 'actions': [{'skill': n, 'action': action} for n, _, _, _, action in plans]}, ensure_ascii=False, indent=2))
        return
    base.mkdir(parents=True, exist_ok=True)
    for name, source, target, original, action in plans:
        if action == 'unchanged':
            continue
        temp = Path(tempfile.mkdtemp(prefix='.theme-install-', dir=base)).resolve()
        assert temp.parent == base.resolve()
        backup = None
        try:
            staging = temp / name
            shutil.copytree(source, staging, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            if hashes(staging) != original:
                raise ValueError('Staging hash mismatch: ' + name)
            receipt = {'source': 'SsunLee/kakaotalk-theme-skills', 'version': (ROOT / 'VERSION').read_text().strip(), 'files': original}
            (staging / RECEIPT).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            if target.exists():
                backup_root = base.parent / '.kakaotalk-theme-skill-backups'
                backup_root.mkdir(exist_ok=True)
                backup = backup_root / (name + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
                assert target.resolve().parent == base.resolve()
                target.rename(backup)
            try:
                staging.rename(target)
            except Exception:
                if backup is not None and not target.exists():
                    backup.rename(target)
                raise
            print(json.dumps({'skill': name, 'status': ('updated' if action == 'update' else 'installed'), 'path': str(target), 'backup': str(backup) if backup else None}, ensure_ascii=False))
        finally:
            assert temp.parent == base.resolve() and temp.name.startswith('.theme-install-')
            shutil.rmtree(temp)
    print('설치했습니다. 새 대화에서 스킬을 확인하세요. 표시되지 않으면 사용 중인 앱을 다시 시작하세요.')


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        main()
    except (ValueError, OSError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(1)
