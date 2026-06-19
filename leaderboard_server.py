import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

LEADERBOARD_FILE = "leaderboard.json"
HOST = "0.0.0.0"
PORT = 8000


def sort_entries(data):
    if not isinstance(data, list):
        return []
    return sorted(
        data,
        key=lambda item: (item.get("score", 0), item.get("accuracy", 0)),
        reverse=True,
    )[:10]


def load_data():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                return sort_entries(json.load(f))
        except Exception:
            return []
    return []


def save_data(data):
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(sort_entries(data), f, ensure_ascii=False, indent=2)


class LeaderboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/":
            self.send_error(404, "Not Found")
            return

        data = load_data()
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/":
            self.send_error(404, "Not Found")
            return

        length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(length)

        try:
            data = json.loads(payload.decode("utf-8"))
            if isinstance(data, list):
                entries = data
            elif isinstance(data, dict):
                entries = [data]
            else:
                entries = []
            current = load_data()
            current.extend(entries)
            save_data(current)
            response = json.dumps(load_data()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)
        except Exception:
            self.send_error(400, "Invalid JSON payload")

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), LeaderboardHandler)
    print(f"Leaderboard server running on http://{HOST}:{PORT}")
    server.serve_forever()
