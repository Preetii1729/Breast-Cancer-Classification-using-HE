#!/usr/bin/env python3
"""
Test script for Federated Learning without Homomorphic Encryption
This allows you to test the federated learning logic before adding encryption
"""

import sys
import os
import pandas as pd
import numpy as np
import torch
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Add paths
sys.path.append('models')
sys.path.append('openfhe_lib/bfv')

# Import our modules
from LogisticRegression import LogisticRegression
from openFHE_simple import generate_keys, encrypt_weights, decrypt_weights, aggregator

class FederatedClient:
    def __init__(self, name, data, n_features, epochs=10, lr=0.01):
        self.name = name
        self.data = data
        self.n_features = n_features
        self.epochs = epochs
        self.lr = lr
        
        # Split data - assuming 'diagnostic' column is the target
        # Find the target column (should be 'diagnostic' or 'diagnosis')
        target_col = None
        for col in ['diagnostic', 'diagnosis']:
            if col in data.columns:
                target_col = col
                break
        
        if target_col is None:
            raise ValueError("No target column found. Expected 'diagnostic' or 'diagnosis'")
        
        # Get feature columns (exclude id and target)
        feature_cols = [col for col in data.columns if col not in ['id', target_col]]
        
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            data[feature_cols], data[target_col], test_size=0.2, random_state=42
        )
        
        # Normalize features
        self.scaler = StandardScaler()
        self.X_train = self.scaler.fit_transform(self.X_train)
        self.X_test = self.scaler.transform(self.X_test)
        
        # Convert to tensors
        self.X_train = torch.FloatTensor(self.X_train)
        self.X_test = torch.FloatTensor(self.X_test)
        self.y_train = torch.FloatTensor(self.y_train.values).reshape(-1, 1)
        self.y_test = torch.FloatTensor(self.y_test.values).reshape(-1, 1)
        
        # Initialize model
        self.model = LogisticRegression(n_features)
        self.optimizer = torch.optim.SGD(self.model.parameters(), lr=lr)
        self.criterion = torch.nn.BCELoss()
        
        print(f"Client {self.name}: {len(self.X_train)} training samples, {len(self.X_test)} test samples")
    
    def train_local(self):
        """Train the local model"""
        self.model.train()
        for epoch in range(self.epochs):
            self.optimizer.zero_grad()
            outputs = self.model(self.X_train)
            loss = self.criterion(outputs, self.y_train)
            loss.backward()
            self.optimizer.step()
        
        # Get model weights
        weights = []
        for param in self.model.parameters():
            weights.extend(param.data.flatten().tolist())
        
        return weights
    
    def evaluate(self):
        """Evaluate the local model"""
        self.model.eval()
        with torch.no_grad():
            predictions = self.model(self.X_test)
            predictions = (predictions > 0.5).float()
            accuracy = accuracy_score(self.y_test.numpy(), predictions.numpy())
        return accuracy
    
    def update_global_weights(self, global_weights):
        """Update local model with global weights"""
        # Reshape global weights back to model parameters
        with torch.no_grad():
            param_idx = 0
            for param in self.model.parameters():
                param_size = param.numel()
                param.data = torch.FloatTensor(global_weights[param_idx:param_idx + param_size]).reshape(param.shape)
                param_idx += param_size

def load_data():
    """Load and prepare datasets"""
    print("Loading datasets...")
    
    # Load datasets
    df1 = pd.read_csv('data/dataset1.csv')
    df2 = pd.read_csv('data/dataset2.csv') 
    df3 = pd.read_csv('data/dataset3.csv')
    df4 = pd.read_csv('data/dataset4.csv')
    
    # Preprocess datasets
    datasets = [df1, df2, df3, df4]
    for i, df in enumerate(datasets):
        # Convert diagnostic/diagnosis to binary
        target_col = None
        for col in ['diagnostic', 'diagnosis']:
            if col in df.columns:
                target_col = col
                break
        
        if target_col:
            df[target_col] = (df[target_col] == 'M').astype(int)
            datasets[i] = df
    
    print(f"Loaded {len(datasets)} datasets")
    return datasets

def federated_learning_simulation():
    """Simulate federated learning without encryption"""
    print("=== Federated Learning Simulation (No Encryption) ===\n")
    
    # Load data
    datasets = load_data()
    
    # Create clients
    clients = []
    for i, data in enumerate(datasets):
        client = FederatedClient(f"Hospital_{i+1}", data, n_features=30, epochs=5)
        clients.append(client)
    
    print(f"\nCreated {len(clients)} clients")
    
    # Federated learning rounds
    num_rounds = 3
    
    for round_num in range(num_rounds):
        print(f"\n--- Round {round_num + 1} ---")
        
        # 1. Local training
        print("1. Local training...")
        local_weights = []
        for client in clients:
            weights = client.train_local()
            local_weights.append(weights)
            print(f"   {client.name}: Trained local model")
        
        # 2. Simulate encryption (just save weights)
        print("2. Simulating encryption...")
        for i, weights in enumerate(local_weights):
            encrypt_weights(weights, f"/enc_weight_client{i+1}.txt")
        
        # 3. Aggregation
        print("3. Aggregating weights...")
        aggregator()
        
        # 4. Simulate decryption and update
        print("4. Updating global model...")
        global_weights = decrypt_weights("/enc_aggregator_weight_server.txt")
        
        # Update all clients with global weights
        for client in clients:
            client.update_global_weights(global_weights)
        
        # 5. Evaluate
        print("5. Evaluating models...")
        for client in clients:
            accuracy = client.evaluate()
            print(f"   {client.name}: Accuracy = {accuracy:.4f}")
    
    print("\nSimulation Complete")
    
if __name__ == "__main__":
    try:
        federated_learning_simulation()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have all required Python packages installed:")
        print("pip install torch pandas numpy scikit-learn")
