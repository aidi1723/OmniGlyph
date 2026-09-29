import os

from fastapi.testclient import TestClient

os.environ.setdefault("OMNIGLYPH_API_TOKEN", "test-token")

_original_test_client_init = TestClient.__init__


def _test_client_init(self, app, *args, **kwargs):
    headers = dict(kwargs.get("headers") or {})
    token = os.environ.get("OMNIGLYPH_API_TOKEN", "").strip()
    if token:
        headers.setdefault("Authorization", f"Bearer {token}")
    kwargs["headers"] = headers
    _original_test_client_init(self, app, *args, **kwargs)


TestClient.__init__ = _test_client_init
