"""Quick Start Training - Windows Compatible"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.models.hybrid_detector import HybridAnomalyDetector
from ml.utils.feature_extraction import NetworkFeatureExtractor
from ml.utils.data_generator import SampleDataGenerator

print("\n" + "="*70)
print("  QUICK START - Training Hybrid Detector")
print("="*70)

# Generate data
print("\n[1/4] Generating training data...")
generator = SampleDataGenerator()
packets = generator.generate_normal_traffic(n_samples=10000)
print(f"  [OK] Generated {len(packets)} packets")

# Extract features
print("\n[2/4] Extracting features...")
extractor = NetworkFeatureExtractor()
features = extractor.extract_batch(packets)
print(f"  [OK] Extracted {features.shape[1]} features from {len(features)} packets")

# Train
print("\n[3/4] Training model...")
detector = HybridAnomalyDetector(sequence_length=10, contamination=0.1)
detector.train(features, epochs=30)

# Save
print("\n[4/4] Saving model...")
detector.save("data/models/hybrid_model")

# Test
print("\n" + "="*70)
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

print(f"\n  Results:")
print(f"    Accuracy:  {accuracy*100:.1f}%")
print(f"    Precision: {precision*100:.1f}%")
print(f"    Recall:    {recall*100:.1f}%")
print(f"    TP:{tp} TN:{tn} FP:{fp} FN:{fn}")

print("\n" + "="*70)
print("  [SUCCESS] Model saved to data/models/hybrid_model")
print("="*70 + "\n")
