"""로컬 화면 테스트용 모의 서버 (실제 AI를 부르지 않음).

    python -I tests/mock_server.py      -> http://localhost:8000

프로젝트 폴더의 정적 파일을 그대로 보여주고, POST /api/coach 는 Worker와 같은 형식의 가짜 응답을 돌려준다.
입력 문장에 아래 단어를 넣으면 오류 상황을 흉내 낸다.
  #quota  무료 일일 한도 소진     #busy  요청 과다(분당 제한)
  #down   AI 서버 연결 실패        #broken 형식이 깨진 답변
"""
import json
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_INPUT = 300

ERRORS = {
    "#quota": (429, "daily_quota", "오늘 쓸 수 있는 무료 AI 사용량이 모두 소진됐어요. 매일 오후 4~5시(한국 시간)에 다시 채워져요."),
    "#busy": (429, "rate_limited", "요청이 너무 잦아요. 1분쯤 뒤에 다시 눌러 주세요."),
    "#down": (502, "upstream", "AI 서버와 연결이 잠깐 끊겼어요. 다시 눌러 주세요."),
}

SAMPLE = {
    "inputType": "mixed",
    "intentKo": "내일 수업 끝나고 도서관에서 같이 공부하자.",
    "final": {
        "tokens": [{"h": "明天", "p": "míngtiān"}, {"h": "下课", "p": "xiàkè"}, {"h": "以后", "p": "yǐhòu"}, {"h": "，", "p": ""},
                   {"h": "我们", "p": "wǒmen"}, {"h": "一起", "p": "yìqǐ"}, {"h": "去", "p": "qù"}, {"h": "图书馆", "p": "túshūguǎn"},
                   {"h": "学习", "p": "xuéxí"}, {"h": "吧", "p": "ba"}, {"h": "！", "p": ""}],
        "hanzi": "明天下课以后，我们一起去图书馆学习吧！",
        "pinyin": "Míngtiān xiàkè yǐhòu, wǒmen yìqǐ qù túshūguǎn xuéxí ba!",
    },
    "score": 75,
    "summary": "(모의 응답) 뜻은 통해요. 장소를 동사 앞에 두는 어순만 기억하세요.",
    "corrections": [{"kind": "어순", "from": "学习在图书馆", "to": "去图书馆学习", "why": "장소는 동사 앞에 옵니다."}],
    "vocab": [{"h": "下课", "p": "xiàkè", "hsk": "2", "ko": "수업이 끝나다", "tip": "下课以后 = 수업 끝나고"},
              {"h": "图书馆", "p": "túshūguǎn", "hsk": "2", "ko": "도서관", "tip": "去图书馆 + 동사"}],
    "grammar": [{"pattern": "…吧", "why": "제안·권유의 어기조사", "ex": "我们走吧。", "exP": "Wǒmen zǒu ba.", "exKo": "우리 가자."}],
    "otherRegister": {"hanzi": "明日课后，望与您一同前往图书馆学习。", "pinyin": "Míngrì kèhòu, wàng yǔ nín yìtóng qiánwǎng túshūguǎn xuéxí.", "note": "서면어는 明日·前往·一同을 써요."},
}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def send_json(self, status, body):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/api/coach":
            return self.send_json(404, {"error": {"code": "not_found", "message": "없는 주소예요."}})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except ValueError:
            return self.send_json(400, {"error": {"code": "bad_request", "message": "요청 형식이 올바르지 않아요."}})
        text = str(body.get("text", "")).strip()
        print("coach request:", json.dumps({"text": text, "mode": body.get("mode"), "profile": body.get("profile")}, ensure_ascii=False), file=sys.stderr)
        if not text:
            return self.send_json(400, {"error": {"code": "empty_input", "message": "문장을 먼저 적어 주세요."}})
        if len(text) > MAX_INPUT:
            return self.send_json(400, {"error": {"code": "input_too_long", "message": f"한 번에 {MAX_INPUT}자까지 넣을 수 있어요. 한두 문장씩 나눠 주세요."}})
        time.sleep(1.5)
        for tag, (status, code, msg) in ERRORS.items():
            if tag in text:
                return self.send_json(status, {"error": {"code": code, "message": msg}})
        if "#broken" in text:
            return self.send_json(200, {"result": {"final": {}}})
        return self.send_json(200, {"result": SAMPLE, "model": "mock"})


if __name__ == "__main__":
    print("http://localhost:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
