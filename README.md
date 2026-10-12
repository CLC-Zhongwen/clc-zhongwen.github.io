# 중문 작문 노트

한국어나 서툰 중국어 문장을 넣으면 회화체(口语)나 서면어(书面语)로 다듬어 주는 중국어 작문 코치예요.
교정 이유, 병음, 핵심 어휘와 HSK 급수, 문법 설명, 다른 문체로 쓴 문장도 함께 보여 줍니다.

**공개 주소**: https://clc-zhongwen.github.io/
**AI 서버**: https://cwn-coach-api.cwn-coach-api.workers.dev (상태 확인: `/api/health`)

```
[학생 브라우저]  ── 문장·문체·학습자 정보 ──▶  [Cloudflare Worker (무료)]  ── 프롬프트 + API 키 ──▶  [Gemini API (무료 등급)]
 GitHub Pages(무료)                              키 보관, 요청 제한, 입력 검사
 기록은 localStorage
```

| 폴더·파일 | 역할 |
|---|---|
| `index.html` | 웹앱 화면 전체 (작문 · 기록 · 설정) |
| `config.js` | AI 서버(Worker) 주소 설정 |
| `worker/src/index.js` | AI 서버. Gemini 호출, 프롬프트, 요청 제한, 오류 안내 |
| `worker/wrangler.toml` | Worker 설정 (허용 사이트, 모델, 분당 요청 제한) |
| `tests/` | 로컬 모의 서버와 Worker 단위 테스트 |
| `legacy/` | claude.ai 아티팩트로 만들었던 이전 버전 (참고용) |

---

## 1. Gemini API 키 만들기 (무료 등급)

1. https://aistudio.google.com/apikey 에 들어가서 Google 계정으로 로그인해요. Gemini API 약관상 만 18세 이상이어야 해요.
2. **Create API key**를 누르고 새 프로젝트를 만들면 키가 생겨요. 키는 어디에도 붙여 넣지 말고 3단계에서만 써요.
3. **결제(Billing)는 연결하지 마세요.** 결제 계정이 연결되지 않은 프로젝트만 무료 등급으로 동작해요.
   - 결제를 연결하면 그 프로젝트는 유료 등급으로 바뀌어 사용량만큼 요금이 나가요.
   - 무료 한도를 다 쓰면 유료로 넘어가지 않고 오류(429)만 나요. 앱에는 "오늘 무료 사용량이 소진됐어요"라고 표시돼요.
4. https://aistudio.google.com/rate-limit 에서 이 프로젝트의 모델별 무료 한도(분당·하루 요청 수)를 확인해요.
   - 공식 문서에는 무료 한도 숫자가 따로 나와 있지 않고 AI Studio에서만 보여요.

## 2. Cloudflare Worker 배포 (AI 서버, 무료 플랜)

PC에 [Node.js LTS](https://nodejs.org/)를 먼저 설치해요.

```bash
cd worker
npx wrangler login
```

브라우저가 열리면 Cloudflare 계정으로 로그인하고 허용을 눌러요. 계정이 없으면 무료로 가입해요.

`worker/wrangler.toml`의 `ALLOWED_ORIGINS`에 웹앱 주소(현재 `https://clc-zhongwen.github.io`)가 들어 있는지 확인해요. 그다음 아래 명령을 차례로 실행해요.

```bash
npx wrangler deploy
```

```bash
npx wrangler secret put GEMINI_API_KEY
```

두 번째 명령은 키를 물어보는데, 1단계에서 만든 키를 붙여 넣으면 돼요. 키는 Cloudflare에 비밀값으로만 저장되고 코드나 GitHub에는 남지 않아요.

- **명령 대신 대시보드로 등록해도 돼요** (현재 배포는 이 방법을 썼어요): Workers & Pages → cwn-coach-api → Settings → Variables and Secrets → Add → Type **Secret**, 이름 `GEMINI_API_KEY`.
- **로그인 권한을 최소로 하고 싶으면**: `npx wrangler login --scopes account:read user:read workers:write workers_scripts:write workers_tail:read`. 이 권한으로 `deploy`와 `tail`(로그 보기)은 되지만, `secret put`은 전체 권한으로 다시 로그인하라고 요구해요. 그래서 키는 대시보드로 등록해요.
- `wrangler.toml`의 `[placement] region = "gcp:asia-northeast3"` 설정은 지우지 마세요.
  - 이 설정이 없으면 한국 접속이 홍콩 데이터센터에서 처리될 수 있어요.
  - 홍콩은 Gemini API 이용 불가 지역이라 `User location is not supported` 오류가 나요. 실제 배포 중에 이 오류를 겪었어요.

배포가 끝나면 `https://cwn-coach-api.<계정이름>.workers.dev` 같은 주소가 나와요. 이 주소 뒤에 `/api/health`를 붙여 브라우저로 열었을 때 `{"ok":true,"configured":true}`가 나오면 키 설정까지 끝난 거예요.

## 3. GitHub Pages 배포 (웹앱 화면, 무료)

1. `config.js`의 `apiUrl`에 2단계의 Worker 주소를 넣어요. 예) `apiUrl: "https://cwn-coach-api.seunggi.workers.dev"`
2. GitHub에 **공개(Public)** 저장소를 만들고 이 폴더 전체를 올려요.
   - 무료 GitHub 계정의 Pages는 공개 저장소에서만 쓸 수 있어요.
   - API 키는 저장소에 없으니 공개해도 괜찮아요.
