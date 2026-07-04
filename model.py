import os
import torch
import torch.nn as nn
from transformers import BertModel, BertPreTrainedModel, AutoTokenizer, BertConfig

# Define the exact same model class used during training
class BertForMultiLabelClassification(BertPreTrainedModel):
    def __init__(self, config):
        super().__init__(config)
        self.num_labels = config.num_labels
        self.bert = BertModel(config)
        self.dropout = nn.Dropout(0.3)
        self.classifier = nn.Linear(config.hidden_size, self.num_labels)

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

# Toxic comment labels
LABELS = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]

class ToxicClassifier:
    def __init__(self, model_dir="./best_model"):
        self.model_dir = model_dir
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_loaded = False
        
    def load_model(self):
        """Loads the saved tokenizer and model from the model directory."""
        if not os.path.exists(self.model_dir):
            raise FileNotFoundError(
                f"Model directory '{self.model_dir}' not found. Please extract the downloaded Colab model "
                f"zip file into a folder named 'best_model' in the root directory."
            )
            
        # Load configuration, tokenizer and model using Hugging Face Auto classes
        from transformers import AutoModelForSequenceClassification
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_dir)
        
        self.model.to(self.device)
        self.model.eval()
        self.is_loaded = True

    def predict(self, text, threshold=0.4):
        """Runs inference on the input text and returns label probabilities and predictions."""
        if not self.is_loaded:
            self.load_model()
            
        # Tokenize input text
        inputs = self.tokenizer(
            text, 
            padding="max_length", 
            truncation=True, 
            max_length=128, 
            return_tensors="pt"
        )
        
        # Move tensors to the appropriate device
        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)
        
        # Run inference
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs["logits"]
            probs = torch.sigmoid(logits).squeeze(0).cpu().numpy()
            
        results = {}
        for label, prob in zip(LABELS, probs):
            results[label] = {
                "probability": float(prob),
                "flagged": bool(prob > threshold)
            }
            
        return results
