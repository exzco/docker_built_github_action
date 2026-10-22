import os
import socket
import threading
import uuid
import queue
import json as _json
import urllib.parse

HOST = "0.0.0.0"
PORT = 5000

FLAG = os.environ.get("GZCTF_FLAG", "flag{！！！联系管理员！！！}")
APP_ORIGIN = os.environ.get("APP_ORIGIN", "http://127.0.0.1:5000")

STORE = {}
MAX_BODY = 64 * 1024

HOME = """<!doctype html>
<html><head><meta charset="utf-8"><title>图床</title>
<style>body{font-family:system-ui,monospace;background:#111;color:#eee;padding:2em}
code{background:#222;padding:.1em .4em;border-radius:3px} td{border:1px solid #333;padding:4px 8px}</style>
</head><body>
<h1>图床</h1>
<p>接口:<code>POST /note </code>上传图片</p>
<p><code>GET /view?id=&amp;trace= </code>访问图片</p>
<p><code>POST /report</code>管理员检验文件是否合规</p>
<p>排查图片显示问题时,可在 <code>/view</code> 链接的 <code>trace</code> 参数附带追踪标记，将其发送给后端人员。</p>
</body></html>"""

# 限制排队队列大小，防止恶意刷爆内存
bot_queue = queue.Queue(maxsize=30)


def recv_request(conn):
    """读取一个 HTTP 请求,返回 (method, path, headers_dict, body_bytes)。"""
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = conn.recv(4096)
        if not chunk:
            break
        buf += chunk
        if len(buf) > 1_000_000:
            break
    head, _, rest = buf.partition(b"\r\n\r\n")
    lines = head.split(b"\r\n")
    req_line = lines[0].decode("latin1") if lines else ""
    headers = {}
    for l in lines[1:]:
        if b":" in l:
            k, _, v = l.partition(b":")
            headers[k.decode("latin1").strip().lower()] = v.decode("latin1").strip()
    body = rest
    try:
        cl = int(headers.get("content-length", "0") or "0")
    except ValueError:
        cl = 0
    while len(body) < cl:
        chunk = conn.recv(4096)
        if not chunk:
            break
        body += chunk
    parts = req_line.split(" ")
    method = parts[0] if parts else ""
    path = parts[1] if len(parts) > 1 else ""
    return method, path, headers, body


def build_response(status, header_list, body_bytes):
    out = ("HTTP/1.1 %s\r\n" % status).encode("latin1")
    for k, v in header_list:
        out += ("%s: %s\r\n" % (k, v)).encode("latin1")
    out += b"\r\n"
    out += body_bytes
    return out


def send(conn, raw):
    try:
        conn.sendall(raw)
    except Exception:
        pass


def send_json(conn, obj):
    data = _json.dumps(obj).encode()
    send(conn, build_response("200 OK", [
        ("Content-Type", "application/json"),
        ("X-Content-Type-Options", "nosniff"),
        ("Content-Length", str(len(data))),
        ("Connection", "close"),
    ], data))


def same_origin(url):
    if "\\" in url or any(c in url for c in " \t\r\n\x00"):
        return False
    o = urllib.parse.urlparse(APP_ORIGIN)
    u = urllib.parse.urlparse(url)
    if u.scheme != o.scheme or u.hostname != o.hostname:
        return False

    def eff_port(x):
        return x.port or (443 if x.scheme == "https" else 80)

    return eff_port(u) == eff_port(o)


