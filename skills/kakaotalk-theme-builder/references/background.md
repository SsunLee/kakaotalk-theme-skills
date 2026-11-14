# 배경 패턴과 배경 이미지

이 스킬의 테마는 **귀여움이 핵심**이다. 배경은 단색을 기본값으로 두지 않는다. 핀터레스트에서 "귀여운 배경"을 찾았을 때 나오는 느낌을 기준으로 삼는다. 파스텔 톤, 동글동글한 물방울, 흩뿌린 하트·별·반짝이·꽃, 몽글몽글한 구름 하늘, 동화책 같은 일러스트, 캐릭터 얼굴을 작은 스티커처럼 흩뿌린 패턴이 그 예다.

사용자가 배경을 정했으면 그대로 따른다. 정하지 않았으면 캐릭터의 색·성격에 맞는 프리셋을 2~3개 골라 카탈로그(아래 `--catalog`)로 보여 주고 고르게 한다. 선택은 작업 기록에 남기고 빌드마다 바꾸지 않는다. 사용자가 미니멀하게 해 달라고 하면 그때 단색이나 옅은 체크를 쓴다.

## 귀여운 프리셋

| preset | 느낌 | 어울리는 캐릭터·테마 |
|---|---|---|
| pastel-polka | 크림 바탕에 분홍·노랑·하늘·연두 물방울 | 거의 모든 캐릭터. 무난하고 사랑스러움 |
| dreamy-sky | 분홍→보라→하늘 그라데이션, 흰 구름, 반짝이·별 | 꿈꾸는·동화적인 테마, 양·토끼·유니콘 느낌 |
| candy-hearts | 연분홍 바탕에 흩날리는 하트와 반짝이 | 러블리·고백·커플, 분홍 캐릭터 |
| flower-meadow | 연두 바탕에 작은 꽃과 꽃가루 | 봄·피크닉, 토끼·병아리·곰 |
| starry-night | 남보라 밤하늘, 노란 별·달·반짝이 | 검정 고양이·부엉이, 잠·꿈 테마. 글자색은 밝게 |
| picnic-hearts | 분홍 깅엄 체크에 하트 | 강아지·빵·소풍 |
| storybook-confetti | 아이보리 바탕에 파스텔 색종이(점·별·하트·고리) | 동화책·문구·생일 |
| cream-check-sparkle | 크림 바둑판에 금빛 반짝이 | 흑백·모노톤 캐릭터, 레트로 |

프리셋 색은 캐릭터 색에 맞춰 덮어쓸 수 있다. 캐릭터 몸 색이나 볼터치 색을 가져와 명도를 높이고 채도를 낮추는 것이 기본이다.

## 더 귀엽게: 캐릭터 스티커와 동화 일러스트

- **캐릭터 스티커 흩뿌리기**: scatter 레이어의 shape에 `image:<경로>`를 쓰면 이번 테마의 캐릭터 얼굴·발자국·소품 PNG를 하트·별과 함께 흩뿌린다. 투명도 0.15~0.3, 크기 7~12pt, 기울기 ±15°에서 시작한다. 탭 아이콘이나 말풍선과 같은 원화를 쓰면 테마 전체가 하나로 묶인다.
- **동화 같은 일러스트**: 수채화·색연필 질감, 손그림 느낌은 도형 패턴으로 표현하기 어렵다. 이미지 생성 도구로 만든 그림을 `image` 레이어로 쓴다. 생성 도구가 없으면 프리셋으로 만들고 일러스트는 생성하지 못했다고 알린다.

이미지 생성 요청 예시:

> 카카오톡 채팅방 배경용 세로 일러스트(9:18)를 그려 주세요. 파스텔 분홍·하늘·크림 톤의 동화책 같은 수채화 느낌입니다. 몽글몽글한 구름, 작은 별과 반짝이, 작은 꽃이 화면 가장자리와 위아래에 흩어져 있고, 가운데는 넓고 비어 있어 말풍선과 글자가 잘 보여야 합니다. 글자, 사람, 로고, 실제 캐릭터 상표는 넣지 마세요.

> 귀여운 손그림 패턴 배경을 그려 주세요. 크림색 바탕에 작은 하트·별·물방울·리본 낙서가 고르게 흩어져 있고 선이 둥글고 부드럽습니다. 대비가 약한 파스텔 색만 쓰고 글자는 넣지 마세요.

생성한 그림은 투명도나 `soften`으로 한 단계 옅게 만들어 쓴다. 다른 작가의 배경화면이나 핀터레스트 이미지를 그대로 가져오지 않는다. 분위기를 참고해 새로 만든다.

## 읽기 쉬움

