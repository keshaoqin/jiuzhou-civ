#!/usr/bin/env python3
"""Local development server for 九州 (threaded, no dependencies)."""
from __future__ import annotations

import argparse
import http.server
import os
import socketserver
from pathlib import Path


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8767)
    args = ap.parse_args()
    root = Path(__file__).resolve().parent / "web"
    os.chdir(root)
    with Server(("127.0.0.1", args.port), Handler) as httpd:
        print(f"九州 · 中国文明地图  →  http://127.0.0.1:{args.port}")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
