#!/usr/bin/env python3
"""
CAN Bus IDS - ML Model Trainer
Trains Isolation Forest on normal CAN traffic
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import sys

def load_data(filename='training_data.csv'):
    """Load training data from CSV"""
    print(f"[*] Loading data from {filename}...")
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        print(f"[ERROR] {filename} not found!")
        print("Run ./can_simulator.exe first to generate training data")
        sys.exit(1)
    
    print(f"[+] Loaded {len(df)} samples")
    print(f"    - Normal: {len(df[df['is_attack'] == 0])}")
    print(f"    - Attack: {len(df[df['is_attack'] == 1])}")
    return df

def prepare_features(df):
    """Extract features for ML model"""
    features = ['can_id', 'dlc', 'avg_byte_value', 'time_since_last', 'byte_0', 'byte_1']
    X = df[features].values
    y = df['is_attack'].values
    return X, y, features

def train_model(X_train, contamination=0.1):
    """Train Isolation Forest model"""
    print(f"\n[*] Training Isolation Forest (contamination={contamination})...")
    
    # Normalize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)
    
    # Train model
    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100,
        max_samples='auto'
    )
    model.fit(X_scaled)
    
    print("[+] Training complete")
    return model, scaler

def evaluate_model(model, scaler, X_test, y_test):
    """Evaluate model performance"""
    print("\n[*] Evaluating model...")
    
    X_scaled = scaler.transform(X_test)
    predictions = model.predict(X_scaled)
    
    # Convert predictions: -1 (anomaly) -> 1 (attack), 1 (normal) -> 0 (normal)
    predictions = np.where(predictions == -1, 1, 0)
    
    print("\n=== Classification Report ===")
    print(classification_report(y_test, predictions, 
                                target_names=['Normal', 'Attack'], zero_division=0))
    
    print("\n=== Confusion Matrix ===")
    cm = confusion_matrix(y_test, predictions)
    print(f"True Negatives:  {cm[0][0]}")
    print(f"False Positives: {cm[0][1]}")
    print(f"False Negatives: {cm[1][0]}")
    print(f"True Positives:  {cm[1][1]}")
    
    # Calculate metrics
    accuracy = (cm[0][0] + cm[1][1]) / np.sum(cm)
    precision = cm[1][1] / (cm[1][1] + cm[0][1]) if (cm[1][1] + cm[0][1]) > 0 else 0
    recall = cm[1][1] / (cm[1][1] + cm[1][0]) if (cm[1][1] + cm[1][0]) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\nAccuracy:  {accuracy:.2%}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall:    {recall:.2%}")
    print(f"F1 Score:  {f1:.4f}")
    
    return accuracy, precision, recall, f1

def export_model_to_c(model, scaler, feature_names, output_file='include/ml_model_params.h'):
    """Export model parameters to C header file"""
    print(f"\n[*] Exporting model to {output_file}...")
    
    with open(output_file, 'w') as f:
        f.write("// Auto-generated ML model parameters\n")
        f.write("// DO NOT EDIT MANUALLY\n\n")
        f.write("#ifndef ML_MODEL_PARAMS_H\n")
        f.write("#define ML_MODEL_PARAMS_H\n\n")
        
        # Export feature scaling parameters
        f.write("// Feature scaling parameters (StandardScaler)\n")
        f.write(f"#define ML_NUM_FEATURES {len(feature_names)}\n\n")
        
        f.write("static const float ML_FEATURE_MEANS[ML_NUM_FEATURES] = {\n    ")
        f.write(", ".join([f"{mean:.6f}f" for mean in scaler.mean_]))
        f.write("\n};\n\n")
        
        f.write("static const float ML_FEATURE_STDS[ML_NUM_FEATURES] = {\n    ")
        f.write(", ".join([f"{std:.6f}f" for std in scaler.scale_]))
        f.write("\n};\n\n")
        
        # Export decision function offset (threshold)
        f.write("// Isolation Forest threshold\n")
        f.write(f"#define ML_THRESHOLD {model.offset_:.6f}f\n\n")
        
        f.write("#endif // ML_MODEL_PARAMS_H\n")
    
    print("[+] Model exported successfully")

def main():
    print("=" * 60)
    print("CAN Bus IDS - Machine Learning Trainer")
    print("=" * 60)
    
    # Load data
    df = load_data()
    
    # Split into train (normal only) and test (all data)
    df_normal = df[df['is_attack'] == 0]
    df_test = df  # Test on all data
    
    print(f"\n[*] Using {len(df_normal)} normal samples for training")
    
    # Prepare features
    X_train, _, feature_names = prepare_features(df_normal)
    X_test, y_test, _ = prepare_features(df_test)
    
    # Train model
    model, scaler = train_model(X_train, contamination=0.1)
    
    # Evaluate
    evaluate_model(model, scaler, X_test, y_test)
    
    # Export to C
    export_model_to_c(model, scaler, feature_names)
    
    print("\n" + "=" * 60)
    print("Training complete! Next steps:")
    print("  1. Review include/ml_model_params.h")
    print("  2. Rebuild with: make clean && make")
    print("  3. Run simulator to test ML detection")
    print("=" * 60)

if __name__ == '__main__':
    main()