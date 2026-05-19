from __future__ import annotations

import sys
import time
import urllib.request


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: wait_for_url.py URL TIMEOUT_SECONDS [LABEL]")
        return 2

    url = sys.argv[1]
    timeout = int(sys.argv[2])
    label = sys.argv[3] if len(sys.argv) > 3 else url
    started = time.monotonic()
    last_log = -15

    while True:
        elapsed = int(time.monotonic() - started)
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                if 200 <= response.status < 300:
                    print(f"{label} is ready after {elapsed}s.")
                    return 0
        except Exception:
            pass

        if elapsed - last_log >= 15:
            print(f"Waiting for {label}... {elapsed}/{timeout}s")
            last_log = elapsed

        if elapsed >= timeout:
            print(f"Timed out waiting for {label} after {timeout}s.")
            return 1

        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
