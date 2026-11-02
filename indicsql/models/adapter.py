"""
IndicSQL Model Adapter Layer.
Provides lazy-loading LoRA inference abstractions with graceful heuristic fallback.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "lora_weights"


class ModelUnavailableError(Exception):
    """Raised when inference is attempted on a model adapter whose weights are unavailable."""

    pass


class ModelAdapter:
    """
    Manages lazy loading and text generation for a fine-tuned LoRA model.
    Falls back gracefully when weights are absent on disk.
    """

    def __init__(
        self,
        model_id: str,
        lora_path: Optional[Path] = None,
        device: str = "auto",
        max_length: int = 512,
    ):
        self.model_id = model_id
        self.lora_path = Path(lora_path) if lora_path else None
        self.device = device
        self.max_length = max_length
        self._model = None
        self._tokenizer = None

    @property
    def is_available(self) -> bool:
        """Returns True if fine-tuned adapter weights exist on local disk."""
        if not self.lora_path or not self.lora_path.exists():
            return False
        has_safetensors = (self.lora_path / "adapter_model.safetensors").exists()
        has_bin = (self.lora_path / "adapter_model.bin").exists()
        return has_safetensors or has_bin

    def load(self) -> None:
        """Lazily loads base model and attaches the fine-tuned LoRA adapter."""
        if self._model is not None:
            return

        if not self.is_available:
            raise ModelUnavailableError(
                f"Cannot load adapter for {self.model_id}: weights not found at {self.lora_path}"
            )

        try:
            import torch
            from peft import PeftModel
            from transformers import AutoModelForCausalLM, AutoTokenizer

            logger.info(f"Loading base model {self.model_id}...")
            self._tokenizer = AutoTokenizer.from_pretrained(
                str(self.lora_path), trust_remote_code=True
            )
            base_model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else "cpu",
                trust_remote_code=True,
            )
            logger.info(f"Attaching LoRA adapter from {self.lora_path}...")
            self._model = PeftModel.from_pretrained(base_model, str(self.lora_path))
            self._model.eval()
        except Exception as e:
            logger.error(f"Failed to load model adapter {self.model_id}: {e}")
            raise ModelUnavailableError(f"Failed loading weights: {e}") from e

    def generate(self, prompt: str, max_new_tokens: int = 256) -> str:
        """
        Runs text generation.
        Raises ModelUnavailableError if adapter weights are absent.
        """
        if not self.is_available:
            raise ModelUnavailableError(
                f"Model weights absent at {self.lora_path}. Use heuristic fallback."
            )

        self.load()

        import torch

        inputs = self._tokenizer(prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self._tokenizer.eos_token_id,
            )

        input_len = inputs["input_ids"].shape[1]
        decoded = self._tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
        return decoded.strip()


class SarvamAdapter(ModelAdapter):
    """Specialized adapter for Sarvam-2B transliteration and Indic query normalization."""

    def __init__(self, lora_path: Optional[Path] = None):
        if lora_path:
            target_path = Path(lora_path)
        elif (
            (DEFAULT_WEIGHTS_DIR / "sarvam_adapter" / "adapter_model.safetensors").exists()
            or (DEFAULT_WEIGHTS_DIR / "sarvam_adapter" / "adapter_model.bin").exists()
        ):
            target_path = DEFAULT_WEIGHTS_DIR / "sarvam_adapter"
        elif (
            (DEFAULT_WEIGHTS_DIR / "sarvam_transliteration" / "adapter_model.safetensors").exists()
            or (DEFAULT_WEIGHTS_DIR / "sarvam_transliteration" / "adapter_model.bin").exists()
        ):
            target_path = DEFAULT_WEIGHTS_DIR / "sarvam_transliteration"
        elif (DEFAULT_WEIGHTS_DIR / "sarvam_adapter").exists():
            target_path = DEFAULT_WEIGHTS_DIR / "sarvam_adapter"
        else:
            target_path = DEFAULT_WEIGHTS_DIR / "sarvam_transliteration"
        super().__init__(
            model_id="sarvamai/sarvam-2b",
            lora_path=target_path,
        )


class QwenAdapter(ModelAdapter):
    """Specialized adapter for Qwen-2.5-Coder-3B SQL synthesis."""

    def __init__(self, lora_path: Optional[Path] = None):
        if lora_path:
            target_path = Path(lora_path)
        elif (
            (DEFAULT_WEIGHTS_DIR / "qwen_adapter" / "adapter_model.safetensors").exists()
            or (DEFAULT_WEIGHTS_DIR / "qwen_adapter" / "adapter_model.bin").exists()
        ):
            target_path = DEFAULT_WEIGHTS_DIR / "qwen_adapter"
        elif (
            (DEFAULT_WEIGHTS_DIR / "qwen_3b_sql" / "adapter_model.safetensors").exists()
            or (DEFAULT_WEIGHTS_DIR / "qwen_3b_sql" / "adapter_model.bin").exists()
        ):
            target_path = DEFAULT_WEIGHTS_DIR / "qwen_3b_sql"
        elif (DEFAULT_WEIGHTS_DIR / "qwen_adapter").exists():
            target_path = DEFAULT_WEIGHTS_DIR / "qwen_adapter"
        else:
            target_path = DEFAULT_WEIGHTS_DIR / "qwen_3b_sql"
        super().__init__(
            model_id="Qwen/Qwen2.5-Coder-3B-Instruct",
            lora_path=target_path,
        )
