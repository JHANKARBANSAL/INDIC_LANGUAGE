#!/usr/bin/env python3
"""
Standard HuggingFace PEFT / TRL Fine-Tuning Harness.
Supports training both Sarvam-2B (transliteration) and Qwen-2.5-Coder-3B (SQL).
Includes dry-run and safety checks for non-CUDA dev machines.
"""

import argparse
import sys
from pathlib import Path


def train_lora(
    model_type: str,
    dataset_path: str,
    output_dir: str,
    max_seq_length: int = 512,
    num_train_epochs: int = 3,
    batch_size: int = 2,
    learning_rate: float = 2e-4,
    dry_run: bool = False,
):
    print("=" * 60)
    print(f"IndicSQL LoRA Harness: Model={model_type}")
    print(f"Dataset: {dataset_path}")
    print(f"Output:  {output_dir}")
    print("=" * 60)

    data_file = Path(dataset_path)
    if not data_file.exists():
        print(f"Error: Dataset not found at {dataset_path}. Run dataset_curator first.")
        sys.exit(1)

    line_count = sum(1 for _ in open(data_file, encoding="utf-8"))
    print(f"Dataset records loaded: {line_count:,}")

    if dry_run:
        print("Dry run requested. Dataset validation passed. Exiting without training.")
        return

    try:
        import torch
        from datasets import load_dataset
        from peft import LoraConfig
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )
        from trl import SFTConfig, SFTTrainer
    except ImportError as e:
        print(f"Notice: ML dependencies not installed ({e}). Training skipped.")
        return

    if not torch.cuda.is_available() and not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
        print("Notice: No CUDA or MPS accelerator detected. Training skipped in CPU dev environment.")
        return

    model_id = "sarvamai/sarvam-2b" if model_type == "sarvam" else "Qwen/Qwen2.5-Coder-3B-Instruct"

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    ) if torch.cuda.is_available() else None

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else "cpu",
        trust_remote_code=True,
    )

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    sft_config = SFTConfig(
        output_dir=output_dir,
        dataset_text_field="output",
        max_length=max_seq_length,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        num_train_epochs=num_train_epochs,
        learning_rate=learning_rate,
        logging_steps=10,
        save_strategy="steps",
        save_steps=100,
        save_total_limit=2,
        fp16=False,
        bf16=False,
    )

    dataset = load_dataset("json", data_files=str(data_file), split="train")

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        peft_config=lora_config,
        args=sft_config,
    )

    trainer.train()
    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Adapter saved to {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HuggingFace PEFT Training Harness")
    parser.add_argument("--model", choices=["sarvam", "qwen"], default="qwen")
    parser.add_argument("--data", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    default_data = "data/training/sarvam_partition.jsonl" if args.model == "sarvam" else "data/training/qwen_partition.jsonl"
    default_output = f"models/lora_weights/{args.model}_adapter"

    train_lora(
        model_type=args.model,
        dataset_path=args.data or default_data,
        output_dir=args.output or default_output,
        dry_run=args.dry_run,
    )
