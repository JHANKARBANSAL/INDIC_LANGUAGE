"""
IndicSQL Fine-Tuning & Training Module.
Provides synthetic corpus curation and fine-tuning harness for Sarvam-2B and Qwen-2.5-Coder.
"""

from indicsql.training.dataset_curator import DatasetCurator, TrainingRecord

__all__ = ["DatasetCurator", "TrainingRecord"]
