# IndicSQL Fine-Tuned LoRA Adapter Weights Directory

This directory stores the PEFT/LoRA adapter weights trained on the NDAP fine-tuning corpora:

1. **`models/lora_weights/qwen_adapter/`**
   - **Base Model**: `Qwen/Qwen2.5-Coder-3B-Instruct`
   - **Role**: Domain-specific SQL Synthesizer (DDL + Table Constraints -> SQL Queries)
   - **Expected Files**: `adapter_config.json`, `adapter_model.safetensors` (or `adapter_model.bin`)

2. **`models/lora_weights/sarvam_adapter/`**
   - **Base Model**: `sarvamai/sarvam-2b`
   - **Role**: Indic Transliteration, Script Normalization & Entity Grounding
   - **Expected Files**: `adapter_config.json`, `adapter_model.safetensors` (or `adapter_model.bin`)

When weights are placed in these folders, `indicsql/models/adapter.py` automatically detects them and enables real-time local edge LoRA inference!
