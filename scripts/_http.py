"""Shared web access for the engine's scripts.

What it does (plain language): fetches a URL with certificate checking ON,
retries a few times when a server is busy (HTTP 429/5xx) or slow, and raises
FetchError when it finally fails, so a failed search can never be mistaken
for "nothing found". v1 switched certificate checks off; v2 does not.
"""
import json
import ssl
import time
import urllib.error
import urllib.request

UA = "research-intelligence-engine/2.0 (literature tool)"


class FetchError(Exception):
    pass


def _context():
    try:
        import certifi  # optional; fixes missing CA bundles on some Macs
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


_CTX = _context()
_last = [0.0]


def fetch(url, timeout=30, tries=4, min_interval=0.35, accept=None):
    """Return the response body as text, or raise FetchError."""
    headers = {"User-Agent": UA}
    if accept:
        headers["Accept"] = accept
    err = None
    for attempt in range(tries):
        wait = _last[0] + min_interval - time.time()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise FetchError("not found (HTTP 404)")
            err = f"HTTP {e.code}"
            if e.code not in (429, 500, 502, 503, 504):
                break
        except ssl.SSLError as e:
            raise FetchError(f"certificate check failed ({e}); try: pip install certifi")
        except Exception as e:  # timeouts, DNS, connection resets
            err = f"{type(e).__name__}: {e}"
        time.sleep(1.5 * (2 ** attempt))
    raise FetchError(err or "unknown error")


def fetch_json(url, **kw):
    text = fetch(url, accept="application/json", **kw)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise FetchError(f"server did not return valid JSON ({e})")