3. 저장소의 **Settings → Pages**로 가서 **Branch: main / (root)**를 고르고 저장해요.
4. 1~2분 뒤 `https://<아이디>.github.io/<저장소이름>/`이 열리면, 그 주소를 학과 분들께 공유하면 돼요.

## 4. 로컬에서 테스트하기 (AI 호출 없음)

```bash
python tests/mock_server.py
```

- 앱: http://localhost:8000 — 가짜 AI 응답으로 화면 흐름을 확인할 수 있어요. 문장에 `#quota`, `#busy`, `#down`, `#broken`을 넣으면 각 오류 상황을 흉내 내요.
- Worker 단위 테스트: http://localhost:8000/tests/worker-test.html — Gemini 응답 모양의 가짜 데이터로 Worker 코드를 실행해요.

실제 Gemini로 로컬 테스트를 하려면 `worker/.dev.vars.example`을 `.dev.vars`로 복사해서 키를 넣고, `worker` 폴더에서 `npx wrangler dev`를 실행해요. 그다음 `config.js`의 `apiUrl`을 `http://localhost:8787`로 바꿔요.

---

## 무료로 쓸 수 있는 범위와 한계 (2026-10-12 공식 문서 기준)

**Gemini API 무료 등급** — [가격](https://ai.google.dev/gemini-api/docs/pricing) · [한도](https://ai.google.dev/gemini-api/docs/rate-limits) · [약관](https://ai.google.dev/gemini-api/terms)
- 이 앱이 쓰는 `gemini-3.5-flash-lite`(기본), `gemini-3.1-flash-lite`(1차 대체), `gemini-3.8-flash`(2차 대체)는 가격표에 무료 등급이 있다고 나와 있어요. 체험판이나 일회성 크레딧이 아니에요.
- **실제 확인한 한도(2026-10-12)**: `gemini-3.8-flash`는 무료 등급이 **하루 20회**라서(Gemini 오류 메시지로 확인) 기본 모델에서 뺐어요. `gemini-3.6-flash`는 "수요 과다(503)" 응답이 잦아서 제외했어요. flash-lite 계열의 하루 한도 숫자는 아직 확인하지 못했어요. https://aistudio.google.com/rate-limit 에서 확인하세요.
- 한도는 **키 하나가 아니라 프로젝트 하나 기준**이라, 모든 사용자가 같은 한도를 나눠 써요.
  - 하루 요청 수(RPD)는 미국 태평양 시간 자정, 즉 한국 시간 오후 4시(여름) 또는 5시(겨울)에 초기화돼요.
  - 정확한 숫자는 AI Studio에서만 볼 수 있고, Google이 공지 없이 바꿀 수 있어요.
- **AI Studio 화면 기준 무료 한도(2026-10-12)**: 분당 요청 수(RPM)는 3.5·3.1 Flash Lite가 15, 3.8·3.6 Flash가 5예요. 분당 토큰은 250K예요. 하루 요청 수(RPD)는 3.8 Flash만 20으로 확인됐어요(오류 메시지).
- **자동 전환**: 기본 모델이 429(분당·하루 한도)나 503(수요 과다)으로 실패하면, `GEMINI_FALLBACK_MODEL`에 적힌 순서대로 다음 모델을 시도해요. 한도에 걸린 모델은 잠시(분당 한도 30초, 하루 한도 10분) 건너뛰어요. 이 기억은 Worker 인스턴스마다 따로라 항상 적용되지는 않아요.
- 실제 확인: 3.8 Flash를 기본으로 두고 하루 한도가 찬 상태에서 요청하니, 429 다음에 3.1 Flash Lite로 넘어가 정상 응답했어요(11.6초, 17.4초).
- **데이터 처리**:
  - 무료 등급에서는 입력과 답변이 Google 제품 개선에 쓰이고, 사람 검토자가 읽을 수 있어요.
  - 약관은 무료 서비스에 민감한 정보나 개인정보를 넣지 말라고 안내해요. 그래서 앱 입력창 아래에 이 안내를 표시해 두었어요.
  - Worker는 `store: false`로 요청해서, Gemini 쪽에 대화가 나중에 다시 불러올 수 있는 형태로 보관되지 않게 해요. 다만 이것과 별개로 위의 제품 개선 사용은 그대로 적용돼요.
- **약관상 주의**:
  - 만 18세 이상만 쓸 수 있어요. 대학 학과 구성원이 대상이면 대부분 해당돼요.
  - 약관에 "consumer use가 아닌 professional/business 목적"이라는 문구가 있어요. 학과 학습용 공개 앱이 여기에 해당하는지는 약관만으로는 분명하지 않아요.
  - EEA·영국·스위스 사용자에게는 유료 서비스만 쓸 수 있다는 제한이 있어요. 한국은 이용 가능 지역 목록에 있어요.

**Cloudflare Workers 무료 플랜** — [가격](https://developers.cloudflare.com/workers/platform/pricing/) · [한도](https://developers.cloudflare.com/workers/platform/limits/)
- 하루 100,000건까지 요청할 수 있어요. 초과하면 요금이 나가지 않고 오류 1027이 나요.
- 요청 한 번에 CPU 10ms까지 쓸 수 있는데, Gemini 응답을 기다리는 시간은 이 CPU 시간에 들어가지 않아요.
- 실제로는 Gemini 무료 한도가 Worker 한도보다 훨씬 먼저 차요.
- 분당 요청 제한(같은 IP에서 60초에 5회)은 Cloudflare Rate Limiting 바인딩을 써요.
  - 무료 플랜에서 배포와 동작을 실제로 확인했어요(2026-10-12).
  - 공식 문서 설명대로 대략적으로 계산돼요. 실제 테스트에서는 연속 요청 몇 번이 더 통과한 뒤부터 429로 막혔어요.
  - 학교 와이파이처럼 여러 명이 같은 IP를 쓰면 함께 제한될 수 있어요.
- 문제가 생기면 `worker` 폴더에서 `npx wrangler tail cwn-coach-api`를 실행해요. Gemini 오류 코드와 메시지가 실시간으로 보여요(키는 로그에 남지 않아요).

**GitHub Pages**: 정적 사이트라 비용이 없어요. 무료 계정은 공개 저장소에서만 쓸 수 있어요.

**학습 기록(localStorage)**
- 기기와 브라우저마다 따로 저장돼요. 브라우저 데이터를 지우거나 시크릿 창을 쓰면 사라져요.
- 다른 사람에게는 보이지 않아요.

## 공개 링크에서의 남용 방지

- **프롬프트는 서버에만 있어요.** 브라우저는 문장, 문체, 정해진 선택지(신분·학년 등)만 보내기 때문에, Worker 주소를 범용 AI 창구로 쓸 수 없어요.
- **입력 길이 제한**: 한 번에 300자까지 받아요. 화면과 서버 양쪽에서 검사해요.
- **사이트 제한**: `ALLOWED_ORIGINS`에 적은 사이트에서 온 브라우저 요청만 받아요.
  - 이건 다른 웹사이트가 이 Worker를 끌어다 쓰는 걸 막는 장치예요.
  - 직접 만든 프로그램(curl 등)까지 막지는 못해요. 그런 요청은 분당 제한과 Gemini 무료 한도에서 막혀요.
- **자동 유료 전환 없음**: Gemini 프로젝트에 결제를 연결하지 않는 한 유료 호출이 생길 수 없어요. Worker는 결제 관련 설정을 하지 않아요.

## 점검 기록 (2026-10-12)

**응답 속도**: 같은 문장, HSK 4·6급 각 3회, 공개 Worker 기준 측정이에요.
- 수정 전(3.8-flash 기본 → flash-lite 보조): 전체 5.7~15.4초. 3.8-flash가 한도 초과나 수요 과다로 실패한 뒤 보조 모델로 넘어가는 시간이 더해졌어요.
- 수정 후(flash-lite 기본): 전체 5.3~6.5초, 이 중 Gemini 처리가 4.8~6.0초예요. 병목은 Gemini 생성 시간이고, Worker와 네트워크는 0.3~0.5초예요.

**HSK 수준**: 프롬프트에 수준별 방침을 넣어서, 4급은 기초 규칙 중심, 6급은 대안 표현과 뉘앙스 중심으로 vocab·grammar가 달라지게 했어요.
- 어휘의 HSK 급수 표시는 AI의 추정이라 틀릴 수 있어요. 예를 들어 天气预报를 4급이나 5급으로 표시해요.

**보안**
- API 키는 Cloudflare Secret에만 있어요. 저장소의 Git 기록 전체, 공개 사이트, Worker 응답 어디에서도 키 문자열이 발견되지 않았어요.
- 다른 사이트나 출처 없이 온 요청은 403, 4000바이트를 넘는 요청은 400, 301자 이상 입력은 400으로 거부해요.
- IP당 1분 5회, 전체 1분 30회로 제한해요. 둘 다 대략적인 제한이에요.
- Worker 로그에는 Gemini 오류 코드와 메시지만 남아요. 입력 문장과 키는 남지 않아요.
- 화면에 넣는 AI 응답과 저장된 기록은 모두 HTML 이스케이프해요. 보안 정책(CSP)으로 외부 스크립트와 외부 전송 주소를 제한해요.
- `Origin` 검사는 브라우저에만 효과가 있어요. curl 같은 직접 호출은 Origin을 꾸며서 보낼 수 있어서, 이런 호출은 요청 제한과 Gemini 무료 한도(결제 미연결)로만 막혀요.

**주소 변경**
- 공개 주소를 `https://clc-zhongwen.github.io/`(GitHub 조직 `CLC-Zhongwen`)로 옮겼어요.
- 이전 주소 `seunggih633-netizen.github.io/chinese-writing-note/`는 404가 나요. GitHub Pages는 저장소를 옮겨도 이전 주소를 자동으로 연결해 주지 않아요.
- Worker는 새 주소만 허용해요.

**측정 도구**: `tests/live_bench.py`로 다시 측정할 수 있어요.
- 모델을 바꿔 가며 비교하려면 Worker에 `DEBUG_TOKEN` 비밀값을 임시로 넣어야 해요(현재는 지워져 있어서 기능이 꺼져 있어요).
- 실제 Gemini 한도를 쓰니 꼭 필요할 때만 실행하세요.

## 사용자가 늘어나면

1. **하루 한도가 자주 소진될 때**
   - 보조 모델을 한도가 더 큰 Flash-Lite 계열로 바꾸거나, 기본 모델을 Flash-Lite로 바꿔요(`wrangler.toml`).
   - 그래도 부족하면 Gemini 유료 등급(결제 연결, AI Studio에서 월 지출 상한 설정 가능)이나 다른 무료 API를 검토해요. 이때는 운영비 0원 원칙을 다시 정해야 해요.
2. **기기 간 기록 동기화가 필요할 때**: 로그인과 DB(예: Cloudflare D1 무료 플랜)를 붙여야 해요. 개인정보 관리 책임도 같이 생겨요.
3. **사람별 사용량을 공정하게 나누고 싶을 때**: 학과 공용 접속 코드나 간단한 로그인을 Worker에 추가해요.
