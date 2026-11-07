"""
IndicSQL Model & Adapter Subsystem.
"""

from indicsql.models.adapter import ModelAdapter, ModelUnavailableError, QwenAdapter, SarvamAdapter
from indicsql.models.combo import ComboResult, TriComboEngine
from indicsql.models.sarvam_client import SarvamAPIError, SarvamClient

__all__ = [
    "ModelAdapter",
    "ModelUnavailableError",
    "SarvamAdapter",
    "QwenAdapter",
    "ComboResult",
    "TriComboEngine",
    "SarvamClient",
    "SarvamAPIError",
]
