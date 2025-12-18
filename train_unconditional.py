import os
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    DataCollatorForLanguageModeling,
    TrainingArguments,
    Trainer,
)

MODEL_NAME = "distilgpt2"
TRAIN_FILE = r"habs_unconditional_train.txt"
OUT_DIR = "habs_distilgpt2_out"

def main():
    # Make output directory
    os.makedirs(OUT_DIR, exist_ok=True)
    # tokenizer, add pad token for eos
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token
    # Load dataset and prep model
    ds = load_dataset("text", data_files={"train": TRAIN_FILE})

    def tokenize_function(batch):
        return tokenizer(batch["text"], truncation=True, max_length=128)

    tokenized = ds.map(tokenize_function, batched=True, remove_columns=["text"])

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    model.config.pad_token_id = tokenizer.eos_token_id

    args = TrainingArguments(
        output_dir=OUT_DIR,
        overwrite_output_dir=True,
        num_train_epochs=2,
        per_device_train_batch_size=16,
        gradient_accumulation_steps=2,
        learning_rate=5e-6,
        warmup_steps=200,
        logging_steps=50,
        save_steps=50,
        save_total_limit=2,
        fp16=False,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenized["train"],
        data_collator=data_collator,
    )

    trainer.train()
    tokenizer.save_model(OUT_DIR)
    tokenizer.save_pretrained(OUT_DIR)

    print(f"Saved model to {OUT_DIR}")

if __name__ == "__main__":
    main()