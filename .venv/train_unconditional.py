import os
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    DataCollatorForLanguageModeling,
    TrainingArguments,
    Trainer,
)

MODEL_NAME = "distilgpt2"
TRAIN_FILE = "habs_unconditional_train.txt"
OUT_DIR = "habs_distilgpt2_out"

def main():
    # Make output directory
    os.makedirs(OUT_DIR, exist_ok=True)
    # tokenizer, add pad token for eos
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token
    # Load dataset
    ds = load_dataset("text", data_files={"train",TRAIN_FILE})

    def tokenize_function(batch):
        return tokenizer(batch["text"], truncation=True, max_length=128)