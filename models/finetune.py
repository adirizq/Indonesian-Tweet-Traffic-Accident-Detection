import sys
import torch
import pytorch_lightning as pl

from torch import nn
from torch.nn import functional as F
from transformers import BertForSequenceClassification
from sklearn.metrics import classification_report


class Finetune(pl.LightningModule):

    def __init__(self, model, learning_rate=2e-5) -> None:

        super(Finetune, self).__init__()
        # self.model = BertForSequenceClassification.from_pretrained(model, num_labels=num_classes, output_attentions=False, output_hidden_states=False)
        self.model = model
        self.lr = learning_rate

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.lr)
        return optimizer

    def training_step(self, batch, batch_idx):
        input_ids, attention_mask, label_batch = batch
        outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, labels=label_batch)
        loss = outputs.loss

        metrics = {}
        metrics['train_loss'] = round(loss.item(), 2)

        self.log_dict(metrics, prog_bar=False, on_epoch=True)

        return loss

    def validation_step(self, batch, batch_idx):
        loss, accuracy, f1_score, precision, recall = self._shared_eval_step(batch, batch_idx)

        metrics = {}
        metrics['val_loss'] = round(loss.item(), 2)
        metrics['val_accuracy'] = accuracy
        metrics['val_f1_score'] = f1_score
        metrics['val_precision'] = precision
        metrics['val_recall'] = recall

        self.log_dict(metrics, prog_bar=False, on_epoch=True)

        return loss

    def test_step(self, batch, batch_idx):
        loss, accuracy, f1_score, precision, recall = self._shared_eval_step(batch, batch_idx)

        metrics = {}
        metrics['test_loss'] = round(loss.item(), 2)
        metrics['test_accuracy'] = accuracy
        metrics['test_f1_score'] = f1_score
        metrics['test_precision'] = precision
        metrics['test_recall'] = recall

        self.log_dict(metrics, prog_bar=False, on_epoch=True)

        return loss

    def _shared_eval_step(self, batch, batch_idx):
        input_ids, attention_mask, label_batch = batch
        outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, labels=label_batch)
        loss = outputs.loss

        true = label_batch.to(torch.device("cpu"))
        pred = torch.argmax(F.softmax(outputs.logits), dim=1).to(torch.device("cpu"))

        cls_report = classification_report(true, pred, output_dict=True)

        accuracy = round(cls_report['accuracy'], 2)
        f1_score = round(cls_report['1']['f1-score'], 2)
        precision = round(cls_report['1']['precision'], 2)
        recall = round(cls_report['1']['recall'], 2)

        return loss, accuracy, f1_score, precision, recall

    def predict_step(self, batch, batch_idx):
        input_ids, attention_mask = batch
        outputs = self.model(input_ids, attention_mask)

        pred = torch.argmax(F.softmax(outputs.logits), dim=1).to(torch.device("cpu"))

        return pred[0]