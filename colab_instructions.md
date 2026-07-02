# Complete Google Colab Script (Fixed for Transformers 4.40+)

This script allows you to upload `train.csv` directly into the Colab session, run the training, and download the trained model to your computer.

It solves the `AttributeError: module '__main__' has no attribute '__file__'` bug by writing the custom BERT model class definition to a separate file (`model_def.py`) and importing it.

## Instructions
1. Open a new Google Colab notebook (set the runtime type to **GPU** by going to *Runtime -> Change runtime type -> T4 GPU*).
2. Copy and paste the script below into a code cell and run it.
3. When prompted, click **Choose Files** and upload your local `train.csv` dataset.
4. Once training finishes, the browser will automatically zip and trigger a download of the `best_model.zip` file.

```python
# ==========================================
# 1. INSTALL DEPENDENCIES & WORKAROUNDS
# ==========================================
!pip install transformers datasets scikit-learn torch torchvision torchaudio --quiet

import os
import shutil
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from google.colab import files
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from datasets import Dataset
from transformers import (
    BertModel, 
    BertPreTrainedModel, 
    BertTokenizer, 
    BertConfig, 
    Trainer, 
    TrainingArguments
)

# Disable Weights & Biases logging
os.environ["WANDB_DISABLED"] = "true"

# Write the model definition to model_def.py to avoid '__main__' has no attribute '__file__' bug in Transformers
with open("model_def.py", "w") as f:
    f.write("""
import torch
import torch.nn as nn
from transformers import BertModel, BertPreTrainedModel

class BertForMultiLabelClassification(BertPreTrainedModel):
    def __init__(self, config, num_labels=6):
        super().__init__(config)
        self.num_labels = num_labels
        self.bert = BertModel(config)
        self.dropout = nn.Dropout(0.3)
        self.classifier = nn.Linear(config.hidden_size, num_labels)
        self.post_init()

    def forward(self, input_ids=None, attention_mask=None, labels=None):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)

        loss = None
        if labels is not None:
            loss_fct = nn.BCEWithLogitsLoss()
            loss = loss_fct(logits, labels.float())

        return {"loss": loss, "logits": logits}
""")

# Import the class from the newly created file
from model_def import BertForMultiLabelClassification
print("Successfully imported BertForMultiLabelClassification from model_def.py")

# ==========================================
# 2. UPLOAD DATASET DIRECTLY TO COLAB
# ==========================================
print("Please upload your 'train.csv' dataset file:")
uploaded = files.upload()

# Check if train.csv (or a renamed version like 'train (1).csv') was uploaded
if not uploaded:
    raise FileNotFoundError("No file was uploaded. Please upload your 'train.csv' dataset.")

uploaded_filename = list(uploaded.keys())[0]
print(f"Dataset '{uploaded_filename}' uploaded successfully! Loading data...")

# Load Dataset
df = pd.read_csv(uploaded_filename, engine="python", on_bad_lines='skip')
labels = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]

# Split dataset into train and validation (10%)
train_texts, val_texts, train_labels, val_labels = train_test_split(
    df["comment_text"].tolist(),
    df[labels].values,
    test_size=0.1,
    random_state=42
)

# Convert to HuggingFace Dataset
train_dataset = Dataset.from_dict({"text": train_texts, "labels": train_labels.tolist()})
val_dataset = Dataset.from_dict({"text": val_texts, "labels": val_labels.tolist()})

# Filter out non-string values
train_dataset = train_dataset.filter(lambda example: isinstance(example["text"], str))
val_dataset = val_dataset.filter(lambda example: isinstance(example["text"], str))

# ==========================================
# 3. TOKENIZATION Setup
# ==========================================
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

def tokenize(batch):
    return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=128)

train_dataset = train_dataset.map(tokenize, batched=True)
val_dataset = val_dataset.map(tokenize, batched=True)

train_dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])
val_dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

# ==========================================
# 4. INITIALIZE MODEL & CONFIG
# ==========================================
config = BertConfig.from_pretrained("bert-base-uncased", num_labels=len(labels))
model = BertForMultiLabelClassification(config)

# ==========================================
# 5. TRAINING ARGUMENTS & METRICS
# ==========================================
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=4,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    eval_strategy="epoch",
    save_strategy="epoch",
    logging_dir="./logs",
    logging_strategy="no",
    logging_steps=50,
    learning_rate=2e-5,
    weight_decay=0.01,
    load_best_model_at_end=True,
    save_total_limit=2,
    fp16=True,  # T4 GPU acceleration
)

# Compute Metrics with fixed NameError for precision
def compute_metrics(pred):
    logits, labels_arr = pred
    probs = torch.sigmoid(torch.tensor(logits)).numpy()
    preds = (probs > 0.4).astype(int)
    labels_arr = labels_arr.astype(int)

    acc = accuracy_score(labels_arr, preds)
    f1 = f1_score(labels_arr, preds, average="macro", zero_division=0)
    precision = precision_score(labels_arr, preds, average="macro", zero_division=0)
    recall = recall_score(labels_arr, preds, average="macro", zero_division=0)

    return {
        "accuracy": acc,
        "f1": f1,
        "precision": precision,
        "recall": recall
    }

# ==========================================
# 6. TRAIN & SAVE
# ==========================================
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics
)

# Train the model
print("Starting Model Training...")
trainer.train()

# Save best model weights and tokenizer configurations
output_model_dir = "./results/best_model"
model.save_pretrained(output_model_dir)
tokenizer.save_pretrained(output_model_dir)
print(f"Best model successfully saved to: {output_model_dir}")

# ==========================================
# 7. ZIP AND DOWNLOAD THE MODEL
# ==========================================
print("Zipping the model directory (this might take a minute)...")
shutil.make_archive('best_model', 'zip', output_model_dir)

print("Initiating download for 'best_model.zip' in your browser...")
files.download('best_model.zip')
```
