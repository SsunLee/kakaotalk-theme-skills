# 도구 사용법과 파일 규격

명령은 설치된 제작 스킬 폴더에서 실행한다. GitHub 저장소를 내려받아 직접 쓰면 아래 scripts/ 앞에 skills/kakaotalk-theme-builder/를 붙인다. Python 3.10 이상이며 아래 도구에는 pip 의존성이 없다.

## 처음 시작

```sh
python scripts/theme_tools.py init --project ./work/my-theme --slug my-theme --name "나의 테마" --package com.example.mytheme
```

생성되는 theme.json의 author·description과 guides/usage.txt를 실제 내용으로 채운다. init은 원화나 완성 설치 파일을 생성하지 않는다. 사용할 운영체제만 platforms에 남길 수 있다.

```text
my-theme/
├── theme.json
├── art/                     사용자 소유 원화
├── ios/
│   ├── KakaoTalkTheme.css   또는 KakaoTalk.css
│   └── Images/
├── android/src/main/
│   ├── AndroidManifest.xml
│   ├── java/
│   ├── res/
│   ├── theme/              사용하는 프로젝트에만 필요
│   └── theme-adv/          사용하는 프로젝트에만 필요
├── previews/               PNG 미리보기 7장 이상
├── guides/                 설치·이용 안내
├── qa/                     검사 근거
└── dist/                   설치 파일·구매용 ZIP
```

theme.json은 schema_version=1, slug, name, author, description, package, version, platforms, files, previews, guides, review를 갖는다. paths는 프로젝트 상대 경로이며 상위 폴더·절대 경로·심볼릭 링크를 허용하지 않는다. 예시는 저장소 examples/theme.example.json을 참고한다.

## iOS

```sh
python scripts/theme_tools.py pack-ios --project ./work/my-theme
```

ios/ 안의 CSS 한 파일과 Images/*.png를 루트 구조 그대로 .ktheme에 넣는다. CSS에서 참조한 PNG가 실제로 있는지, ZIP 구조가 정상인지 확인한다. 기존 출력 파일은 덮어쓰지 않는다. 새 버전은 새 작업 폴더 또는 theme.json의 새 출력 경로로 만든다.

이 명령은 CSS의 모든 스타일 의미나 현재 카카오톡과의 호환성을 검사하지 않는다. 실제 적용 확인은 별도다.

## Android

설치된 JDK와 Android SDK Build Tools·Platform, 본인 서명키가 필요하다. 버전 값은 실제 설치한 도구와 현재 배포 요건에 맞춘다. 아래 35와 35.0.0은 명령 형태를 설명하는 예시다.

```sh
python scripts/build_android.py --project ./work/my-theme --sdk /path/to/android-sdk --api 35 --build-tools 35.0.0 --java-home /path/to/jdk --keystore /private/path/theme-signing.p12 --alias my-theme
```

Windows에서도 같은 옵션에 본인 PC의 경로를 넣는다. 공백이 있는 경로는 따옴표로 감싼다. THEME_STORE_PASSWORD를 해당 프로세스 환경에 준비하고, 키 비밀번호가 다르면 THEME_KEY_PASSWORD도 설정한다. 비밀번호를 명령 인수·문서·저장소에 쓰지 않는다. 서명키를 자동으로 새로 만들거나 배포 중인 앱의 키를 교체하지 않는다.

빌더는 AAPT2 → javac → D8 → zipalign → apksigner 순서로 실행한다. APK 서명, 정렬, 패키지를 검증하고 qa/android-signature.json과 android-badging.txt를 남긴다. 단순 Java Activity와 리소스 프로젝트만 지원한다. Kotlin, AndroidX, Gradle 플러그인 의존성이 있는 프로젝트는 해당 프로젝트의 정상 빌드를 사용한다.

[Android SDK 안내](https://developer.android.com/studio), [AAPT2](https://developer.android.com/tools/aapt2), [apksigner](https://developer.android.com/tools/apksigner)를 참고한다. SDK와 JDK의 설치·사용 조건은 각 배포처를 따른다.

## 검사와 구매용 ZIP

```sh
python scripts/theme_tools.py check --project ./work/my-theme
python scripts/theme_tools.py package --project ./work/my-theme
```

check는 파일 경로, 해시, 압축 구조, PNG 헤더·크기, 안내서 유무를 검사한다. PNG 전체 디코딩, 텍스트 가독성, 캐릭터 배치와 APK 서명은 이 명령의 자동 검사 범위가 아니다. 이미지를 직접 열고 Android 서명 검사를 별도로 수행해야 한다.

package는 dist/<slug>-bundle.zip과 bundle-manifest.json을 만든다. ZIP에는 설치 파일과 안내서만 들어가며 미리보기는 별도 파일로 유지된다. 원화·소스·서명키는 포함하지 않는다. manifest의 checks는 자동 검사와 별도 검수 범위를 구분한다.

이미 완성한 .ktheme·APK·미리보기가 있으면 theme.json에 해당 프로젝트 내부 상대 경로를 지정해 check와 package부터 사용할 수 있다.
