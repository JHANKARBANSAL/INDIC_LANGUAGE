"""
Sarvam AI Cloud Client & Wrapper for IndicSQL.
Connects to Sarvam AI official endpoints for:
- Speech-to-Text (Saaras:v1 with automatic Indian language identification)
- Text-to-Speech (Bulbul:v1 with native Indic accents)
- Language Translation & Transliteration (Mayura:v1)
- Chat Completion & Dialect Normalization (Sarvam-2B)
"""

import base64
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx

from indicsql.core.config import settings

logger = logging.getLogger(__name__)


class SarvamAPIError(Exception):
    """Raised when an error occurs during communication with Sarvam AI API."""

    pass


class SarvamClient:
    """
    Client wrapper for Sarvam AI Sovereign Indic API.
    Gracefully handles missing keys and provides fallback diagnostics.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.sarvam.ai",
        timeout: float = 30.0,
    ):
        self.api_key = api_key or settings.sarvam_api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        """Returns True if a Sarvam API subscription key is configured."""
        return bool(self.api_key and self.api_key.strip())

    def _get_headers(self) -> Dict[str, str]:
        if not self.is_configured:
            raise SarvamAPIError(
                "SARVAM_API_KEY is not set. Please set it in your .env or pass api_key to SarvamClient."
            )
        return {
            "api-subscription-key": self.api_key.strip(),
        }

    # -------------------------------------------------------------------------
    # 1. Speech-to-Text (Saaras:v1) — Auto Language Detection
    # -------------------------------------------------------------------------
    def speech_to_text(
        self,
        audio_data: Union[bytes, Path, str],
        filename: str = "audio.wav",
        language_code: Optional[str] = "unknown",
        model: str = "saaras:v1",
        with_diacritics: bool = False,
    ) -> Dict[str, Any]:
        """
        Transcribes spoken Indic audio into text.
        By default uses language_code='unknown' to automatically identify
        the spoken Indian language (Hindi, Marathi, Bengali, Tamil, Telugu, etc.).
        """
        if not self.is_configured:
            raise SarvamAPIError("SARVAM_API_KEY not configured.")

        # Read bytes if audio_data is a file path
        if isinstance(audio_data, (str, Path)):
            path = Path(audio_data)
            if not path.exists():
                raise FileNotFoundError(f"Audio file not found: {path}")
            filename = path.name
            with open(path, "rb") as f:
                content = f.read()
        else:
            content = audio_data

        url = f"{self.base_url}/speech-to-text"
        headers = self._get_headers()
        files = {
            "file": (filename, content, "audio/wav"),
        }
        data: Dict[str, Any] = {
            "model": model,
            "with_diacritics": str(with_diacritics).lower(),
        }
        if language_code:
            data["language_code"] = language_code

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, files=files, data=data)
                response.raise_for_status()
                result = response.json()
                return {
                    "transcript": result.get("transcript", ""),
                    "detected_language": result.get("language_code", language_code or "unknown"),
                    "raw_response": result,
                }
        except httpx.HTTPStatusError as e:
            logger.error(f"Sarvam STT HTTP error {e.response.status_code}: {e.response.text}")
            raise SarvamAPIError(f"Sarvam STT failed: {e.response.text}") from e
        except Exception as e:
            logger.error(f"Sarvam STT request failed: {e}")
            raise SarvamAPIError(f"Sarvam STT error: {e}") from e

    # -------------------------------------------------------------------------
    # 2. Text-to-Speech (Bulbul:v1) — Vernacular Audio Synthesis
    # -------------------------------------------------------------------------
    def text_to_speech(
        self,
        text: str,
        target_language_code: str = "hi-IN",
        speaker: str = "meera",
        model: str = "bulbul:v1",
        pace: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Synthesizes natural Indic speech from text using Sarvam Bulbul model.
        Returns base64 audio string and metadata.
        """
        if not self.is_configured:
            raise SarvamAPIError("SARVAM_API_KEY not configured.")

        url = f"{self.base_url}/text-to-speech"
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"

        payload = {
            "inputs": [text],
            "target_language_code": target_language_code,
            "speaker": speaker,
            "pitch": 0,
            "pace": pace,
            "loudness": 1.5,
            "speech_sample_rate": 8000,
            "enable_preprocessing": True,
            "model": model,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                audios = result.get("audios", [])
                audio_base64 = audios[0] if audios else None
                return {
                    "audio_base64": audio_base64,
                    "target_language_code": target_language_code,
                    "speaker": speaker,
                }
        except httpx.HTTPStatusError as e:
            logger.error(f"Sarvam TTS HTTP error {e.response.status_code}: {e.response.text}")
            raise SarvamAPIError(f"Sarvam TTS failed: {e.response.text}") from e
        except Exception as e:
            logger.error(f"Sarvam TTS request failed: {e}")
            raise SarvamAPIError(f"Sarvam TTS error: {e}") from e

    # -------------------------------------------------------------------------
    # 3. Translation & Transliteration (Mayura:v1)
    # -------------------------------------------------------------------------
    def translate(
        self,
        text: str,
        source_language_code: str = "auto",
        target_language_code: str = "en-IN",
        model: str = "mayura:v1",
        mode: str = "formal",
    ) -> Dict[str, Any]:
        """
        Translates or normalizes regional Indic queries into canonical English/Indic concepts.
        """
        if not self.is_configured:
            raise SarvamAPIError("SARVAM_API_KEY not configured.")

        url = f"{self.base_url}/translate"
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"

        payload = {
            "input": text,
            "source_language_code": source_language_code,
            "target_language_code": target_language_code,
            "speaker_gender": "Female",
            "mode": mode,
            "model": model,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                return {
                    "translated_text": result.get("translated_text", ""),
                    "source_language_code": source_language_code,
                    "target_language_code": target_language_code,
                }
        except httpx.HTTPStatusError as e:
            logger.error(f"Sarvam Translate error {e.response.status_code}: {e.response.text}")
            raise SarvamAPIError(f"Sarvam Translate failed: {e.response.text}") from e
        except Exception as e:
            logger.error(f"Sarvam Translate request failed: {e}")
            raise SarvamAPIError(f"Sarvam Translate error: {e}") from e

    # -------------------------------------------------------------------------
    # 4. Chat Completion & Normalization (Sarvam-2B / OpenAI Compatible)
    # -------------------------------------------------------------------------
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "sarvam-2b",
        temperature: float = 0.2,
        max_tokens: int = 256,
    ) -> str:
        """
        Calls Sarvam completion endpoint for dialectal normalization and reasoning.
        """
        if not self.is_configured:
            raise SarvamAPIError("SARVAM_API_KEY not configured.")

        url = f"{self.base_url}/v1/chat/completions"
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
        except httpx.HTTPStatusError as e:
            logger.error(f"Sarvam Chat error {e.response.status_code}: {e.response.text}")
            raise SarvamAPIError(f"Sarvam Chat failed: {e.response.text}") from e
        except Exception as e:
            logger.error(f"Sarvam Chat request failed: {e}")
            raise SarvamAPIError(f"Sarvam Chat error: {e}") from e

