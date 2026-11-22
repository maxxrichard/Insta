import pytest

from igbot.client import InstagramBot, InstagramError


class FakeResponse:
    def __init__(self, body, status=200):
        self._body, self.status_code = body, status

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)


def make_bot(responses):
    session = FakeSession([FakeResponse(*r) if isinstance(r, tuple) else FakeResponse(r) for r in responses])
    return InstagramBot("42", "tok", session=session, sleep=lambda s: None), session


def test_post_photo_runs_container_poll_publish():
    bot, session = make_bot([
        {"id": "c1"},
        {"status_code": "IN_PROGRESS"},
        {"status_code": "FINISHED"},
        {"id": "m1"},
        {"permalink": "https://www.instagram.com/p/abc/"},
    ])
    assert bot.post_photo("https://x/y.jpg", "hi") == ("m1", "https://www.instagram.com/p/abc/")
    calls = [(m, u) for m, u, _ in session.calls]
    assert calls[0] == ("POST", "https://graph.instagram.com/42/media")
    assert calls[3] == ("POST", "https://graph.instagram.com/42/media_publish")
    assert session.calls[0][2]["data"] == {"image_url": "https://x/y.jpg", "caption": "hi"}
    assert session.calls[3][2]["data"] == {"creation_id": "c1"}
    for _, url, kwargs in session.calls:
        assert "tok" not in url
        assert kwargs["headers"]["Authorization"] == "Bearer tok"


def test_failed_container_is_not_published():
    bot, session = make_bot([{"id": "c1"}, {"status_code": "ERROR"}])
    with pytest.raises(InstagramError, match="ERROR"):
        bot.post_photo("https://x/y.jpg")
    assert len(session.calls) == 2


def test_container_timeout():
    bot, _ = make_bot([{"id": "c1"}] + [{"status_code": "IN_PROGRESS"}] * 10)
    with pytest.raises(InstagramError, match="not ready"):
        bot.post_photo("https://x/y.jpg")


def test_api_error_does_not_leak_token():
    bot, _ = make_bot([({"error": {"code": 190, "message": "expired"}}, 400)])
    with pytest.raises(InstagramError) as exc:
        bot.post_photo("https://x/y.jpg")
    assert "190" in str(exc.value) and "tok" not in str(exc.value)
