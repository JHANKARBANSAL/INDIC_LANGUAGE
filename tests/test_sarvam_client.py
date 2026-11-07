"""
Unit tests for SarvamClient wrapper.
Tests STT, TTS, Translation, and Chat completion with mocked network responses.
"""

from unittest.mock import MagicMock, patch
import pytest

from indicsql.models.sarvam_client import SarvamAPIError, SarvamClient


def test_sarvam_client_unconfigured():
    client = SarvamClient(api_key=None)
    assert not client.is_configured
    with pytest.raises(SarvamAPIError, match="not configured|not set"):
        client.speech_to_text(b"fake_audio")


def test_sarvam_client_configured():
    client = SarvamClient(api_key="test_api_key_123")
    assert client.is_configured
    assert client._get_headers()["api-subscription-key"] == "test_api_key_123"


@patch("httpx.Client.post")
def test_sarvam_speech_to_text_mocked(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "transcript": "महाराष्ट्रात कापूस पिकाचे उत्पादन किती झाले?",
        "language_code": "mr-IN",
    }
    mock_post.return_value = mock_response

    client = SarvamClient(api_key="test_key")
    res = client.speech_to_text(b"dummy_bytes", filename="test.wav")

    assert res["transcript"] == "महाराष्ट्रात कापूस पिकाचे उत्पादन किती झाले?"
    assert res["detected_language"] == "mr-IN"
    assert mock_post.called


@patch("httpx.Client.post")
def test_sarvam_text_to_speech_mocked(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "audios": ["UklGRigAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="]
    }
    mock_post.return_value = mock_response

    client = SarvamClient(api_key="test_key")
    res = client.text_to_speech("किसान योजना", target_language_code="hi-IN")

    assert res["audio_base64"] is not None
    assert res["target_language_code"] == "hi-IN"


@patch("httpx.Client.post")
def test_sarvam_translate_mocked(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "translated_text": "What is the crop production in Maharashtra?"
    }
    mock_post.return_value = mock_response

    client = SarvamClient(api_key="test_key")
    res = client.translate("महाराष्ट्रात पीक उत्पादन किती?", target_language_code="en-IN")

    assert res["translated_text"] == "What is the crop production in Maharashtra?"


@patch("httpx.Client.post")
def test_sarvam_chat_completion_mocked(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": "Canonical query: Total farmer beneficiaries in Pune"}}
        ]
    }
    mock_post.return_value = mock_response

    client = SarvamClient(api_key="test_key")
    out = client.chat_completion([{"role": "user", "content": "Pune farmers"}])

    assert "Total farmer beneficiaries in Pune" in out

