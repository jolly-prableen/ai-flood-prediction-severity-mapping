import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)
import xgboost as xgb
import shap


class BaselinePipeline:
    def __init__(self, output_dir="results"):
        self.output_dir = output_dir
        self.metrics_dir = os.path.join(output_dir, "metrics")
        self.figures_dir = os.path.join(output_dir, "figures")
        os.makedirs(self.metrics_dir, exist_ok=True)
        os.makedirs(self.figures_dir, exist_ok=True)

        self.models = {
            "LogisticRegression": LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42),
            "RandomForest": RandomForestClassifier(n_estimators=300, max_depth=15, class_weight="balanced", random_state=42),
            "XGBoost": xgb.XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.05, eval_metric="logloss", random_state=42)
        }

    def evaluate_binary(self, y_true, y_pred, y_prob):
        return {
            "Accuracy": float(accuracy_score(y_true, y_pred)),
            "Precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "Recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "F1-Score": float(f1_score(y_true, y_pred, zero_division=0)),
            "ROC-AUC": float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.0,
            "PR-AUC": float(average_precision_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.0
        }

    def train_and_evaluate(self, train_path, test_path, target_col="flood_occurred"):
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)

        drop_cols = [target_col, "district", "state", "year", "month", "district_lgd_code"]
        feature_cols = [c for c in train_df.columns if c not in drop_cols and not train_df[c].dtype == 'object']

        X_train, y_train = train_df[feature_cols].fillna(0), train_df[target_col]
        X_test, y_test = test_df[feature_cols].fillna(0), test_df[target_col]

        results = {}

        for name, model in self.models.items():
            print(f"Training {name}...")
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred

            results[name] = self.evaluate_binary(y_test, y_pred, y_prob)

            # Confusion Matrix
            cm = confusion_matrix(y_test, y_pred)
            plt.figure(figsize=(6, 5))
            sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
            plt.title(f"{name} Confusion Matrix")
            plt.ylabel("True Label")
            plt.xlabel("Predicted Label")
            plt.tight_layout()
            plt.savefig(os.path.join(self.figures_dir, f"{name}_cm.png"))
            plt.close()

            # SHAP Summary Plot
            if name == "XGBoost":
                try:
                    explainer = shap.TreeExplainer(model)
                    shap_values = explainer.shap_values(X_test)
                    plt.figure(figsize=(10, 6))
                    shap.summary_plot(shap_values, X_test, show=False)
                    plt.tight_layout()
                    plt.savefig(os.path.join(self.figures_dir, "xgb_shap_summary.png"))
                    plt.close()
                except Exception as e:
                    print(f"SHAP calculation skipped: {e}")

        output_file = os.path.join(self.metrics_dir, "baseline_metrics.json")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=4)
            
        print(f"\nBaseline metrics successfully saved to: {output_file}")
        return results


if __name__ == "__main__":
    print("Baseline module setup complete.")