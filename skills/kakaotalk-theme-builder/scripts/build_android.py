#!/usr/bin/env python3
"""Build a plain Java Android theme project with an installed Android SDK."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from theme_tools import load_project, safe_path, sha256, write_json

ANDROID_NS = '{http://schemas.android.com/apk/res/android}'


def run(args, cwd, log, env=None):
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    result = subprocess.run([str(x) for x in args], cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8', errors='replace', creationflags=flags)
    with log.open('a', encoding='utf-8') as f:
        f.write(Path(str(args[0])).name + '\n' + result.stdout + '\n')
    if result.returncode:
        raise ValueError('Android tool failed. Read local log: ' + str(log))
    return result.stdout


def build(args):
    root, theme = load_project(args.project)
    if 'android' not in theme['platforms']:
        raise ValueError('Android is not selected')
    output = safe_path(root, theme['files']['android'])
    if output.exists():
        raise ValueError('APK already exists; use a new versioned output path')
    source = safe_path(root, 'android/src/main')
    for path in source.rglob('*'):
        safe_path(root, path.relative_to(root).as_posix())
    manifest = ET.parse(source / 'AndroidManifest.xml').getroot()
    if manifest.get('package') != theme['package']:
        raise ValueError('Manifest package differs from theme.json')
    uses_sdk = manifest.find('uses-sdk')
    if uses_sdk is None or not uses_sdk.get(ANDROID_NS + 'minSdkVersion', '').isdigit():
        raise ValueError('Set numeric minSdkVersion in source manifest')
    target_sdk = uses_sdk.get(ANDROID_NS + 'targetSdkVersion', '')
    if not target_sdk.isdigit() or int(target_sdk) > args.api:
        raise ValueError('Set targetSdkVersion no greater than the installed --api')
    sdk = Path(args.sdk).expanduser().resolve()
    java_home = args.java_home or os.environ.get('JAVA_HOME')
    if not java_home:
        raise ValueError('Provide --java-home or JAVA_HOME')
    jdk = Path(java_home).expanduser().resolve() / 'bin'
    executable = '.exe' if os.name == 'nt' else ''
    bt = sdk / 'build-tools' / args.build_tools
    android_jar = sdk / 'platforms' / ('android-' + str(args.api)) / 'android.jar'
    required = [jdk / ('java' + executable), jdk / ('javac' + executable), bt / ('aapt2' + executable), bt / ('zipalign' + executable), bt / 'lib/d8.jar', bt / 'lib/apksigner.jar', android_jar, Path(args.keystore).expanduser().resolve()]
    missing = [str(x) for x in required if not x.is_file()]
    if missing:
        raise ValueError('Missing installed tool/key: ' + ', '.join(missing))
    if not os.environ.get('THEME_STORE_PASSWORD'):
        raise ValueError('Set THEME_STORE_PASSWORD in the process environment; never commit it')
    env = os.environ.copy()
    env.setdefault('THEME_KEY_PASSWORD', env['THEME_STORE_PASSWORD'])
    qa = root / 'qa'
    qa.mkdir(exist_ok=True)
    log = qa / 'android-build.log'
    log.write_text('', encoding='utf-8')
    java = jdk / ('java' + executable)
    aapt = bt / ('aapt2' + executable)
    with tempfile.TemporaryDirectory(prefix='kakao-theme-build-') as temporary:
        stage = Path(temporary)
        local = stage / 'src'
        shutil.copytree(source, local)
        resource_args = []
        for name in ['res', 'theme', 'theme-adv']:
            if (local / name).is_dir():
                compiled = stage / (name + '.zip')
                run([aapt, 'compile', '--dir', local / name, '-o', compiled], stage, log)
                resource_args += ['-R', compiled]
        if not resource_args:
            raise ValueError('No Android resource directories')
        generated = stage / 'generated'
        generated.mkdir()
        unsigned = stage / 'unsigned.apk'
        run([aapt, 'link', '-o', unsigned, '-I', android_jar, '--manifest', local / 'AndroidManifest.xml', '--java', generated, '--auto-add-overlay', *resource_args], stage, log)
        classes = stage / 'classes'
        classes.mkdir()
        sources = sorted((local / 'java').rglob('*.java')) + sorted(generated.rglob('*.java'))
        if not list((local / 'java').rglob('*.java')):
            raise ValueError('Provide a plain Java Activity in android/src/main/java')
        # Use an argument file so projects with many sources avoid Windows command limits.
        javac_args = stage / 'javac.args'
        javac_args.write_text('\n'.join('"' + str(x).replace('\\', '/') + '"' for x in sources), encoding='utf-8')
        run([jdk / ('javac' + executable), '-encoding', 'UTF-8', '-source', '8', '-target', '8', '-classpath', android_jar, '-d', classes, '@' + str(javac_args)], stage, log)
        classjar = stage / 'classes.jar'
        with zipfile.ZipFile(classjar, 'w') as archive:
            for path in classes.rglob('*.class'):
                archive.write(path, path.relative_to(classes).as_posix())
        dex = stage / 'dex'
        dex.mkdir()
        run([java, '-cp', bt / 'lib/d8.jar', 'com.android.tools.r8.D8', '--release', '--min-api', uses_sdk.get(ANDROID_NS + 'minSdkVersion'), '--lib', android_jar, '--output', dex, classjar], stage, log)
        with zipfile.ZipFile(unsigned, 'a', zipfile.ZIP_DEFLATED) as archive:
            for path in dex.glob('*.dex'):
                archive.write(path, path.name)
        aligned = stage / 'aligned.apk'
        run([bt / ('zipalign' + executable), '-f', '4', unsigned, aligned], stage, log)
        signed = stage / 'signed.apk'
        signer = [java, '-jar', bt / 'lib/apksigner.jar']
        run([*signer, 'sign', '--ks', Path(args.keystore).expanduser().resolve(), '--ks-key-alias', args.alias, '--ks-pass', 'env:THEME_STORE_PASSWORD', '--key-pass', 'env:THEME_KEY_PASSWORD', '--out', signed, aligned], stage, log, env)
        verification = run([*signer, 'verify', '--verbose', signed], stage, log)
        badging = run([aapt, 'dump', 'badging', signed], stage, log)
        if "package: name='" + theme['package'] + "'" not in badging:
            raise ValueError('Compiled APK package differs from the project')
        run([bt / ('zipalign' + executable), '-c', '4', signed], stage, log)
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(signed, output)
        write_json(qa / 'android-signature.json', {'apk': output.relative_to(root).as_posix(), 'sha256': sha256(output), 'signature_verified': True, 'verification': verification, 'kakaotalk_runtime_verified': False})
        (qa / 'android-badging.txt').write_text(badging, encoding='utf-8')
    print(json.dumps({'apk': str(output), 'sha256': sha256(output), 'signature_verified': True, 'kakaotalk_runtime_verified': False}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', required=True)
    p.add_argument('--sdk', required=True, help='Android SDK root, with build-tools and platforms')
    p.add_argument('--api', type=int, required=True, help='Installed compile API, e.g. 35; not a promise of store policy compliance')
    p.add_argument('--build-tools', required=True, help='Installed version folder, e.g. 35.0.0')
    p.add_argument('--java-home')
    p.add_argument('--keystore', required=True)
    p.add_argument('--alias', required=True)
    build(p.parse_args())


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        main()
    except (ValueError, OSError, ET.ParseError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(1)
