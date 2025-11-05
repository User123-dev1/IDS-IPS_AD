"""
Auto-deploy ML system
"""
import os
from pathlib import Path

# Create feature extraction
feature_code = '''"""Feature Extraction for ICS Network Traffic"""
import numpy as np
from datetime import datetime
from collections import defaultdict

class NetworkFeatureExtractor:
    def __init__(self):
        self.packet_history = defaultdict(list)
        self.ics_ports = [502, 20000, 102, 47808, 44818, 4840]
        
    def extract_features(self, packet_data):
        """Extract 10 features from packet"""
        features = []
        
        # 1-2: Sizes (normalized)
        features.append(packet_data.get('packet_size', 0) / 1500.0)
        features.append(packet_data.get('payload_size', 0) / 1500.0)
        
        # 3: Port (normalized)
        dst_port = packet_data.get('dst_port', 0)
        features.append(dst_port / 65535.0)
        
        # 4: Is ICS protocol
        features.append(1.0 if dst_port in self.ics_ports else 0.0)
        
        # 5: Inter-arrival time
        src_ip = packet_data.get('src_ip', '')
        timestamp = packet_data.get('timestamp', datetime.now())
        if src_ip in self.packet_history and self.packet_history[src_ip]:
            inter_arrival = (timestamp - self.packet_history[src_ip][-1]).total_seconds()
            features.append(min(inter_arrival, 10.0) / 10.0)
        else:
            features.append(0.0)
        self.packet_history[src_ip].append(timestamp)
        if len(self.packet_history[src_ip]) > 100:
            self.packet_history[src_ip] = self.packet_history[src_ip][-100:]
        
        # 6: TCP flags
        features.append(packet_data.get('tcp_flags', 0) / 255.0)
        
        # 7-8: Time features
        hour = timestamp.hour if hasattr(timestamp, 'hour') else 0
        features.append(hour / 24.0)
        weekday = timestamp.weekday() if hasattr(timestamp, 'weekday') else 0
        features.append(weekday / 7.0)
        
        # 9: Packet rate
        recent = [t for t in self.packet_history[src_ip] if (timestamp - t).total_seconds() < 1.0]
        features.append(min(len(recent) / 100.0, 1.0))
        
        # 10: Is internal IP
        try:
            import ipaddress
            is_internal = ipaddress.ip_address(src_ip).is_private
        except:
            is_internal = False
        features.append(1.0 if is_internal else 0.0)
        
        return np.array(features, dtype=np.float32)
    
    def extract_batch(self, packet_list):
        return np.array([self.extract_features(p) for p in packet_list])
    
    def get_feature_names(self):
        return ['packet_size', 'payload_size', 'dst_port', 'is_ics', 
                'inter_arrival', 'tcp_flags', 'hour', 'weekday', 
                'packet_rate', 'is_internal']
'''

