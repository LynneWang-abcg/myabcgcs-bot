import pytest

from app.translator import TranslationResult, translate_to_simplified_chinese


class FakeClient:
    def __init__(self):
        self.calls = []

    async def get(self, url, params, timeout):
        self.calls.append((url, params, timeout))
        return FakeResponse(
            {
                "responseData": {"translatedText": "客户无法登录。"},
                "responseStatus": 200,
            }
        )


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_translate_to_simplified_chinese_uses_mymemory():
    client = FakeClient()

    result = await translate_to_simplified_chinese("Customer cannot log in.", client=client)

    assert result == TranslationResult(text="客户无法登录。", source_language="auto")
    assert client.calls[0][1]["langpair"] == "auto|zh-CN"
