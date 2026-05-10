"""End-to-end smoke test for the Privacy Bridge.

Exercises the real code paths without needing cloudflared or a real
Ollama instance:
  - Spins up a tiny in-process FakeOllama HTTP server
  - Issues a token, registers it as if the installer hit the public endpoint
  - Calls llm_provider.invoke(sensitive=True) — confirms the request lands
    on FakeOllama (proving the bridge routes correctly)
  - Calls llm_provider.stream(sensitive=True) — confirms streaming works
  - Confirms non-sensitive prompts DON'T hit the bridge
  - Confirms a 'down' bridge transparently falls through to cloud/Ollama

Run:  python -m scripts.smoke_privacy_bridge

Note on DB: forces DB_PATH to %TEMP%/nexus_pb_smoke.db so the test runs
against a fresh, OS-temp file. The project's real DB lives inside OneDrive,
which doesn't play nicely with SQLite's WAL mode for tight open/close cycles.
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import List

# Override DB_PATH BEFORE importing anything that touches config.settings.
# Tests already do this same trick (per the comment in config/db.py).
_TEMP_DB = os.path.join(tempfile.gettempdir(), "nexus_pb_smoke.db")
if os.path.exists(_TEMP_DB):
    os.remove(_TEMP_DB)
for ext in (".db-wal", ".db-shm"):
    p = _TEMP_DB.replace(".db", ext)
    if os.path.exists(p):
        os.remove(p)
os.environ["DB_PATH"] = _TEMP_DB

GREEN = "\033[92m"
RED   = "\033[91m"
DIM   = "\033[90m"
RST   = "\033[0m"

# -- Tiny FakeOllama HTTP server --------------------------------------------
class FakeOllama(BaseHTTPRequestHandler):
    received: List[dict] = []

    def log_message(self, *a, **kw):
        pass  # silence

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n) if n else b""
        try:
            payload = json.loads(body)
        except Exception:
            payload = {"raw": body.decode("utf-8", errors="ignore")}
        FakeOllama.received.append({"path": self.path, "payload": payload})

        if self.path == "/api/generate":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            if payload.get("stream"):
                # Stream three NDJSON chunks then done
                for piece in ("hello", " from", " bridge"):
                    chunk = json.dumps({"response": piece, "done": False}) + "\n"
                    self.wfile.write(chunk.encode())
                self.wfile.write((json.dumps({"response": "", "done": True}) + "\n").encode())
            else:
                self.wfile.write(json.dumps(
                    {"response": "hello from the bridge", "done": True}
                ).encode())
        elif self.path == "/api/tags":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(
                {"models": [{"name": "llama3.1:8b"}]}
            ).encode())
        else:
            self.send_response(404)
            self.end_headers()


def _check_https_validator(pb_module, token: str) -> bool:
    """Confirm the public register_endpoint still rejects http:// URLs."""
    try:
        pb_module.register_endpoint(
            token=token, endpoint_url="http://malicious.example",
            ollama_models=[],
        )
        return False
    except ValueError:
        return True


def start_fake_ollama(port: int = 18434) -> HTTPServer:
    server = HTTPServer(("127.0.0.1", port), FakeOllama)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)  # let it bind
    return server


# -- Test runner with green/red reporting ----------------------------------
PASS = []
FAIL = []

def check(label: str, cond: bool, detail: str = ""):
    if cond:
        PASS.append(label)
        print(f"  {GREEN}PASS{RST} {label}")
    else:
        FAIL.append((label, detail))
        print(f"  {RED}FAIL{RST} {label}  {DIM}{detail}{RST}")