# Create data generator
generator_code = '''"""Sample Data Generator"""
import numpy as np
from datetime import datetime, timedelta
import random

class SampleDataGenerator:
    def __init__(self, seed=42):
        np.random.seed(seed)
        random.seed(seed)
        self.ics_ports = [502, 20000, 102, 47808, 44818, 4840]
        
    def generate_normal_traffic(self, n_samples=10000):
        packets = []
        base_time = datetime.now()
        for i in range(n_samples):
            packet = {
                'src_ip': f"192.168.1.{random.randint(1, 50)}",
                'dst_ip': f"192.168.1.{random.randint(51, 100)}",
                'src_port': random.randint(10000, 65535),
                'dst_port': random.choice(self.ics_ports),
                'protocol': 'TCP',
                'packet_size': int(np.random.normal(200, 50)),
                'payload_size': int(np.random.normal(150, 40)),
                'timestamp': base_time + timedelta(seconds=i*0.1 + np.random.uniform(0, 0.05)),
                'tcp_flags': random.choice([2, 16, 18, 24]),
            }
            packet['packet_size'] = max(packet['packet_size'], packet['payload_size'] + 40)
            packets.append(packet)
        return packets
    
    def generate_anomalous_traffic(self, n_samples=1000):
        packets = []
        base_time = datetime.now()
        for i in range(n_samples):
            anom_type = random.choice(['port_scan', 'ddos', 'unusual_size'])
            if anom_type == 'port_scan':
                packet = {
                    'src_ip': f"192.168.1.{random.randint(1, 254)}",
                    'dst_ip': "192.168.1.100",
                    'src_port': random.randint(30000, 60000),
                    'dst_port': random.randint(1, 65535),
                    'protocol': 'TCP',
                    'packet_size': 60,
                    'payload_size': 0,
                    'timestamp': base_time + timedelta(seconds=i*0.001),
                    'tcp_flags': 2,
                }
            elif anom_type == 'ddos':
                packet = {
                    'src_ip': f"10.0.0.{random.randint(1, 254)}",
                    'dst_ip': "192.168.1.50",
                    'src_port': random.randint(1024, 65535),
                    'dst_port': random.choice(self.ics_ports),
                    'protocol': 'TCP',
                    'packet_size': random.randint(500, 1500),
                    'payload_size': random.randint(400, 1400),
                    'timestamp': base_time + timedelta(seconds=i*0.001),
                    'tcp_flags': 2,
                }
            else:  # unusual_size
                packet = {
                    'src_ip': f"192.168.1.{random.randint(1, 50)}",
                    'dst_ip': f"192.168.1.{random.randint(51, 100)}",
                    'src_port': random.randint(10000, 65535),
                    'dst_port': random.choice(self.ics_ports),
                    'protocol': 'TCP',
                    'packet_size': random.choice([50, 1500, 9000]),
                    'payload_size': random.choice([10, 1450, 8950]),
                    'timestamp': base_time + timedelta(seconds=i*0.1),
                    'tcp_flags': 24,
                }
            packets.append(packet)
        return packets
    
    def generate_mixed_dataset(self, n_normal=10000, n_anomalous=500):
        normal = self.generate_normal_traffic(n_normal)
        anomalous = self.generate_anomalous_traffic(n_anomalous)
        all_packets = normal + anomalous
        labels = [0] * n_normal + [1] * n_anomalous
        combined = list(zip(all_packets, labels))
        random.shuffle(combined)
        packets, labels = zip(*combined)
        return list(packets), np.array(labels)
'''

# Create hybrid detector
detector_code = '''"""Hybrid Anomaly Detector"""
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
    print("TensorFlow not available - using Isolation Forest only")

class HybridAnomalyDetector:
    def __init__(self, sequence_length=10, contamination=0.1):
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
        autoencoder.compile(optimizer=keras.optimizers.Adam(0.001), loss='mse', metrics=['mae'])
        return autoencoder
    
    def train(self, normal_traffic_features, epochs=50, batch_size=32):
        print("\\n" + "="*60)
        print("  Training Hybrid Anomaly Detector")
        print("="*60)
        self.feature_dim = normal_traffic_features.shape[1]
        print(f"\\n[1/3] Normalizing {len(normal_traffic_features)} samples...")
        X_scaled = self.scaler.fit_transform(normal_traffic_features)
        print("  ✓ Normalized")
        
        print(f"\\n[2/3] Training Isolation Forest...")
        self.isolation_forest.fit(X_scaled)
        print("  ✓ Trained")
        
        if self.use_lstm:
            print(f"\\n[3/3] Training LSTM Autoencoder...")
            X_seq = self._create_sequences(X_scaled)
            if self.autoencoder is None:
                self.autoencoder = self._build_lstm_autoencoder(self.feature_dim)
            history = self.autoencoder.fit(
                X_seq, X_seq, epochs=epochs, batch_size=batch_size,
                validation_split=0.2, verbose=1,
                callbacks=[keras.callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)]
            )
            reconstructions = self.autoencoder.predict(X_seq, verbose=0)
            errors = np.mean(np.abs(X_seq - reconstructions), axis=(1, 2))
            self.reconstruction_threshold = np.percentile(errors, 95)
            print(f"  ✓ Trained (threshold: {self.reconstruction_threshold:.6f})")
        
        self.is_trained = True
        print("\\n" + "="*60)
        print("  ✓ Training Complete!")
        print("="*60 + "\\n")
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
            self.autoencoder.save(f"{path}_lstm.h5")
            np.save(f"{path}_threshold.npy", self.reconstruction_threshold)
        metadata = {'sequence_length': self.sequence_length, 'contamination': self.contamination,
                   'feature_dim': self.feature_dim, 'use_lstm': self.use_lstm, 'is_trained': self.is_trained,
                   'threshold': float(self.reconstruction_threshold) if self.reconstruction_threshold else None}
        with open(f"{path}_meta.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"✓ Saved to {path}_*")
    
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
        if self.use_lstm and TF_AVAILABLE and Path(f"{path}_lstm.h5").exists():
            self.autoencoder = keras.models.load_model(f"{path}_lstm.h5")
        print(f"✓ Loaded from {path}_*")
'''

