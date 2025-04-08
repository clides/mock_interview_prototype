import requests
import json
from dotenv import load_dotenv
import pytorch_lightning as pl
from transformers import T5Tokenizer
from transformers import T5ForConditionalGeneration
import torch
from torch.optim import AdamW

class T5Model(pl.LightningModule):
    def __init__(self):
        super().__init__()
        self.model = T5ForConditionalGeneration.from_pretrained("t5-base", return_dict=True)

    def forward(self, input_ids, attention_mask, labels=None):
        output = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )

        return output.loss, output.logits

    def training_step(self, batch, batch_idx):
        input_ids = batch["inputs_ids"]
        attention_mask = batch["attention_mask"]
        labels= batch["targets"]
        loss, outputs = self(input_ids, attention_mask, labels) # calls the forward method

        self.log("train_loss", loss, prog_bar=True, logger=True)

        return loss

    def validation_step(self, batch, batch_idx):
        input_ids = batch["inputs_ids"]
        attention_mask = batch["attention_mask"]
        labels= batch["targets"]
        loss, outputs = self(input_ids, attention_mask, labels) # calls the forward method

        self.log("val_loss", loss, prog_bar=True, logger=True)

        return loss

    def configure_optimizers(self):
        return AdamW(self.parameters(), lr=0.0001)

class QuestionGenerator():
    def __init__(self):     
        self.checkpoint_path = "questions/models/best_checkpoint.ckpt"
        self.model = T5Model.load_from_checkpoint(self.checkpoint_path)
        self.tokenizer = T5Tokenizer.from_pretrained("t5-base", model_max_length= 512)
        
        # Move the model to the appropriate device (e.g., GPU or CPU)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        # Set the model to evaluation mode
        self.model.eval()
        
    # Function to preprocess and make predictions
    def make_prediction(self, input_text):
        # Preprocess input text (tokenize)
        inputs = self.tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True, padding="max_length").to(self.device)
    
        # Generate predictions
        with torch.no_grad():  # Disable gradient computation
            outputs = self.model.model.generate(input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"])
    
        # Decode the predicted tokens to a string
        predicted_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return predicted_text