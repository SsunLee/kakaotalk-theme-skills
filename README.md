# 카카오톡 테마 제작·업로드 스킬

**내 캐릭터로 테마를 만들고, 설치 파일을 검수한 뒤, 원하는 플랫폼에 등록하세요.**

[![검사](https://github.com/SsunLee/kakaotalk-theme-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/SsunLee/kakaotalk-theme-skills/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[설치법](docs/INSTALL.md) · [사용법](docs/USAGE.md) · [문제 해결](docs/TROUBLESHOOTING.md) · [지원 범위](#지원-범위) · [라이선스](LICENSE)

Codex와 Claude Code 등 **Agent Skills를 읽는 AI 코딩 도구용 스킬 모음**입니다.
기존 원화와 편집 가능한 테마 프로젝트를 확인하고, 제작·파일 검수·배포 자료 준비·실제 등록 확인을 단계별로 수행합니다.

| 스킬 | 하는 일 |
|---|---|
| [`kakaotalk-theme-builder`](skills/kakaotalk-theme-builder/SKILL.md) | 원화와 디자인을 리소스로 구현하고 iOS·Android 파일, 미리보기, 배포 ZIP을 제작·검수합니다. |
| [`kakaotalk-theme-publisher`](skills/kakaotalk-theme-publisher/SKILL.md) | 리틀리·포스타입·원스토어별 가격과 공개 범위를 준비하고 승인된 업로드를 진행합니다. |

> **시작하기 전에**
>
> 스킬은 AI가 따라야 할 작업 지침과 Python 보조 도구입니다. 이미지 제작에는 사용자 원화 또는 이미지 생성 도구가, Android 빌드에는 JDK·Android SDK·본인 서명키가 필요합니다. 실제 업로드에는 본인 판매자 계정과 AI 환경의 브라우저 제어 기능이 필요합니다. 설치 프로그램은 계정 로그인이나 상품 발행을 실행하지 않습니다.

## 빠른 설치

### 방법 1. 저장소를 내려받아 설치하기

Python **3.10 이상**을 준비합니다. Git을 사용하지 않는다면 GitHub의 **Code → Download ZIP**으로 내려받아 압축을 풀어도 됩니다.

```sh
git clone https://github.com/SsunLee/kakaotalk-theme-skills.git
cd kakaotalk-theme-skills
python install.py --target codex
```

Claude Code를 사용한다면 마지막 명령을 다음과 같이 바꿉니다.

```sh
python install.py --target claude
```

Windows에서 `python`을 찾지 못하면 `py`, macOS·Linux에서는 `python3`로 실행해 보세요.

| 대상 | 기본 설치 위치 |
|---|---|
| Codex | `~/.agents/skills/` |
| Claude Code | `~/.claude/skills/` |
| 프로젝트 한정 | `--project <프로젝트경로>` 옵션으로 지정합니다. |

설치 후 **새 대화**에서 아래 스킬을 불러보세요. 목록에 보이지 않으면 사용 중인 앱을 다시 시작합니다.
설치 확인은 `python install.py --target codex --check`로 할 수 있습니다.

### 방법 2. Codex에 설치를 요청하기

다음 문장을 Codex에 붙여 넣으세요.

```text
$skill-installer
https://github.com/SsunLee/kakaotalk-theme-skills 저장소에서
skills/kakaotalk-theme-builder와
skills/kakaotalk-theme-publisher를 설치해 주세요.
```

스킬 선택 설치, 프로젝트 설치, 업데이트, 수동 복사는 [설치법](docs/INSTALL.md)에 정리했습니다.

## 사용법

### 새 테마 제작

Codex에서는 다음과 같이 요청합니다.

```text
$kakaotalk-theme-builder
내가 제공한 토끼 원화로 아이폰·안드로이드 카카오톡 테마를 만들어 주세요.
테마 이름은 ‘작은 토끼의 하루’입니다.
작업 폴더는 ./work/little-rabbit 입니다.
기존 원화를 먼저 확인하고, 미리보기 7장과 설치 안내, 배포 ZIP까지 준비해 주세요.
```

Claude Code에서는 첫 줄을 `/kakaotalk-theme-builder`로 바꿉니다.
원화가 없으면 사용할 수 있는 이미지 생성 도구와 원하는 스타일을 함께 알려주세요.

### 완성된 테마 업로드

```text
$kakaotalk-theme-publisher
./work/little-rabbit의 완성된 테마를 내 계정에 등록해 주세요.
리틀리는 1,000원, 포스타입은 구독자 전용 무료, 원스토어는 1,000원입니다.
원스토어는 대한민국 배포, 심사 통과 후 자동 판매로 설정해 주세요.
기존 상품과 중복되지 않는지 확인하고 플랫폼별 실제 결과를 알려주세요.
```

위 가격과 공개 조건은 **요청 예시**입니다. 자신의 판매 조건으로 바꿔 사용하세요.
자료만 준비하려면 “업로드하지 말고 등록 자료까지만 준비해 주세요”라고 지정하면 됩니다.

[기존 테마 수정, 파일만 패키징, 중단된 업로드 재개 예시 →](docs/USAGE.md)

## 어떤 결과물이 나오나요?

```text
내 테마 프로젝트/
├── theme.json              테마명·제작자·파일·검수 설정
├── ios/                    iOS CSS와 이미지
├── android/                Android 소스와 리소스
├── previews/               전체·채팅·말풍선 등 미리보기 7장
├── guides/                 설치·이용 안내
├── qa/                     빌드와 검수 기록
├── dist/                   .ktheme, .apk, 구매용 ZIP
└── bundle-manifest.json    파일 목록과 SHA-256

플랫폼별 등록 폴더/
├── uploads/                해당 플랫폼에 올릴 파일
├── description.md          검토·보완할 소개 글
├── listing.json            계정·가격·공개 범위
├── state.json              상품 ID와 제출 상태
└── CHECKLIST.md            남은 확인 사항
```

구매용 ZIP에는 설치 파일과 안내서가 들어갑니다. 원화·소스·서명키는 자동으로 포함되지 않습니다.

## 지원 범위

| 기능 | 제공 방식과 필요한 준비 |
|---|---|
| 원화·테마 디자인 | AI 작업 지침을 제공합니다. 원화나 이미지 생성 도구는 사용자가 준비합니다. |
| iOS `.ktheme` | 완성한 CSS·이미지 폴더를 검증하고 패키징합니다. |
| Android `.apk` | 단순 Java 프로젝트용 SDK 빌더를 제공합니다. JDK·SDK·서명키가 필요합니다. Kotlin·AndroidX 프로젝트는 기존 빌드를 사용합니다. |
| 미리보기 | 에이전트가 설치 리소스로 제작하고 직접 검토합니다. 7장 이상 파일·크기 검사는 도구가 수행합니다. |
| 리틀리·포스타입·원스토어 | 플랫폼별 절차와 자료·상태 기록 도구를 제공합니다. 실제 업로드는 연결된 브라우저에서 수행합니다. |
| 업로드 재개 | 상품 ID·시도·관찰 근거를 기록하며, 불명확한 최종 요청을 확인 없이 반복하지 않도록 합니다. |
| 기기 적용 검증 | 파일 검사와 별도로 수행합니다. 실제 확인하지 않은 카카오톡 적용을 성공으로 표시하지 않습니다. |

`theme_tools.py check`는 구조·해시·PNG 헤더를 검사합니다.
APK 서명은 Android 빌더 또는 별도의 `apksigner` 검사로 확인해야 합니다.
서명과 파일 검사 통과만으로 최신 카카오톡·스토어 호환성이 보장되지는 않습니다.

이 저장소에는 기존 판매용 테마·캐릭터, 카카오 공식 샘플, Android SDK, 서명키, 판매자 인증정보가 포함되어 있지 않습니다.
카카오의 공식 제품이 아닌 독립적인 작업 도구입니다.

## 개발·기여

보조 도구는 Python 표준 라이브러리를 사용합니다. 설치·패키징·오류 처리·중복 시도 방지는 다음 명령으로 검사합니다.

```sh
python -m unittest discover -s tests -v
```

[기여 안내](CONTRIBUTING.md)와 [보안 안내](SECURITY.md)를 확인해 주세요.
문제 제보에는 OS, Python 버전, 실패한 단계, 민감정보를 지운 오류 내용을 적어 주세요.

코드와 문서는 [MIT 라이선스](LICENSE)로 제공합니다.
사용자 원화·폰트·공식 샘플·생성한 상품의 이용조건은 해당 권리자와 제작 도구의 조건을 따릅니다.
