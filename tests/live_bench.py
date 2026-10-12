"""배포된 Worker로 실제 Gemini 응답 시간·내용을 측정하는 스크립트 (관리자용).

    python -I tests/live_bench.py <label> <결과.json> [model] [thinking]

- 같은 문장을 HSK 4급·6급 학생 프로필로 각각 3번씩 보낸다.
- 1분 5회 제한을 넘지 않도록 요청 사이에 13초씩 쉰다.
- model·thinking 을 바꿔 보려면 환경변수 CWN_DEBUG_TOKEN 에 Worker의 DEBUG_TOKEN 값을 넣는다(없으면 기본 설정으로만 측정).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = os.environ.get("CWN_API", "https://cwn-coach-api.cwn-coach-api.workers.dev/api/coach")
ORIGIN = os.environ.get("CWN_ORIGIN", "https://seunggih633-netizen.github.io")
TEXT = "这个周末我想跟朋友去爬山，但是天气预报说下雨了会，所以我们还没有决定了要不要去。"
PROFILES = {
    "HSK4": {"role": "학생", "grade": "2학년", "level": "중급 (HSK 4)"},
    "HSK6": {"role": "학생", "grade": "4학년", "level": "고급 (HSK 6)"},
}


def call(profile, mode, model, thinking):
    body = {"text": TEXT, "mode": mode, "profile": profile}
    headers = {"Content-Type": "application/json; charset=utf-8", "Origin": ORIGIN, "User-Agent": "cwn-live-bench/1.0"}
    token = os.environ.get("CWN_DEBUG_TOKEN")
    if token and (model or thinking):
        headers["X-Debug-Token"] = token
        if model:
            body["debugModel"] = model
        if thinking:
            body["debugThinking"] = thinking
    req = urllib.request.Request(API, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers=headers, method="POST")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=150) as r:
            status, timing, data = r.status, r.headers.get("Server-Timing", ""), json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        status, timing, data = e.code, e.headers.get("Server-Timing", ""), json.loads(e.read().decode("utf-8") or "{}")
    total = time.perf_counter() - t0
    gem = None
    if "gemini;dur=" in timing:
        gem = int(timing.split("gemini;dur=")[1].split(",")[0]) / 1000
    return {"status": status, "total_s": round(total, 2), "gemini_s": gem, "data": data}


def main():
    label, out = sys.argv[1], sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "-" else None
    thinking = sys.argv[4] if len(sys.argv) > 4 else None
    runs = int(os.environ.get("CWN_RUNS", "3"))
    levels = os.environ.get("CWN_LEVELS", "HSK4,HSK6").split(",")
    results = []
    first = True
    for i in range(runs):
        for lv in levels:
            if not first:
                time.sleep(13)
            first = False
            r = call(PROFILES[lv], "spoken", model, thinking)
            r.update({"label": label, "level": lv, "run": i + 1, "model": model or "default", "thinking": thinking or "default"})
            results.append(r)
            print(label, lv, i + 1, r["status"], "total", r["total_s"], "gemini", r["gemini_s"], flush=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