채팅방 배경 위에는 이름·시간·날짜 글자가 바로 올라간다. 무늬는 작고 옅게, 배경 두 색의 대비는 약하게 한다. 밝은 배경에는 진한 글자색, starry-night 같은 어두운 배경에는 밝은 글자색을 CSS와 Android 색상 리소스에 함께 지정한다. 말풍선이 흰색이면 배경은 살짝 색이 있어야 말풍선 외곽이 보인다. 채팅방용 일러스트는 가운데를 비운다.

## 도구로 만들기

카카오톡은 배경 이미지를 반복하지 않고 화면에 맞춰 자른다. iOS는 상단 중앙 기준으로 자른다. 그래서 패턴도 작은 타일이 아니라 화면 크기 이미지로 렌더링한다. 흩뿌리기 배치는 가로 중앙 기준의 고정 좌표에서 seed로 만들어 iOS와 Android에서 같은 그림이 된다.

```sh
python scripts/background_pattern.py --catalog <작업폴더>/qa/cute-presets.png   # 프리셋 한눈에 보기
python scripts/background_pattern.py --list-presets
python scripts/background_pattern.py --spec background.json --project <작업폴더> [--preview-only]
```

`background.json` 예시(크기 단위 pt):

```json
{
  "chatroom": {"preset": "dreamy-sky"},
  "main": {"text_color": "#8A5E6B", "layers": [
    {"type": "solid", "color": "#FFF1F5"},
    {"type": "scatter", "seed": 21, "spacing": 44, "shapes": [
      {"shape": "image:art/face@3x.png", "size": [7, 10], "opacity": 0.2, "tilt": 12},
      {"shape": "heart", "colors": ["#FFB3C7", "#FFD3DE"], "size": [3, 5], "weight": 2, "tilt": 20}]}]},
  "passcode": {"preset": "starry-night", "soften": 0.1}
}
```

- 대상마다 `preset`(프리셋 + 덮어쓰기), `layers`(직접 쌓기) 중 하나를 쓴다. 공통 옵션은 `text_color`(대비 검사용 글자색), `soften`(0~1, 흰 막으로 옅게), `soften_color`다.
- 레이어 `type`
  - `solid`: `color`
  - `gradient`: 위→아래 `colors`
  - `checker`, `gingham`, `stripes`, `grid`: `color`, `color2`, `cell`, grid는 `line`
  - `dots`: 규칙적인 물방울. `colors`(여러 색 번갈아), `cell`, `dot`
  - `scatter`: 흩뿌리기. `seed`, `spacing`, `density`(0~1), `shapes`
  - `motif`: 하나의 그림을 엇갈려 반복
  - `image`: 일러스트를 화면에 맞춰 자름
  - 모든 레이어에 `opacity`를 쓸 수 있다.
- scatter의 `shapes` 항목: `shape`(dot·ring·heart·star·sparkle·flower·cloud·moon 또는 `image:<경로>`), `colors`, `size`(반지름 범위), `weight`(나올 비율), `opacity`, `tilt`(기울기 범위, 도). flower는 `center`로 꽃술 색을 정한다.
- 필요 없는 대상(chatroom·main·passcode)은 생략한다.

만드는 파일:

| 대상 | iOS | Android |
|---|---|---|
| chatroom | chatroomBgImage@3x·@2x (1125×2250, 750×1500) | theme_chatroom_background_image.png (1440×2880, xxhdpi·sw600dp-xxhdpi) |
| main | mainBgImage@3x·@2x | theme_background_image.png |
| passcode | passcodeBgImage@3x·@2x | theme_passcode_background_image.png (1440×1440) |

iOS CSS에는 `BackgroundStyle-ChatRoom`, `MainViewStyle-Primary`, `BackgroundStyle-Passcode`의 `-ios-background-image`에 같은 파일 이름을 지정하고, `background-color`를 배경의 주된 색으로 맞춘다. Android는 위 리소스 이름을 공식 샘플과 대조한다. 단색 shape XML(theme-adv의 theme_background_image.xml 등)이 같은 이름으로 있으면 어느 리소스가 쓰이는지 확인하고 의도한 쪽만 남긴다. 사용 중인 공식 샘플의 크기·파일 이름이 다르면 그 샘플을 우선한다.

## 검수

`qa/background-<대상>.png`와 `qa/background-report.json`을 직접 열어 확인한다. `worst_contrast`는 글자 크기(약 12pt) 단위로 평균 낸 배경 중 가장 밝은 쪽과 가장 어두운 쪽(극단 2% 제외)에 대한 `text_color`의 대비 중 작은 값이다. 3:1 미만이면 경고한다. 무늬를 옅게 하거나 `soften`을 올리거나 글자색을 바꾼다.

말풍선 미리보기를 배경 위에 놓고 확인한다. 귀여운지(무늬 크기·밀도·색 조화), 말풍선 외곽과 이름·시간·날짜가 무늬에 묻히지 않는지, 반복 무늬가 어지럽지 않은지 본다. 기종별 화면 비율에 따른 잘림·확대는 실제 기기에서 따로 확인한다.