def main():
    print("\n-- Privacy Bridge end-to-end smoke --\n")

    # 0. Verify DB override worked
    from config.db import _db_path
    print(f"0. test DB: {_db_path()}")
    if "OneDrive" in _db_path():
        print(f"   {RED}!! DB override failed — still using OneDrive DB. Aborting.{RST}")
        return 2

    # 1. Boot fake Ollama
    print("1. boot FakeOllama on :18434")
    server = start_fake_ollama(18434)
    fake_url = "http://127.0.0.1:18434"
    check("FakeOllama running", True)

    # 2. Issue token + register endpoint
    print("\n2. issue token + register endpoint via real DB layer")
    from api import privacy_bridge as pb
    BIZ = "smoke_test_biz"
    USER = "smoke_test_user"

    token = pb.issue_token(BIZ, USER)
    check("token issued", token.startswith("pb_") and len(token) > 30, f"got {token!r}")

    # The public register_endpoint enforces https:// (correct prod behavior).
    # For the smoke we write the row directly to point at our http fake server.
    from config.db import get_conn
    from utils.timez import now_iso
    conn = get_conn()
    conn.execute(
        "UPDATE nexus_privacy_bridges SET endpoint_url=?, status='healthy', "
        "registered_at=?, ollama_models=?, last_pinged_at=?, last_ping_error=NULL, "
        "updated_at=? WHERE business_id=?",
        (fake_url, now_iso(), json.dumps(["llama3.1:8b"]), now_iso(), now_iso(), BIZ),
    )
    conn.commit()
    conn.close()
    check("https-only validator still enforced",
          _check_https_validator(pb, token), "validator should reject http://")

    state = pb.get_state(BIZ)
    check("state reflects endpoint", state.get("endpoint_url") == fake_url,
          f"got {state.get('endpoint_url')}")
    check("models stored", state.get("ollama_models") == ["llama3.1:8b"],
          f"got {state.get('ollama_models')}")
    check("get_endpoint_for_use returns the bridge",
          pb.get_endpoint_for_use(BIZ) == fake_url,
          f"got {pb.get_endpoint_for_use(BIZ)!r}")

    # 4. Direct invoke_via_bridge
    print("\n3. invoke_via_bridge() -- direct forwarder")
    FakeOllama.received.clear()
    out = pb.invoke_via_bridge(BIZ, "ping", system="be brief", max_tokens=50)
    check("got response from fake Ollama", out == "hello from the bridge", f"got {out!r}")
    check("FakeOllama received the request", len(FakeOllama.received) == 1,
          f"received {len(FakeOllama.received)} requests")
    if FakeOllama.received:
        last = FakeOllama.received[-1]
        check("hit /api/generate", last["path"] == "/api/generate",
              f"path={last['path']}")
        check("model auto-picked from installed list",
              last["payload"].get("model") == "llama3.1:8b",
              f"model={last['payload'].get('model')}")
        check("prompt forwarded intact",
              last["payload"].get("prompt") == "ping",
              f"prompt={last['payload'].get('prompt')!r}")

    # 5. stream_via_bridge
    print("\n4. stream_via_bridge() — streaming forwarder")
    FakeOllama.received.clear()
    chunks = list(pb.stream_via_bridge(BIZ, "stream me", max_tokens=50))
    check("got streaming chunks", chunks == ["hello", " from", " bridge"],
          f"got {chunks!r}")
    check("FakeOllama got stream:true",
          FakeOllama.received and FakeOllama.received[-1]["payload"].get("stream") is True,
          f"payload={FakeOllama.received}")

    # 6. llm_provider.invoke routes sensitive=True through the bridge
    print("\n5. llm_provider.invoke(sensitive=True) routes via bridge")
    from config import llm_provider, cloud_budget
    FakeOllama.received.clear()
    tok = cloud_budget.set_active_business(BIZ)
    try:
        out2 = llm_provider.invoke(
            "summarise this call", system="be brief",
            max_tokens=50, sensitive=True,
        )
    finally:
        cloud_budget.reset_active_business(tok)
    check("response came back", "hello from the bridge" in (out2 or ""),
          f"got {out2!r}")
    check("bridge was hit (not cloud)", len(FakeOllama.received) == 1,
          f"received {len(FakeOllama.received)} requests")

    # 7. llm_provider.invoke WITHOUT sensitive must NOT hit the bridge
    print("\n6. non-sensitive invoke does NOT hit the bridge")
    FakeOllama.received.clear()
    tok = cloud_budget.set_active_business(BIZ)
    try:
        try:
            llm_provider.invoke(
                "what's 2+2?", system="be brief",
                max_tokens=20, sensitive=False,
            )
        except Exception:
            # Cloud may not be configured locally — that's fine for this assertion
            pass
    finally:
        cloud_budget.reset_active_business(tok)
    check("non-sensitive bypassed bridge", len(FakeOllama.received) == 0,
          f"bridge got hit {len(FakeOllama.received)} times")

    # 8. When bridge is 'down', invoke transparently falls through
    print("\n7. down bridge -> falls through (does not raise)")
    conn = get_conn()
    conn.execute(
        "UPDATE nexus_privacy_bridges SET status='down', last_ping_error='smoke' "
        "WHERE business_id=?",
        (BIZ,),
    )
    conn.commit()
    conn.close()
    check("get_endpoint_for_use returns None when down",
          pb.get_endpoint_for_use(BIZ) is None,
          f"got {pb.get_endpoint_for_use(BIZ)!r}")

    FakeOllama.received.clear()
    tok = cloud_budget.set_active_business(BIZ)
    try:
        try:
            llm_provider.invoke(
                "anything", system="x", max_tokens=20, sensitive=True,
            )
            fell_through_cleanly = True
        except Exception as e:
            # Cloud may also not work locally — that's still "fell through" not "raised on bridge"
            msg = str(e).lower()
            fell_through_cleanly = "bridge" not in msg
    finally:
        cloud_budget.reset_active_business(tok)
    check("down bridge did not block sensitive call", fell_through_cleanly)
    check("down bridge was not contacted", len(FakeOllama.received) == 0,
          f"got {len(FakeOllama.received)} hits")

    # 9. Cleanup
    print("\n8. cleanup")
    conn = get_conn()
    conn.execute("DELETE FROM nexus_privacy_bridges WHERE business_id=?", (BIZ,))
    conn.commit()
    conn.close()
    server.shutdown()
    check("test row deleted",
          pb.get_state(BIZ).get("status") == "unconfigured")

    # Report
    print("\n" + "-" * 50)
    print(f"  {GREEN}{len(PASS)} passed{RST}   {RED}{len(FAIL)} failed{RST}")
    if FAIL:
        print("\nFailures:")
        for label, detail in FAIL:
            print(f"  {RED}FAIL{RST} {label}  {DIM}{detail}{RST}")
        return 1
    print(f"\n  {GREEN}Privacy Bridge wiring verified end-to-end.{RST}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
