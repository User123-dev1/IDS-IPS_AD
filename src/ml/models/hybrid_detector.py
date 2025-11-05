"""Hybrid Anomaly Detector - Fixed for Keras 3"""
import numpy as np
import json
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

try:
    from tensorflow import keras
    from tensorflow.keras import layers
    TF_AVAILABLE = True
except:
    TF_AVAILABLE = False
    print("[WARNING] TensorFlow not available - using Isolation Forest only")

class HybridAnomalyDetector:
    def __init__(self, sequence_length=10, contamination=0.05):  # Reduced contamination
        self.sequence_length = sequence_length
        self.contamination = contamination
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(
            contamination=contamination, n_estimators=100,
            max_samples='auto', random_state=42, n_jobs=-1
        )
        self.autoencoder = None
        self.reconstruction_threshold = None
        self.is_trained = False
        self.use_lstm = TF_AVAILABLE
        self.feature_dim = None
        
    def _build_lstm_autoencoder(self, input_dim):
        if not TF_AVAILABLE:
            return None
        encoder_inputs = keras.Input(shape=(self.sequence_length, input_dim))
        encoded = layers.LSTM(64, activation='relu', return_sequences=True, dropout=0.2)(encoder_inputs)
        encoded = layers.LSTM(32, activation='relu', return_sequences=False, dropout=0.2)(encoded)
        encoded = layers.Dense(16, activation='relu')(encoded)
        encoded = layers.Dropout(0.2)(encoded)
        decoded = layers.RepeatVector(self.sequence_length)(encoded)
        decoded = layers.LSTM(32, activation='relu', return_sequences=True, dropout=0.2)(decoded)
        decoded = layers.LSTM(64, activation='relu', return_sequences=True, dropout=0.2)(decoded)
        decoded = layers.TimeDistributed(layers.Dense(input_dim))(decoded)
        autoencoder = keras.Model(encoder_inputs, decoded)
        autoencoder.compile(optimizer=keras.optimizers.Adam(0.001), loss='mse')
        return autoencoder
    
    def train(self, normal_traffic_features, epochs=50, batch_size=32):
        print("\n" + "="*60)
        print("  Training Hybrid Anomaly Detector")
        print("="*60)
        self.feature_dim = normal_traffic_features.shape[1]
        print(f"\n[1/3] Normalizing {len(normal_traffic_features)} samples...")
        X_scaled = self.scaler.fit_transform(normal_traffic_features)
        print("  [OK] Normalized")
        
        print(f"\n[2/3] Training Isolation Forest...")
        self.isolation_forest.fit(X_scaled)
        print("  [OK] Trained")
        
        if self.use_lstm:
            print(f"\n[3/3] Training LSTM Autoencoder...")
            X_seq = self._create_sequences(X_scaled)
            if self.autoencoder is None:
                self.autoencoder = self._build_lstm_autoencoder(self.feature_dim)
            
            history = self.autoencoder.fit(
                X_seq, X_seq, epochs=epochs, batch_size=batch_size,
                validation_split=0.2, verbose=1,
                callbacks=[keras.callbacks.EarlyStopping(
                    monitor='val_loss', patience=10, restore_best_weights=True
                )]
            )
            
            reconstructions = self.autoencoder.predict(X_seq, verbose=0)
            errors = np.mean(np.abs(X_seq - reconstructions), axis=(1, 2))
            self.reconstruction_threshold = np.percentile(errors, 95)
            print(f"  [OK] Trained (threshold: {self.reconstruction_threshold:.6f})")
        
        self.is_trained = True
        print("\n" + "="*60)
        print("  [SUCCESS] Training Complete!")
        print("="*60 + "\n")
        return {'trained': True}
    
    def _create_sequences(self, data):
        if len(data) < self.sequence_length:
            padding = np.zeros((self.sequence_length - len(data), data.shape[1]))
            data = np.vstack([padding, data])
        sequences = []
        for i in range(len(data) - self.sequence_length + 1):
            sequences.append(data[i:i+self.sequence_length])
        return np.array(sequences)
    
    def predict(self, traffic_features):
        if not self.is_trained:
            raise ValueError("Model not trained!")
        X_scaled = self.scaler.transform(traffic_features)
        if_preds = self.isolation_forest.predict(X_scaled)
        if_scores = self.isolation_forest.score_samples(X_scaled)
        if_anomalies = (if_preds == -1)
        if_scores_norm = 1 / (1 + np.exp(if_scores))
        
        if self.use_lstm and self.autoencoder:
            X_seq = self._create_sequences(X_scaled)
            reconstructions = self.autoencoder.predict(X_seq, verbose=0)
            errors = np.mean(np.abs(X_seq - reconstructions), axis=(1, 2))
            ae_anomalies = (errors > self.reconstruction_threshold)
            ae_anomalies = np.pad(ae_anomalies, (self.sequence_length-1, 0), mode='edge')
            ae_scores = np.clip(errors / (self.reconstruction_threshold * 2), 0, 1)
            ae_scores = np.pad(ae_scores, (self.sequence_length-1, 0), mode='edge')
            combined_scores = 0.4 * if_scores_norm + 0.6 * ae_scores
            combined_anomalies = if_anomalies | ae_anomalies
        else:
            combined_scores = if_scores_norm
            combined_anomalies = if_anomalies
        
        return {'is_anomaly': combined_anomalies, 'anomaly_score': combined_scores}
    
    def save(self, path_prefix):
        path = Path(path_prefix)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.isolation_forest, f"{path}_if.pkl")
        joblib.dump(self.scaler, f"{path}_scaler.pkl")

        if self.use_lstm and self.autoencoder:
            # Try Keras 3 API first, fallback to TensorFlow 2.x API
            try:
                # Keras 3 API
                keras.saving.save_model(self.autoencoder, f"{path}_lstm.keras")
            except (AttributeError, ImportError):
                # TensorFlow 2.x / Keras 2.x API
                self.autoencoder.save(f"{path}_lstm.keras")
            np.save(f"{path}_threshold.npy", self.reconstruction_threshold)

        metadata = {
            'sequence_length': self.sequence_length,
            'contamination': self.contamination,
            'feature_dim': self.feature_dim,
            'use_lstm': self.use_lstm,
            'is_trained': self.is_trained,
            'threshold': float(self.reconstruction_threshold) if self.reconstruction_threshold else None
        }
        with open(f"{path}_meta.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"[OK] Saved to {path}_*")
    
    def load(self, path_prefix):
        path = Path(path_prefix)
        with open(f"{path}_meta.json", 'r') as f:
            meta = json.load(f)
        
        self.sequence_length = meta['sequence_length']
        self.contamination = meta['contamination']
        self.feature_dim = meta['feature_dim']
        self.use_lstm = meta['use_lstm']
        self.is_trained = meta['is_trained']
        self.reconstruction_threshold = meta['threshold']
        
        self.isolation_forest = joblib.load(f"{path}_if.pkl")
        self.scaler = joblib.load(f"{path}_scaler.pkl")
        
        if self.use_lstm and TF_AVAILABLE:
            keras_path = f"{path}_lstm.keras"
            h5_path = f"{path}_lstm.h5"
            if Path(keras_path).exists():
                # Try Keras 3 API first, fallback to TensorFlow 2.x API
                try:
                    self.autoencoder = keras.saving.load_model(keras_path)
                except (AttributeError, ImportError):
                    self.autoencoder = keras.models.load_model(keras_path, compile=False)
                    self.autoencoder.compile(optimizer='adam', loss='mse')
            elif Path(h5_path).exists():
                # Fallback to old H5 format
                self.autoencoder = keras.models.load_model(h5_path, compile=False)
                self.autoencoder.compile(optimizer='adam', loss='mse')
        
        print(f"[OK] Loaded from {path}_*")