# Write files
Path("../src/ml/utils").mkdir(parents=True, exist_ok=True)
Path("../src/ml/models").mkdir(parents=True, exist_ok=True)

with open("../src/ml/utils/feature_extraction.py", "w") as f:
    f.write(feature_code)
print("✓ Created feature_extraction.py")

with open("../src/ml/utils/data_generator.py", "w") as f:
    f.write(generator_code)
print("✓ Created data_generator.py")

with open("../src/ml/models/hybrid_detector.py", "w") as f:
    f.write(detector_code)
print("✓ Created hybrid_detector.py")

# Create quick start
quickstart_code = '''"""Quick Start Training"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.models.hybrid_detector import HybridAnomalyDetector
from ml.utils.feature_extraction import NetworkFeatureExtractor
from ml.utils.data_generator import SampleDataGenerator

print("\\n" + "="*70)
print("  QUICK START - Training Hybrid Detector")
print("="*70)

# Generate data
print("\\n[1/4] Generating training data...")
generator = SampleDataGenerator()
packets = generator.generate_normal_traffic(n_samples=10000)
print(f"  ✓ Generated {len(packets)} packets")

# Extract features
print("\\n[2/4] Extracting features...")
extractor = NetworkFeatureExtractor()
features = extractor.extract_batch(packets)
print(f"  ✓ Extracted {features.shape[1]} features from {len(features)} packets")

# Train
print("\\n[3/4] Training model...")
detector = HybridAnomalyDetector(sequence_length=10, contamination=0.1)
detector.train(features, epochs=30)

# Save
print("\\n[4/4] Saving model...")
detector.save("data/models/hybrid_model")

# Test
print("\\n" + "="*70)
print("  TESTING")
print("="*70)
test_packets, labels = generator.generate_mixed_dataset(n_normal=900, n_anomalous=100)
test_features = extractor.extract_batch(test_packets)
results = detector.predict(test_features)

tp = ((results['is_anomaly'] == 1) & (labels == 1)).sum()
tn = ((results['is_anomaly'] == 0) & (labels == 0)).sum()
fp = ((results['is_anomaly'] == 1) & (labels == 0)).sum()
fn = ((results['is_anomaly'] == 0) & (labels == 1)).sum()

accuracy = (tp + tn) / len(labels)
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0

print(f"\\n  Results:")
print(f"    • Accuracy:  {accuracy*100:.1f}%")
print(f"    • Precision: {precision*100:.1f}%")
print(f"    • Recall:    {recall*100:.1f}%")
print(f"    • TP:{tp} TN:{tn} FP:{fp} FN:{fn}")

print("\\n" + "="*70)
print("  ✓ COMPLETE! Model saved to data/models/hybrid_model")
print("="*70 + "\\n")
'''

with open("../src/ml/quick_start.py", "w") as f:
    f.write(quickstart_code)
print("✓ Created quick_start.py")

print("\\n✓✓✓ All ML files deployed!")
