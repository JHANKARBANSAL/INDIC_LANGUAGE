#!/usr/bin/env python3
"""
Standalone QLoRA Fine-Tuning Harness for Qwen-2.5-Coder-3B using Unsloth.
Optimized for Tesla T4 (16 GB) / RTX 3090/4090 GPUs.
Peak VRAM footprint: ~4.2 GB.
"""

import argparse
import sys


def train_qwen_unsloth(
    dataset_path: str,
    output_dir: str,
    max_seq_length: int = 512,
    num_train_epochs: int = 3,
    batch_size: int = 2,
    gradient_accumulation_steps: int = 4,
    learning_rate: float = 2e-4,
    push_to_hub: bool = False,
    hub_model_id: str = "",
):
    try:
        import torch
        from datasets import load_dataset
        from trl import SFTConfig, SFTTrainer
        from unsloth import FastLanguageModel  # type: ignore[import-not-found]
    except ImportError as e:
        print(f"Error: Required training packages not installed ({e}).")
        print("Install via: pip install unsloth trl transformers accelerate bitsandbytes")
        sys.exit(1)

    if not torch.cuda.is_available():
        print("Warning: CUDA is not available. Unsloth requires an NVIDIA GPU (e.g. Google Colab T4).")
        print("Exiting in dry-run mode.")
        return

    print("=" * 60)
    print("Starting Qwen-2.5-Coder-3B QLoRA Fine-Tuning with Unsloth")
    print(f"Dataset: {dataset_path}")
    print(f"Output:  {output_dir}")
    print("=" * 60)

    # 1. Load model and tokenizer in 4-bit
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Qwen2.5-Coder-3B-Instruct-bnb-4bit",
        max_seq_length=max_seq_length,
        load_in_4bit=True,
    )

    # 2. Add LoRA adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=32,
        lora_dropout=0.0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    # 3. Format dataset
    dataset = load_dataset("json", data_files=dataset_path, split="train")

    def formatting_prompts_func(examples):
        texts = []
        for instruction, ddl, output in zip(examples["instruction"], examples["input"], examples["output"]):
            prompt = f"<|im_start|>system\n{instruction}\nSchema:\n{ddl}<|im_end|>\n<|im_start|>assistant\n{output}<|im_end|>"
            texts.append(prompt)
        return {"text": texts}

    dataset = dataset.map(formatting_prompts_func, batched=True)

    # 4. SFT Configuration
    sft_config = SFTConfig(
        output_dir=output_dir,
        dataset_text_field="text",
        max_length=max_seq_length,
        dataset_num_proc=2,
        packing=False,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        warmup_steps=10,
        num_train_epochs=num_train_epochs,
        learning_rate=learning_rate,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=20,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        save_strategy="steps",
        save_steps=100,
        save_total_limit=2,
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        args=sft_config,
    )

    # 5. Train
    print("Executing training loop...")
    trainer.train()

    # 6. Save final LoRA adapter
    print(f"Saving fine-tuned LoRA adapter to {output_dir}...")
    model.save_pretrained_merged(output_dir, tokenizer, save_method="lora")

    if push_to_hub and hub_model_id:
        print(f"Pushing adapter to Hugging Face Hub: {hub_model_id}...")
        model.push_to_hub_merged(hub_model_id, tokenizer, save_method="lora", private=True)

    print("Fine-tuning completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Qwen-2.5-Coder-3B with Unsloth")
    parser.add_argument("--data", default="data/training/qwen_partition.jsonl")
    parser.add_argument("--output", default="models/lora_weights/qwen_3b_sql")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--push-to-hub", action="store_true")
    parser.add_argument("--hub-id", default="")
    args = parser.parse_args()

    train_qwen_unsloth(
        dataset_path=args.data,
        output_dir=args.output,
        num_train_epochs=args.epochs,
        batch_size=args.batch_size,
        push_to_hub=args.push_to_hub,
        hub_model_id=args.hub_id,
    )
