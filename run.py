#!/usr/bin/env python3
"""
TriLingua Bridge — PWA Launcher
=================================
Serves PWA manifest/service-worker alongside Streamlit with full HTTP + WebSocket proxy.

Usage:
    python run.py                 # PWA mode (port 8500 → proxies to Streamlit 8501)
    python run.py --direct        # Streamlit directly (no PWA)
    python run.py --port 3000     # Custom PWA port
    python run.py --no-browser    # Don't auto-open browser

What it does:
  - /manifest.json, /sw.js, /icon*.png|svg  → served from pwa/ directory
  - everything else (HTTP + WebSocket)       → proxied to Streamlit
"""

import os
import signal
import socket
import struct
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
import zlib
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingTCPServer

# ── Config ────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
PWA_DIR = ROOT / "pwa"
STREAMLIT_PORT = 8501
PROXY_PORT = 8500
STREAMLIT_CMD = [
    sys.executable,
    "-m",
    "streamlit",
    "run",
    str(ROOT / "app.py"),
    "--server.port",
    str(STREAMLIT_PORT),
    "--server.headless",
    "true",
]

PWA_FILES = {"manifest.json", "sw.js", "icon.svg", "icon-192.png", "icon-512.png"}

NO_BROWSER = "--no-browser" in sys.argv
for arg in sys.argv[:]:
    if arg.startswith("--port="):
        PROXY_PORT = int(arg.split("=", 1)[1])
    elif arg == "--direct" or arg == "--no-browser":
        pass  # handled elsewhere

streamlit_proc: subprocess.Popen | None = None


# ── Icon generation ───────────────────────────────────────────


def ensure_icons():
    """Generate PNG icons if missing."""
    for size in (192, 512):
        png_path = PWA_DIR / f"icon-{size}.png"
        if not png_path.exists():
            break
    else:
        return

    print("🔨 Generating PWA icons...")
    try:
        from pwa.gen_icons import main as gen

        gen()
    except Exception:
        for size in (192, 512):
            png_path = PWA_DIR / f"icon-{size}.png"
            if not png_path.exists():
                _make_placeholder_png(png_path, size)


def _make_placeholder_png(path: Path, size: int):
    raw = bytearray()
    for y in range(size):
        raw.append(0)
        for x in range(size):
            cx, cy = size / 2, size / 2
            r = size / 2 - 2
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if dist < r:
                raw.extend([37, 99, 235, 255])
            elif dist < r + 4:
                raw.extend([15, 23, 42, 255])
            else:
                raw.extend([245, 247, 251, 0])

    def chunk(ctype, data):
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw)))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)
    print(f"  ✓ {path.name} ({size}x{size})")


# ── Streamlit management ──────────────────────────────────────


