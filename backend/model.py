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

# Determine dynamic default model path (looks locally inside backend/ first, then in the parent project root)
current_dir = os.path.dirname(os.path.abspath(__file__))
local_model = os.path.join(current_dir, "best_model")
parent_model = os.path.join(os.path.dirname(current_dir), "best_model")
DEFAULT_MODEL_DIR = local_model if os.path.exists(local_model) else parent_model

class ToxicClassifier:
    def __init__(self, model_dir=None):
        self.model_dir = model_dir or DEFAULT_MODEL_DIR
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_loaded = False
        
    def load_model(self):
        """Loads the saved tokenizer and model from the model directory."""
        if not os.path.exists(self.model_dir):
            raise FileNotFoundError(
                f"Model directory '{self.model_dir}' not found. Please extract the downloaded Colab model "
                f"zip file into the 'best_model' folder at the root of the project."
            )
            
        # Load configuration and tokenizer
        config = BertConfig.from_pretrained(self.model_dir, num_labels=len(LABELS))
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir, use_fast=True)
        
        # Create model architecture (empty weights)
        self.model = BertForMultiLabelClassification(config)
        
        # Load weights manually from safetensors to minimize memory usage
        safetensors_path = os.path.join(self.model_dir, "model.safetensors")
        if os.path.exists(safetensors_path):
            from safetensors.torch import load_file
            state_dict = load_file(safetensors_path, device="cpu")
            self.model.load_state_dict(state_dict, strict=False)
            del state_dict  # Free memory immediately
        else:
            # Fallback: try pytorch bin format
            bin_path = os.path.join(self.model_dir, "pytorch_model.bin")
            state_dict = torch.load(bin_path, map_location="cpu")
            self.model.load_state_dict(state_dict, strict=False)
            del state_dict
        
        import gc
        gc.collect()
        
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
