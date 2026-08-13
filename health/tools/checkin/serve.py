"""深夜 check-in 點選介面的極小後端。

- GET  /            → index.html
- POST /submit      → 寫入 submissions/YYYY-MM-DD.json 並在 stdout 印一行 SUBMIT

只綁 127.0.0.1，不對外。
"""

import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "submissions")
PORT = int(os.environ.get("CHECKIN_PORT", "8901"))


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/plain; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            with open(os.path.join(BASE, "index.html"), encoding="utf-8") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        else:
            self._send(404, "not found")

    def do_POST(self):
        if self.path.split("?")[0] != "/submit":
            self._send(404, "not found")
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self._send(400, "bad json")
            return

        payload["submitted_at"] = datetime.now().isoformat(timespec="seconds")
        date = str(payload.get("date") or datetime.now().strftime("%Y-%m-%d"))[:10]
        os.makedirs(OUT, exist_ok=True)
        target = os.path.join(OUT, date + ".json")
        with open(target, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        print("SUBMIT " + target, flush=True)
        self._send(200, json.dumps({"ok": True}), "application/json; charset=utf-8")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    # 必須是 ThreadingHTTPServer：瀏覽器的 preconnect 會開一條閒置連線，
    # 單執行緒版會被它卡住 accept 迴圈，導致後續 POST 逾時（前端顯示「送出失敗」）。
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
