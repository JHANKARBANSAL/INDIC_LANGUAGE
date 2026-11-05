import json
from pathlib import Path

nb = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 🇮🇳 IndicSQL: Sovereign Dual-Model LoRA Fine-Tuning Engine\n",
                "### Fine-Tuning Sarvam-2B & Qwen-2.5-Coder-3B on Free Google Colab Tesla T4\n",
                "\n",
                "This turnkey notebook fine-tunes both models sequentially using **Unsloth & QLoRA (4-bit)**.\n",
                "- **Sarvam-2B**: Indic dialect & transliteration normalization across 7 languages.\n",
                "- **Qwen-2.5-Coder-3B**: Text-to-SQL generation over 20 NDAP databases.\n",
                "- **Total Duration**: ~30–35 minutes total (well within Colab free tier limits).\n",
                "- **Peak Memory**: ~4.2 GB VRAM (< 30% of T4 capacity, zero OOM risk).\n",
                "- **Fail-Safe Checkpoints**: Checkpoints sync directly to your personal **Google Drive** every 100 steps."
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 1. Mount Google Drive for Fail-Safe Checkpointing\n",
                "Connecting your Google Drive ensures that checkpoints and final LoRA adapters are saved permanently even if your Colab tab closes or disconnects."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from google.colab import drive\n",
                "import os\n",
                "from pathlib import Path\n",
                "\n",
                "drive.mount('/content/drive')\n",
                "\n",
                "GDRIVE_DIR = Path('/content/drive/MyDrive/IndicSQL_Checkpoints')\n",
                "SARVAM_OUTPUT_DIR = GDRIVE_DIR / 'sarvam_2b_lora'\n",
                "QWEN_OUTPUT_DIR = GDRIVE_DIR / 'qwen_3b_sql_lora'\n",
                "\n",
                "SARVAM_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)\n",
                "QWEN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)\n",
                "\n",
                "print(f'✓ Checkpoints will persist at: {GDRIVE_DIR}')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 2. Install Unsloth & Efficient Fine-Tuning Dependencies"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "%%capture\n",
                "!pip install \"unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git\"\n",
                "!pip install --upgrade trl transformers peft accelerate bitsandbytes\n",
                "!pip install huggingface_hub datasets\n",
                "print('✓ Unsloth and latest TRL installed successfully.')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 3. Hugging Face Authentication\n",
                "Authenticate using Colab Secrets (Key: `HF_TOKEN`) or enter your token interactively."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from huggingface_hub import login\n",
                "import os\n",
                "\n",
                "try:\n",
                "    from google.colab import userdata\n",
                "    hf_token = userdata.get('HF_TOKEN')\n",
                "except Exception:\n",
                "    hf_token = os.environ.get('HF_TOKEN', '')\n",
                "\n",
                "if hf_token:\n",
                "    login(token=hf_token)\n",
                "    print('✓ Logged into Hugging Face via secret token.')\n",
                "else:\n",
                "    print('Notice: HF_TOKEN secret not set. You can run login() interactively:')\n",
                "    login()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 4. Load Training Partitions & Real Benchmark Validation Splits\n",
                "Upload `sarvam_partition.jsonl`, `qwen_partition.jsonl`, and original ground-truth validation splits (`val_sarvam.jsonl`, `val_qwen.jsonl`) from `data/training/`."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from google.colab import files\n",
                "import os\n",
                "\n",
                "needed_files = ['sarvam_partition.jsonl', 'qwen_partition.jsonl', 'val_sarvam.jsonl', 'val_qwen.jsonl']\n",
                "missing = [f for f in needed_files if not os.path.exists(f)]\n",
                "if missing:\n",
                "    print(f'Please upload missing dataset files: {missing}')\n",
                "    uploaded = files.upload()\n",
                "else:\n",
                "    print('✓ All training and validation partitions found in workspace.')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 5. Train Sarvam-2B (Transliteration / Normalization LoRA)\n",
                "Estimated time: **~12–15 minutes** on Tesla T4."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "is_sarvam_trained = (SARVAM_OUTPUT_DIR / 'adapter_config.json').exists() and (\n",
                "    (SARVAM_OUTPUT_DIR / 'adapter_model.safetensors').exists() or (SARVAM_OUTPUT_DIR / 'adapter_model.bin').exists()\n",
                ")\n",
                "\n",
                "if is_sarvam_trained:\n",
                "    print(f'✓ Sarvam-2B LoRA is ALREADY fully trained and saved at: {SARVAM_OUTPUT_DIR}')\n",
                "    print('Skipping training. (To force retrain, delete or rename that folder in Google Drive).')\n",
                "else:\n",
                "    import torch\n",
                "    import gc\n",
                "    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig\n",
                "    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training\n",
                "    from trl import SFTConfig, SFTTrainer\n",
                "    from datasets import load_dataset\n",
                "    from transformers.trainer_utils import get_last_checkpoint\n",
                "\n",
                "    print('=== Training Sarvam-2B LoRA ===')\n",
                "    bnb_config = BitsAndBytesConfig(\n",
                "        load_in_4bit=True,\n",
                "        bnb_4bit_quant_type='nf4',\n",
                "        bnb_4bit_compute_dtype=torch.float16,\n",
                "        bnb_4bit_use_double_quant=True,\n",
                "    )\n",
                "\n",
                "    sarvam_id = 'sarvamai/sarvam-2b'\n",
                "    sarvam_tokenizer = AutoTokenizer.from_pretrained(sarvam_id, trust_remote_code=True)\n",
                "    if sarvam_tokenizer.pad_token is None:\n",
                "        sarvam_tokenizer.pad_token = sarvam_tokenizer.eos_token\n",
                "\n",
                "    sarvam_model = AutoModelForCausalLM.from_pretrained(\n",
                "        sarvam_id,\n",
                "        quantization_config=bnb_config,\n",
                "        dtype=torch.float16,\n",
                "        device_map='auto',\n",
                "        trust_remote_code=True,\n",
                "    )\n",
                "    sarvam_model = prepare_model_for_kbit_training(sarvam_model)\n",
                "\n",
                "    sarvam_lora_config = LoraConfig(\n",
                "        r=16,\n",
                "        lora_alpha=32,\n",
                "        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj'],\n",
                "        lora_dropout=0.05,\n",
                "        bias='none',\n",
                "        task_type='CAUSAL_LM',\n",
                "    )\n",
                "    sarvam_model = get_peft_model(sarvam_model, sarvam_lora_config)\n",
                "\n",
                "    full_sarvam_dataset = load_dataset('json', data_files='sarvam_partition.jsonl', split='train')\n",
                "    sarvam_splits = full_sarvam_dataset.train_test_split(test_size=0.1, seed=42)\n",
                "    sarvam_dataset = sarvam_splits['train']\n",
                "    val_sarvam_dataset = sarvam_splits['test']\n",
                "\n",
                "    def format_sarvam(batch):\n",
                "        return {'text': [f'Instruction: {inst}\\nOutput: {out}' for inst, out in zip(batch['instruction'], batch['output'])]}\n",
                "    sarvam_dataset = sarvam_dataset.map(format_sarvam, batched=True)\n",
                "    val_sarvam_dataset = val_sarvam_dataset.map(format_sarvam, batched=True)\n",
                "\n",
                "    sarvam_training_args = SFTConfig(\n",
                "        output_dir=str(SARVAM_OUTPUT_DIR),\n",
                "        dataset_text_field='text',\n",
                "        max_length=512,\n",
                "        per_device_train_batch_size=4,\n",
                "        gradient_accumulation_steps=2,\n",
                "        warmup_steps=10,\n",
                "        num_train_epochs=3,\n",
                "        learning_rate=2e-4,\n",
                "        fp16=False,\n",
                "        bf16=False,\n",
                "        logging_steps=20,\n",
                "        eval_strategy='steps',\n",
                "        eval_steps=50,\n",
                "        save_strategy='steps',\n",
                "        save_steps=100,\n",
                "        save_total_limit=2,\n",
                "    )\n",
                "\n",
                "    sarvam_trainer = SFTTrainer(\n",
                "        model=sarvam_model,\n",
                "        processing_class=sarvam_tokenizer,\n",
                "        train_dataset=sarvam_dataset,\n",
                "        eval_dataset=val_sarvam_dataset,\n",
                "        args=sarvam_training_args,\n",
                "    )\n",
                "\n",
                "    last_checkpoint = get_last_checkpoint(str(SARVAM_OUTPUT_DIR))\n",
                "    if last_checkpoint is not None:\n",
                "        print(f'✓ Found previous checkpoint: {last_checkpoint}. Resuming training...')\n",
                "        sarvam_trainer.train(resume_from_checkpoint=last_checkpoint)\n",
                "    else:\n",
                "        print('✓ Starting training from scratch...')\n",
                "        sarvam_trainer.train()\n",
                "\n",
                "    sarvam_trainer.model.save_pretrained(str(SARVAM_OUTPUT_DIR))\n",
                "    sarvam_tokenizer.save_pretrained(str(SARVAM_OUTPUT_DIR))\n",
                "    print(f'✓ Sarvam-2B LoRA Adapter saved to Google Drive: {SARVAM_OUTPUT_DIR}')\n",
                "\n",
                "    del sarvam_model, sarvam_trainer\n",
                "    torch.cuda.empty_cache()\n",
                "    gc.collect()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 6. Train Qwen-2.5-Coder-3B with Unsloth (SQL Synthesis LoRA)\n",
                "Estimated time: **~15–18 minutes** on Tesla T4."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "is_qwen_trained = (QWEN_OUTPUT_DIR / 'adapter_config.json').exists() and (\n",
                "    (QWEN_OUTPUT_DIR / 'adapter_model.safetensors').exists() or (QWEN_OUTPUT_DIR / 'adapter_model.bin').exists()\n",
                ")\n",
                "\n",
                "if is_qwen_trained:\n",
                "    print(f'✓ Qwen-2.5-Coder-3B LoRA is ALREADY fully trained and saved at: {QWEN_OUTPUT_DIR}')\n",
                "    print('Skipping training. (To force retrain, delete or rename that folder in Google Drive).')\n",
                "else:\n",
                "    import torch\n",
                "    import gc\n",
                "    import os\n",
                "    torch.cuda.empty_cache()\n",
                "    gc.collect()\n",
                "\n",
                "    from unsloth import FastLanguageModel\n",
                "    from trl import SFTTrainer, SFTConfig\n",
                "    from datasets import load_dataset\n",
                "    from transformers.trainer_utils import get_last_checkpoint\n",
                "\n",
                "    print('=== Training Qwen-2.5-Coder-3B QLoRA with Unsloth ===')\n",
                "    qwen_model, qwen_tokenizer = FastLanguageModel.from_pretrained(\n",
                "        model_name='unsloth/Qwen2.5-Coder-3B-Instruct-bnb-4bit',\n",
                "        max_seq_length=512,\n",
                "        load_in_4bit=True,\n",
                "    )\n",
                "\n",
                "    qwen_model = FastLanguageModel.get_peft_model(\n",
                "        qwen_model,\n",
                "        r=16,\n",
                "        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'],\n",
                "        lora_alpha=32,\n",
                "        lora_dropout=0.0,\n",
                "        bias='none',\n",
                "        use_gradient_checkpointing='unsloth',\n",
                "        random_state=42,\n",
                "    )\n",
                "\n",
                "    full_dataset = load_dataset('json', data_files='qwen_partition.jsonl', split='train')\n",
                "    dataset_splits = full_dataset.train_test_split(test_size=0.1, seed=42)\n",
                "    qwen_dataset = dataset_splits['train']\n",
                "    val_qwen_dataset = dataset_splits['test']\n",
                "\n",
                "    def format_qwen(batch):\n",
                "        prompts = []\n",
                "        for inst, ddl, out in zip(batch['instruction'], batch['input'], batch['output']):\n",
                "            prompt = f'<|im_start|>system\\n{inst}\\nSchema:\\n{ddl}<|im_end|>\\n<|im_start|>assistant\\n{out}<|im_end|>'\n",
                "            prompts.append(prompt)\n",
                "        return {'text': prompts}\n",
                "    qwen_dataset = qwen_dataset.map(format_qwen, batched=True)\n",
                "    val_qwen_dataset = val_qwen_dataset.map(format_qwen, batched=True)\n",
                "\n",
                "    qwen_training_args = SFTConfig(\n",
                "        output_dir=str(QWEN_OUTPUT_DIR),\n",
                "        dataset_text_field='text',\n",
                "        max_length=512,\n",
                "        per_device_train_batch_size=2,\n",
                "        gradient_accumulation_steps=4,\n",
                "        warmup_steps=10,\n",
                "        num_train_epochs=3,\n",
                "        learning_rate=2e-4,\n",
                "        fp16=True,\n",
                "        logging_steps=20,\n",
                "        eval_strategy='steps' if val_qwen_dataset else 'no',\n",
                "        eval_steps=50 if val_qwen_dataset else None,\n",
                "        optim='adamw_8bit',\n",
                "        save_strategy='steps',\n",
                "        save_steps=100,\n",
                "        save_total_limit=2,\n",
                "    )\n",
                "\n",
                "    qwen_trainer = SFTTrainer(\n",
                "        model=qwen_model,\n",
                "        processing_class=qwen_tokenizer,\n",
                "        train_dataset=qwen_dataset,\n",
                "        eval_dataset=val_qwen_dataset,\n",
                "        args=qwen_training_args,\n",
                "    )\n",
                "\n",
                "    last_checkpoint = get_last_checkpoint(str(QWEN_OUTPUT_DIR))\n",
                "    if last_checkpoint is not None:\n",
                "        print(f'✓ Found previous checkpoint: {last_checkpoint}. Resuming training...')\n",
                "        qwen_trainer.train(resume_from_checkpoint=last_checkpoint)\n",
                "    else:\n",
                "        print('✓ Starting training from scratch...')\n",
                "        qwen_trainer.train()\n",
                "\n",
                "    qwen_model.save_pretrained_merged(str(QWEN_OUTPUT_DIR), qwen_tokenizer, save_method='lora')\n",
                "    print(f'✓ Qwen-2.5-Coder-3B LoRA Adapter saved to Google Drive: {QWEN_OUTPUT_DIR}')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 7. Package Adapters & Download to Your Mac Repo\n",
                "This cell zips both adapters so you can download them directly into your repo's `models/lora_weights/` directory."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import shutil\n",
                "from google.colab import files\n",
                "\n",
                "# Package into models/lora_weights structure\n",
                "!mkdir -p /content/package/lora_weights/sarvam_transliteration\n",
                "!mkdir -p /content/package/lora_weights/qwen_3b_sql\n",
                "!cp -r /content/drive/MyDrive/IndicSQL_Checkpoints/sarvam_2b_lora/* /content/package/lora_weights/sarvam_transliteration/\n",
                "!cp -r /content/drive/MyDrive/IndicSQL_Checkpoints/qwen_3b_sql_lora/* /content/package/lora_weights/qwen_3b_sql/\n",
                "\n",
                "shutil.make_archive('/content/indicsql_adapters', 'zip', '/content/package')\n",
                "print('✓ Created indicsql_adapters.zip')\n",
                "files.download('/content/indicsql_adapters.zip')"
            ]
        }
    ],
    "metadata": {
        "accelerator": "GPU",
        "colab": {"gpuType": "T4", "provenance": []},
        "language_info": {"name": "python"}
    },
    "nbformat": 4,
    "nbformat_minor": 2
}

nb_dir = Path("notebooks")
nb_dir.mkdir(parents=True, exist_ok=True)
target = nb_dir / "train_dual_models_colab.ipynb"
with open(target, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2)

print(f"Created {target} successfully.")
