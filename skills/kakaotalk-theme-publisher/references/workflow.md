# 공통 등록 절차와 기록 도구

## 필요한 입력

완성된 테마의 bundle-manifest.json과 연결 파일, 대상 플랫폼, 본인 계정, 플랫폼별 가격·공개 범위, 사용자의 등록 요청을 확인한다. manifest의 경로는 manifest 파일이 있는 프로젝트를 기준으로 한다. 제작 스킬의 package 명령이 이 파일을 생성한다.

기존 파일을 직접 연결할 때도 다음 규격을 맞춘다.

- schema_version: 1.
- theme: slug, name, author, description, version, package, platforms.
- assets: role(ios/android/preview/guide), 프로젝트 상대 path, sha256 목록.
- bundle: 구매용 ZIP의 path, sha256, bytes.
- review: preview_kind(rendered/device_capture/mixed), kakaotalk_tested(boolean), notes.

## 등록 자료 준비

아래 명령은 설치된 업로드 스킬 폴더에서 실행한다. 계정·가격은 사용자가 지정한 값을 쓴다.

```sh
python scripts/release_tools.py prepare --bundle-manifest /path/to/theme/bundle-manifest.json --out /path/to/releases/littly-my-theme --platform littly --account MY_ACCOUNT --price 1000 --visibility buyers
python scripts/release_tools.py prepare --bundle-manifest /path/to/theme/bundle-manifest.json --out /path/to/releases/postype-my-theme --platform postype --account MY_ACCOUNT --price 0 --visibility subscribers
python scripts/release_tools.py prepare --bundle-manifest /path/to/theme/bundle-manifest.json --out /path/to/releases/onestore-my-theme --platform onestore --account MY_ACCOUNT --price 1000 --visibility buyers
```

위 가격은 사용법 예시이며 모든 테마의 기본 가격이 아니다. public·subscribers는 0원, buyers는 양수 가격이어야 한다. subscribers는 포스타입에만 사용한다. 리틀리·원스토어의 buyers는 유료 상품을 뜻한다.

prepare는 업로드 파일 복사본, listing.json, state.json, description.md, CHECKLIST.md를 만든다. 이미지 생성 방식·사용권·문의처·유료 구매 안내를 실제 상품에 맞게 보완한다. 원본 해시가 달라지면 준비를 중단한다. 이미 생성한 폴더는 덮어쓰지 않고 해당 폴더에서 이어간다.

## 브라우저 연결

현재 에이전트 환경에서 지원하는 브라우저 제어 도구를 사용한다. 특정 확장 프로그램·Orca·Chrome 포트·개인 계정을 필수로 가정하지 않는다. 정상 로그인으로 접근하고 세션 파일·쿠키·토큰을 다른 브라우저에서 추출해 복사하지 않는다.

도구가 없으면 파일 준비까지 완료하고 실제 업로드는 미실행으로 보고한다. 연결 오류는 인증 실패와 구분한다. 페이지에 들어가지 못했으면 로그인 성공이나 실패를 추정하지 않는다.

## 초안 ID와 최종 시도 기록

실제 화면에서 초안이 만들어진 것을 확인한 뒤 기록한다. URL·ID는 관찰한 값으로 바꾼다.

```sh
python scripts/release_tools.py bind --release /path/to/release --remote-id OBSERVED_ID --url https://platform.example/observed-product
python scripts/release_tools.py attempt --release /path/to/release --authorization "사용자가 지정한 이 플랫폼·상품·가격·공개 범위의 업로드 요청"
```

attempt가 성공한 뒤 최종 버튼을 한 번 누른다. 상태가 submit_attempted이면 같은 명령을 반복할 수 없다. 도구가 실제 클릭을 수행하는 것은 아니므로 에이전트는 기록과 화면 동작을 함께 관리해야 한다.

## 확인 근거

실제 상품 설정·공개 화면·심사 히스토리를 읽고 아래 내용으로 evidence.json을 작성한다. 사용자나 에이전트가 관찰한 근거를 저장하는 형식이며 스크립트 자체가 원격 서버를 조회하는 것은 아니다.

```json
{
  "platform": "postype",
  "account": "MY_ACCOUNT",
  "remote_id": "OBSERVED_ID",
  "url": "https://platform.example/observed-product",
  "price": 0,
  "visibility": "subscribers",
  "outcome": "published",
  "observed_at": "2026-10-17T12:00:00+09:00",
  "note": "같은 ID의 공개 설정과 첨부 파일을 재조회했습니다."
}
```

실제 관찰 시각과 실제 주소를 적는다. 위 주소는 실행용 사이트가 아닌 문서 예시다.

```sh
python scripts/release_tools.py confirm --release /path/to/release --evidence /path/to/evidence.json
python scripts/release_tools.py status --release /path/to/release
```

원스토어의 성공 outcome은 review_requested다. 판매 시작으로 기록하지 않는다. 파일이 변했거나 가격·계정·공개 범위·ID가 다르면 확인을 거부한다.

## 응답이 끊긴 경우

같은 remote_id의 실제 상태를 먼저 확인한다.

- 발행·심사가 접수되었으면 reconcile --outcome published 또는 review_requested로 성공 근거를 기록한다.
- 요청 히스토리가 없고 아직 초안임을 확인한 경우에만 reconcile --outcome not_submitted로 초안 상태를 복구한다. 이전 시도 기록은 남는다.
- 상태를 확인할 수 없으면 submit_attempted를 유지한다. 새 상품을 생성하거나 재클릭하지 않는다.

.release.lock이 남았다고 임의로 삭제하지 않는다. 이전 프로세스가 종료되었고 원격 상태까지 대조된 경우에만 복구한다.
