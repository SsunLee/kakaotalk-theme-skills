# 사용법

[← README](../README.md) · [설치법](INSTALL.md) · [문제 해결](TROUBLESHOOTING.md)

## 1. 원화를 먼저 확인하고 제작하기

```text
$kakaotalk-theme-builder
./art 폴더의 기존 캐릭터 원화를 사용해 ‘작은 토끼의 하루’ 테마를 만들어 주세요.
아이폰과 안드로이드를 지원하고 채팅·말풍선·암호 화면·친구목록을 확인할 수 있게 해 주세요.
작업 폴더는 ./work/little-rabbit 입니다.
원화와 기존 설정을 먼저 확인하고 설치 파일, 미리보기 7장, 안내서, ZIP을 준비해 주세요.
```

제작자명과 배포용 고유 패키지 ID가 필요합니다. 사용자가 이미 정한 값이 있으면 함께 알려 주세요. AI가 파일 확인부터 구현·빌드·검수까지 진행할 때 필요한 도구가 없는 단계는 따로 설명합니다.

## 2. 원화부터 새로 만들기

```text
$kakaotalk-theme-builder
민트색 리본을 단 독창적인 고양이 캐릭터로 카카오톡 테마를 만들어 주세요.
또렷한 윤곽과 단색 면을 사용하고, 보내는 말풍선과 받는 말풍선의 표정을 다르게 해 주세요.
이미지 생성 도구를 사용할 수 있는지 확인하고 원화와 배경을 만든 뒤 구현해 주세요.
```

이미지 생성 서비스의 이용권한·요금과 결과물 이용조건은 사용하는 서비스에 따릅니다. 생성 도구가 없는 환경에서는 기존 원화로 작업하거나 필요한 자료를 먼저 안내받을 수 있습니다.

## 3. 기존 테마 수정하기

```text
$kakaotalk-theme-builder
./work/my-theme의 말풍선을 수정해 주세요.
짧은 ‘응’에서도 오른쪽에 빈 공간이 길게 남지 않도록 하고 캐릭터 크기는 유지해 주세요.
기존 파일을 보존한 새 버전으로 만들고 한 글자·한 줄·여러 줄을 비교해 주세요.
```

기존 상품을 수정하거나 가격을 바꾸는 작업은 별도의 업로드 요청 범위에 따릅니다.

## 4. 완성 파일만 검사하고 묶기

GitHub 저장소 루트에서 다음 명령을 사용합니다.

```sh
python skills/kakaotalk-theme-builder/scripts/theme_tools.py init --project ./work/my-theme --slug my-theme --name "나의 테마" --package com.example.mytheme
```

theme.json의 이름·제작자·설명·패키지를 실제 값으로 채우고 파일 경로를 연결합니다. 완성한 파일과 미리보기를 작업 폴더 안에 둔 뒤 실행합니다.

```sh
python skills/kakaotalk-theme-builder/scripts/theme_tools.py check --project ./work/my-theme
python skills/kakaotalk-theme-builder/scripts/theme_tools.py package --project ./work/my-theme
```

[전체 파일 규격과 Android 빌드 사용법](../skills/kakaotalk-theme-builder/references/tooling.md)을 참고하세요.

## 5. 플랫폼마다 다른 조건으로 업로드하기

```text
$kakaotalk-theme-publisher
./work/my-theme/bundle-manifest.json을 기준으로 내 계정에 등록해 주세요.
리틀리는 1,000원, 포스타입은 일반 구독자 전용 무료, 원스토어는 1,000원입니다.
원스토어는 대한민국 배포와 심사 통과 후 자동 판매를 선택해 주세요.
각 플랫폼의 기존 상품부터 확인하고 실제 URL·가격·공개 범위·심사 상태를 알려주세요.
```

본인 플랫폼 계정과 브라우저 도구 연결이 필요합니다. 로그인이나 인증 화면에서 사용자 조작이 필요한 경우 해당 단계가 표시됩니다. 이 저장소는 인증정보를 저장하거나 판매자 계정을 공유하지 않습니다.

## 6. 업로드 자료만 준비하기

```text
$kakaotalk-theme-publisher
이 테마를 리틀리 1,000원과 포스타입 구독자 전용 무료로 배포할 자료만 만들어 주세요.
실제 사이트에 업로드하거나 발행하지는 마세요.
```

[등록 도구 명령](../skills/kakaotalk-theme-publisher/references/workflow.md)을 직접 실행해도 됩니다. prepare는 오프라인으로 동작하며 웹사이트에 상품을 만들지 않습니다.

## 7. 중단한 업로드 이어가기

```text
$kakaotalk-theme-publisher
./releases/postype-my-theme 작업을 이어가 주세요.
state.json의 기존 상품 ID와 실제 플랫폼 상태를 먼저 대조해 주세요.
이미 발행됐다면 재발행하지 말고 가격·구독자 제한·첨부 파일만 확인해 주세요.
```

submit_attempted 상태는 성공·실패가 아직 확인되지 않은 상태입니다. 같은 ID의 실제 화면과 히스토리를 대조한 후 기록을 복구합니다. 폴더를 지우거나 새 상품을 만들면 중복을 막기 어려워집니다.

## 결과를 읽는 방법

- prepared: 등록 자료가 만들어졌습니다. 원격 업로드 완료를 뜻하지 않습니다.
- draft_uploaded: 실제 원격 초안 ID가 기록되었습니다.
- submit_attempted: 최종 제출 직전 시도가 기록됐으며, 결과 확인이 필요합니다.
- published: 리틀리·포스타입에서 확인한 게시 결과를 근거로 기록했습니다.
- review_requested: 원스토어의 심사 접수를 확인했습니다. 판매 시작과 다릅니다.

이 상태들은 에이전트 또는 사용자가 관찰한 근거를 기록합니다. Python 스크립트가 플랫폼 서버를 자동으로 조회해 보증하는 값은 아닙니다.