def handle(method, path, headers, body, conn):
    parsed = urllib.parse.urlparse(path)
    q = urllib.parse.parse_qs(parsed.query)
    p = parsed.path

    if method == "GET" and p == "/":
        data = HOME.encode()
        send(conn, build_response("200 OK", [
            ("Content-Type", "text/html; charset=utf-8"),
            ("X-Content-Type-Options", "nosniff"),
            ("Content-Length", str(len(data))),
            ("Connection", "close"),
        ], data))
        return

    if method == "POST" and p == "/note":
        data = body
        if not data:
            send_json(conn, {"code": 400, "msg": "empty body"})
            return
        if len(data) > MAX_BODY:
            send_json(conn, {"code": 400, "msg": "too large"})
            return
        nid = uuid.uuid4().hex
        STORE[nid] = data
        send_json(conn, {"code": 200, "data": nid})
        return

    if method == "GET" and p == "/view":
        nid = (q.get("id") or [""])[0]
        trace = (q.get("trace") or [""])[0]
        data = STORE.get(nid, b"")
        send(conn, build_response("200 OK", [
            ("X-Trace", trace),
            ("Content-Type", "image/png"),
            ("X-Content-Type-Options", "nosniff"),
            ("Content-Length", str(len(data))),
            ("Connection", "close"),
        ], data))
        return

    if method == "POST" and p == "/report":
        try:
            payload = _json.loads(body.decode() or "{}")
        except Exception:
            payload = {}
        url = payload.get("url", "")
        if not same_origin(url):
            send_json(conn, {"code": 400, "msg": "bad url: admin only visits %s" % APP_ORIGIN})
            return
        try:
            bot_queue.put_nowait(url)
            send_json(conn, {"code": 200, "msg": "admin will visit your link shortly"})
        except queue.Full:
            send_json(conn, {"code": 429, "msg": "bot queue is full, please try again later"})
        return

    data = b"not found\n"
    send(conn, build_response("404 Not Found", [
        ("Content-Type", "text/plain"),
        ("X-Content-Type-Options", "nosniff"),
        ("Content-Length", str(len(data))),
        ("Connection", "close"),
    ], data))


def bot_worker_loop():
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        print("[bot] init error (is playwright installed?):", e)
        return

    chromium_args = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-default-apps",
        "--disable-sync",
        "--disable-translate",
        "--mute-audio",
        "--no-zygote",
        "--js-flags=--max-old-space-size=128",
    ]

    while True:
        try:
            with sync_playwright() as p:
                browser = None
                for channel in (None, "chrome", "msedge"):
                    try:
                        browser = p.chromium.launch(
                            headless=True,
                            args=chromium_args,
                            channel=channel,
                        )
                        print("[bot] using browser:", channel or "bundled chromium")
                        break
                    except Exception:
                        continue

                if browser is None:
                    print("[bot] no browser available, retrying in 10s...")
                    threading.Event().wait(10)
                    continue

                visit_count = 0
                while True:
                    url = bot_queue.get()
                    ctx = None
                    try:
                        ctx = browser.new_context(
                            ignore_https_errors=True,
                            java_script_enabled=True,
                        )
                        ctx.add_cookies([
                            {"name": "GZCTF_FLAG", "value": FLAG, "url": APP_ORIGIN + "/"},
                        ])
                        page = ctx.new_page()
                        try:
                            print(f"[bot] visiting: {url}")
                            page.goto(url, timeout=8000, wait_until="load")
                            page.wait_for_timeout(3000)
                        except Exception as e:
                            print("[bot] visit error:", e)
                        finally:
                            try:
                                page.close()
                            except Exception:
                                pass
                    finally:
                        if ctx is not None:
                            try:
                                ctx.close()
                            except Exception:
                                pass
                        bot_queue.task_done()

                    visit_count += 1
                    if visit_count >= 50:
                        print("[bot] recycling browser to reclaim memory...")
                        try:
                            browser.close()
                        except Exception:
                            pass
                        break
        except Exception as e:
            print("[bot] worker loop crashed, restarting...", e)
            threading.Event().wait(3)


def serve_conn(conn, addr):
    try:
        method, path, headers, body = recv_request(conn)
        handle(method, path, headers, body, conn)
    except Exception as e:
        print("[server] error:", e)
    finally:
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        conn.close()


def main():
    if "GZCTF_FLAG" not in os.environ:
        print("[!!] 未设置 GZCTF_FLAG 环境变量")

    threading.Thread(target=bot_worker_loop, daemon=True).start()
    print("[*] Admin Bot Worker started")

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(64)
    print("[*] SniffSocket listening on %s:%d" % (HOST, PORT))
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=serve_conn, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