def start_streamlit():
    global streamlit_proc
    print(f"  Starting Streamlit on port {STREAMLIT_PORT}...")
    streamlit_proc = subprocess.Popen(
        STREAMLIT_CMD,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(45):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{STREAMLIT_PORT}", timeout=2)
            print(f"  ✓ Streamlit ready on port {STREAMLIT_PORT}")
            return True
        except Exception:
            time.sleep(1)
    print("  ⚠ Streamlit may not have started. Check later.")
    return False


def stop_streamlit():
    global streamlit_proc
    if streamlit_proc and streamlit_proc.poll() is None:
        print("  Stopping Streamlit...")
        streamlit_proc.terminate()
        try:
            streamlit_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            streamlit_proc.kill()


# ── Combined TCP Proxy ────────────────────────────────────────
# Handles both HTTP and WebSocket on the same port.
# WebSocket connections are detected by the "Upgrade: websocket" header
# and tunneled via raw TCP to Streamlit.


class ProxyHandler(BaseHTTPRequestHandler):
    """Serves PWA files OR proxies HTTP/WebSocket to Streamlit."""

    # Disable default logging
    def log_message(self, fmt, *args):
        pass

    # ── Routing ─────────────────────────────────────
    def do_GET(self):
        path = self.path.split("?")[0].split("#")[0].lstrip("/")
        # Check for WebSocket upgrade (also handled in handle_one_request)
        if self.headers.get("Upgrade", "").lower() == "websocket":
            self._tunnel_websocket()
            return
        # Serve PWA static files directly
        if path in PWA_FILES:
            self._serve_pwa_file(path)
            return
        # Proxy to Streamlit
        self._proxy_http()

    def do_POST(self):
        self._proxy_http()

    def do_OPTIONS(self):
        self._proxy_http()

    # ── PWA file serving ────────────────────────────
    def _serve_pwa_file(self, path):
        file_path = PWA_DIR / path
        if not file_path.exists():
            self.send_error(404)
            return

        mime_map = {
            ".json": "application/json",
            ".js": "application/javascript",
            ".svg": "image/svg+xml",
            ".png": "image/png",
        }
        ext = file_path.suffix.lower()
        content_type = mime_map.get(ext, "application/octet-stream")

        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    # ── HTTP proxy ──────────────────────────────────
    def _proxy_http(self):
        method = self.command
        path = self.path
        body_bytes = None

        content_len = int(self.headers.get("Content-Length", 0))
        if content_len > 0:
            body_bytes = self.rfile.read(content_len)

        target_url = f"http://127.0.0.1:{STREAMLIT_PORT}{path}"
        try:
            req = urllib.request.Request(target_url, data=body_bytes, method=method)
            # Forward relevant headers
            for h in (
                "Cookie",
                "Accept",
                "Accept-Language",
                "Content-Type",
                "Origin",
                "Referer",
                "User-Agent",
                "X-Requested-With",
            ):
                if self.headers.get(h):
                    req.add_header(h, self.headers[h])

            with urllib.request.urlopen(req, timeout=60) as resp:
                self.send_response(resp.status)
                for key, val in resp.headers.items():
                    lk = key.lower()
                    if lk in (
                        "content-type",
                        "content-length",
                        "cache-control",
                        "set-cookie",
                        "location",
                        "x-accel-redirect",
                    ):
                        self.send_header(key, val)
                self.end_headers()
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            body = e.read() if hasattr(e, "read") else b""
            if body:
                self.wfile.write(body)
        except (urllib.error.URLError, ConnectionRefusedError):
            self._show_starting()

    def _show_starting(self):
        self.send_response(502)
        self.send_header("Content-Type", "text/html;charset=UTF-8")
        self.end_headers()
        msg = (
            "<html><body style='font-family:system-ui;padding:2rem;text-align:center'>"
            "<h2>&#127760; TriLingua Bridge</h2>"
            "<p>Streamlit is starting up... <a href='/'>Refresh</a></p>"
            "<script>setTimeout(()=>location.reload(),2000);</script>"
            "</body></html>"
        )
        self.wfile.write(msg.encode("utf-8"))

    # ── WebSocket tunneling ─────────────────────────
    def _tunnel_websocket(self):
        """Bidirectionally tunnel a WebSocket connection to Streamlit."""
        client = self.connection
        try:
            backend = socket.create_connection(("127.0.0.1", STREAMLIT_PORT), timeout=5)
        except Exception:
            self.send_error(502)
            return

        # Forward the original HTTP upgrade request to Streamlit
        raw_req = (
            f"{self.command} {self.path} {self.request_version}\r\n"
            + "".join(f"{k}: {v}\r\n" for k, v in self.headers.items())
            + "\r\n"
        )
        try:
            backend.sendall(raw_req.encode())
        except Exception:
            backend.close()
            return

        # Send 101 Switching Protocols back to client
        self.send_response(101)
        self.end_headers()

        # Bidirectional copy
        self._pipe_sockets(client, backend)

    def _pipe_sockets(self, client, backend):
        """Copy data bidirectionally between two sockets."""

        def forward(src, dst, name):
            try:
                while True:
                    data = src.recv(65536)
                    if not data:
                        break
                    dst.sendall(data)
            except Exception:
                pass
            finally:
                try:
                    dst.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    dst.close()
                except Exception:
                    pass

        t1 = threading.Thread(target=forward, args=(client, backend, "C→B"), daemon=True)
        t2 = threading.Thread(target=forward, args=(backend, client, "B→C"), daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

    # ── Disable default HTTP handling for WebSocket ─
    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, BrokenPipeError):
            pass


# ── Threaded PWA Server ───────────────────────────────────────


class ThreadedPWAServer(ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        super().server_bind()


# ── Main ──────────────────────────────────────────────────────


def main():
    if "--direct" in sys.argv:
        print("Starting Streamlit directly...")
        os.execvp(sys.executable, [sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py")])

    print()
    print("╔══════════════════════════════════════════╗")
    print("║   🌐  TriLingua Bridge  PWA v2.1       ║")
    print("║   Cross-cultural language coach          ║")
    print("╚══════════════════════════════════════════╝")
    print()

    ensure_icons()
    start_streamlit()

    server = ThreadedPWAServer(("0.0.0.0", PROXY_PORT), ProxyHandler)
    url = f"http://localhost:{PROXY_PORT}"

    print(f"  🌍  Open:  {url}")
    print("  📱  Install: Browser menu → Add to Home Screen")
    print("  ⏹   Ctrl+C to stop")
    print()

    if not NO_BROWSER:
        threading.Timer(2.0, lambda: webbrowser.open(url)).start()

    def shutdown(signum=None, frame=None):
        print("\n  Shutting down...")
        stop_streamlit()
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
