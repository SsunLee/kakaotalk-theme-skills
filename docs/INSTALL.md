# 설치법

[← README](../README.md) · [사용법](USAGE.md)

## 준비할 것

- 스킬을 읽을 수 있는 Codex 또는 Claude Code.
- 설치 스크립트를 쓰려면 Python 3.10 이상. 별도의 pip 설치는 필요하지 않습니다.
- 원화 생성·Android 빌드·웹 업로드에 필요한 도구는 해당 작업을 할 때 준비합니다. 스킬 설치만으로 SDK나 판매자 계정이 생기지는 않습니다.

## 저장소 받기

```sh
git clone https://github.com/SsunLee/kakaotalk-theme-skills.git
cd kakaotalk-theme-skills
```

Git이 없다면 [저장소](https://github.com/SsunLee/kakaotalk-theme-skills)의 Code → Download ZIP을 선택하고 압축을 풉니다. install.py가 있는 폴더에서 다음 명령을 실행합니다.

## 개인용 설치

```sh
python install.py --target codex
python install.py --target codex --check
```

Claude Code는 `--target claude`를 사용합니다. 두 도구를 모두 쓰면 각각 설치하면 됩니다.

Windows의 Python 실행 이름이 py라면 `py install.py --target codex`로 실행합니다. macOS·Linux에서 python3만 있다면 그 이름으로 바꿉니다.

공식 문서의 현재 기본 경로에 맞춰 Codex는 ~/.agents/skills, Claude Code는 ~/.claude/skills에 복사합니다. 이 경로의 ~는 현재 사용자 홈 폴더입니다. [Codex 스킬 안내](https://learn.chatgpt.com/docs/build-skills), [Claude Code 스킬 안내](https://code.claude.com/docs/en/skills)를 참고합니다.

## 특정 프로젝트에만 설치

```sh
python install.py --target codex --project /path/to/my-project
```

프로젝트의 .agents/skills에 설치됩니다. Claude Code는 같은 옵션으로 .claude/skills에 설치됩니다. Windows 경로에 공백이 있으면 따옴표로 감싸세요.

## 하나만 설치

```sh
python install.py --target codex --skills kakaotalk-theme-builder
python install.py --target codex --skills kakaotalk-theme-publisher
```

제작과 업로드 스킬은 각각 설치할 수 있습니다. 업로드 스킬은 완성 파일과 bundle-manifest.json을 입력으로 사용합니다.

## 다른 호환 도구 또는 직접 지정 경로

```sh
python install.py --dest /path/to/your/skills
```

해당 도구가 SKILL.md 폴더를 읽는지 확인하세요. README의 스킬 호출 기호는 Codex와 Claude Code 기준입니다. 다른 도구의 검색·실행 방식은 해당 제품 문서를 따릅니다.

## Python 없이 수동 설치

skills/kakaotalk-theme-builder와 skills/kakaotalk-theme-publisher 폴더 전체를 해당 도구의 스킬 폴더로 복사합니다. SKILL.md만 복사하면 scripts와 references가 누락됩니다.

수동 복사만으로 작업 지침을 읽을 수 있지만 Python 보조 도구 실행에는 Python이 필요합니다. 수동 설치본은 설치 프로그램의 --update로 덮어쓰지 않습니다.

## 설치 확인

새 대화에서 Codex는 $kakaotalk-theme-builder, Claude Code는 /kakaotalk-theme-builder를 입력합니다. 목록에 보이지 않으면 앱을 다시 시작하고 아래 명령으로 파일 상태를 확인합니다.

```sh
python install.py --target codex --check
```

이 검사는 설치된 파일이 현재 내려받은 저장소와 일치하는지 확인합니다. 이미지 생성·Android SDK·브라우저 로그인 상태까지 검사하지는 않습니다.

## 업데이트

```sh
git pull --ff-only
python install.py --target codex --update
python install.py --target codex --check
```

설치 프로그램으로 설치한 파일이고 로컬 수정이 없을 때만 업데이트합니다. 이전 설치본은 skills 폴더 옆의 .kakaotalk-theme-skill-backups에 보존합니다. 사용자가 수정한 파일은 자동으로 덮어쓰지 않습니다.

ZIP으로 받았다면 새 ZIP을 별도 폴더에 풀고 같은 --update 명령을 실행합니다. 다른 스킬·앱 설정은 변경하지 않습니다.

설치 전에 경로와 동작만 보려면 --dry-run을 사용하세요.
