import json
from backend.app import app


def test_index_route():
    client = app.test_client()
    res = client.get("/")
    assert res.status_code == 200
    assert b"AI Audio Generator" in res.data


def test_generate_audio_missing_text():
    client = app.test_client()
    res = client.post(
        "/generate-audio",
        data=json.dumps({}),
        content_type="application/json"
    )
    assert res.status_code == 400
