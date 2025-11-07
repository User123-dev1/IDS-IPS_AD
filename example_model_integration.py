"""
Example: Integrate Improved Model into IDS/IPS Application

This script shows how to load and use the trained model for real-time
network traffic classification.
"""

import pickle
import json
import pandas as pd
import numpy as np
from pathlib import Path

class ImprovedIDSDetector:
    """
    Improved IDS/IPS detector with 90.2% accuracy.

    Performance Metrics:
    - Accuracy: 90.2%
    - Precision: 86.4%
    - Recall: 97.6% (catches 97.6% of attacks!)
    - F1-Score: 91.6%
    """

    def __init__(self, model_dir='data/models'):
        """Load the trained model and its components."""
        self.model_dir = Path(model_dir)

        # Load model
        with open(self.model_dir / 'improved_ids_model.pkl', 'rb') as f:
            self.model = pickle.load(f)

        # Load scaler
        with open(self.model_dir / 'improved_ids_scaler.pkl', 'rb') as f:
            self.scaler = pickle.load(f)

        # Load required features list
        with open(self.model_dir / 'improved_ids_features.json', 'r') as f:
            self.features = json.load(f)

        # Load metadata
        with open(self.model_dir / 'improved_ids_metadata.json', 'r') as f:
            self.metadata = json.load(f)

        print(f"✓ Loaded model with {self.metadata['accuracy']:.1%} accuracy")
        print(f"✓ Using {len(self.features)} features")

    def extract_features(self, network_packet):
        """
        Extract features from a network packet.

        Args:
            network_packet: Dict with network traffic data

        Returns:
            pandas DataFrame with required features
        """
        # Create feature dictionary with defaults
        feature_dict = {}

        for feature_name in self.features:
            # Get feature from packet, default to 0 if missing
            feature_dict[feature_name] = network_packet.get(feature_name, 0)

        # Convert to DataFrame
        df = pd.DataFrame([feature_dict])

        # Handle missing/infinite values
        df = df.replace([np.inf, -np.inf], np.nan).fillna(0)

        return df

    def predict(self, network_packet):
        """
        Classify a network packet as 'Normal' or 'Attack'.

        Args:
            network_packet: Dict with network traffic features

        Returns:
            dict with prediction, probability, and threat level
        """
        # Extract features
        features = self.extract_features(network_packet)

        # Normalize features
        features_scaled = self.scaler.transform(features)

        # Predict
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]

        # Format result
        result = {
            'prediction': 'Attack' if prediction == 1 else 'Normal',
            'confidence': float(probabilities[prediction]),
            'attack_probability': float(probabilities[1]),
            'normal_probability': float(probabilities[0]),
            'threat_level': self._get_threat_level(probabilities[1])
        }

        return result

    def _get_threat_level(self, attack_prob):
        """Determine threat level based on attack probability."""
        if attack_prob >= 0.9:
            return 'CRITICAL'
        elif attack_prob >= 0.7:
            return 'HIGH'
        elif attack_prob >= 0.5:
            return 'MEDIUM'
        else:
            return 'LOW'

    def predict_batch(self, network_packets):
        """
        Classify multiple network packets efficiently.

        Args:
            network_packets: List of dicts with network traffic features

        Returns:
            List of prediction results
        """
        results = []

        for packet in network_packets:
            result = self.predict(packet)
            results.append(result)

        return results


# Example usage
if __name__ == '__main__':
    print("=" * 70)
    print("Improved IDS/IPS Detector - Integration Example")
    print("=" * 70)

    # Initialize detector
    detector = ImprovedIDSDetector()

    print("\nModel Performance:")
    print(f"  Accuracy:  {detector.metadata['accuracy']:.1%}")
    print(f"  Precision: {detector.metadata['precision']:.1%}")
    print(f"  Recall:    {detector.metadata['recall']:.1%}")
    print(f"  F1-Score:  {detector.metadata['f1_score']:.1%}")

    # Example 1: Normal traffic
    print("\n" + "=" * 70)
    print("Example 1: Normal Web Traffic")
    print("=" * 70)

    normal_packet = {
        'sttl': 64,
        'time_to_live': 64,
        'connection_state': 1,  # Established
        'rate': 100,
        'sbytes': 1024,
        'dbytes': 2048,
        'sload': 50.5,
        'byte_asymmetry': 0.3,
        'ttl_difference': 0,
        'ct_state_ttl': 5,
        'dttl': 64,
        # ... other features with defaults
    }

    result = detector.predict(normal_packet)
    print(f"Prediction:     {result['prediction']}")
    print(f"Confidence:     {result['confidence']:.1%}")
    print(f"Threat Level:   {result['threat_level']}")
    print(f"Attack Prob:    {result['attack_probability']:.1%}")

    # Example 2: Suspicious traffic (port scan pattern)
    print("\n" + "=" * 70)
    print("Example 2: Suspicious Traffic (Port Scan)")
    print("=" * 70)

    attack_packet = {
        'sttl': 128,
        'time_to_live': 128,
        'connection_state': 0,  # No connection established
        'rate': 1000,  # High packet rate
        'sbytes': 60,  # Small packets
        'dbytes': 0,   # No response
        'sload': 500.0,  # High load
        'byte_asymmetry': 1.0,  # Only outbound
        'ttl_difference': 64,  # TTL anomaly
        'ct_state_ttl': 100,  # Many connection attempts
        'dttl': 0,
        # ... other features
    }

    result = detector.predict(attack_packet)
    print(f"Prediction:     {result['prediction']}")
    print(f"Confidence:     {result['confidence']:.1%}")
    print(f"Threat Level:   {result['threat_level']}")
    print(f"Attack Prob:    {result['attack_probability']:.1%}")

    # Example 3: Batch processing
    print("\n" + "=" * 70)
    print("Example 3: Batch Processing (100 packets)")
    print("=" * 70)

    # Simulate 100 packets
    packets = [normal_packet] * 70 + [attack_packet] * 30
    results = detector.predict_batch(packets)

    attacks_detected = sum(1 for r in results if r['prediction'] == 'Attack')
    print(f"Total packets:     100")
    print(f"Attacks detected:  {attacks_detected}")
    print(f"Normal traffic:    {100 - attacks_detected}")

    print("\n" + "=" * 70)
    print("Integration complete! Model ready for deployment.")
    print("=" * 70)
