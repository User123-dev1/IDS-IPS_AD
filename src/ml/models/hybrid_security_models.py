#!/usr/bin/env python3
"""
Hybrid ML Security Models for OT/ICS Networks
Advanced threat detection using multiple ML techniques
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json

try:
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.svm import SVC
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. ML features limited.")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("Warning: XGBoost not available. Advanced classification disabled.")


class AnomalyDetectionHybrid:
    """
    Hybrid: Isolation Forest (unsupervised) + Random Forest (supervised)
    Purpose: Detect unusual network behavior and zero-day attacks
    """

    def __init__(self):
        self.isolation_forest = None
        self.random_forest = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.baseline_established = False

        if SKLEARN_AVAILABLE:
            # Isolation Forest for anomaly detection (unsupervised)
            self.isolation_forest = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42,
                n_estimators=100
            )

            # Random Forest for classification (supervised)
            self.random_forest = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=10
            )

    def establish_baseline(self, normal_traffic: np.ndarray):
        """
        Establish baseline from normal network traffic
        Args:
            normal_traffic: Array of feature vectors from normal devices
        """
        if not SKLEARN_AVAILABLE:
            return False

        try:
            # Scale features
            scaled_traffic = self.scaler.fit_transform(normal_traffic)

            # Train Isolation Forest on normal traffic
            self.isolation_forest.fit(scaled_traffic)

            self.baseline_established = True
            print(f"✓ Anomaly detection baseline established ({len(normal_traffic)} samples)")
            return True

        except Exception as e:
            print(f"Error establishing baseline: {e}")
            return False

    def train_classifier(self, X_train: np.ndarray, y_train: np.ndarray):
        """
        Train supervised Random Forest classifier
        Args:
            X_train: Training feature vectors
            y_train: Labels (0=normal, 1=anomaly)
        """
        if not SKLEARN_AVAILABLE:
            return False

        try:
            scaled_X = self.scaler.transform(X_train)
            self.random_forest.fit(scaled_X, y_train)
            self.is_trained = True
            print(f"✓ Random Forest classifier trained ({len(X_train)} samples)")
            return True

        except Exception as e:
            print(f"Error training classifier: {e}")
            return False

    def detect_anomaly(self, features: np.ndarray) -> Dict:
        """
        Detect if traffic is anomalous using hybrid approach
        Returns: Dict with anomaly_detected, confidence, anomaly_type
        """
        if not SKLEARN_AVAILABLE or not self.baseline_established:
            return {
                'anomaly_detected': False,
                'confidence': 0.0,
                'anomaly_type': 'Unknown',
                'severity': 'LOW'
            }

        try:
            # Ensure 2D array
            if features.ndim == 1:
                features = features.reshape(1, -1)

            scaled_features = self.scaler.transform(features)

            # Step 1: Isolation Forest (unsupervised anomaly detection)
            if_prediction = self.isolation_forest.predict(scaled_features)[0]
            if_score = self.isolation_forest.score_samples(scaled_features)[0]

            # Step 2: Random Forest (supervised classification) if trained
            rf_prediction = 0
            rf_confidence = 0.0
            if self.is_trained:
                rf_prediction = self.random_forest.predict(scaled_features)[0]
                rf_proba = self.random_forest.predict_proba(scaled_features)[0]
                rf_confidence = max(rf_proba)

            # Combine predictions
            is_anomaly = (if_prediction == -1)  # -1 = anomaly in Isolation Forest

            # Determine anomaly type
            if is_anomaly and self.is_trained and rf_prediction == 1:
                anomaly_type = "Known Attack Pattern"
                severity = "HIGH"
            elif is_anomaly and if_score < -0.5:
                anomaly_type = "Zero-Day Threat"
                severity = "CRITICAL"
            elif is_anomaly:
                anomaly_type = "Unusual Behavior"
                severity = "MEDIUM"
            else:
                anomaly_type = "Normal"
                severity = "LOW"

            # Calculate combined confidence
            confidence = abs(if_score) * 0.6 + rf_confidence * 0.4

            return {
                'anomaly_detected': is_anomaly,
                'confidence': float(confidence),
                'anomaly_type': anomaly_type,
                'severity': severity,
                'if_score': float(if_score),
                'rf_prediction': int(rf_prediction) if self.is_trained else None
            }

        except Exception as e:
            print(f"Error detecting anomaly: {e}")
            return {
                'anomaly_detected': False,
                'confidence': 0.0,
                'anomaly_type': 'Error',
                'severity': 'LOW'
            }


class ThreatClassificationHybrid:
    """
    Hybrid: XGBoost (static features) + LSTM placeholder (time-series)
    Purpose: Classify threats based on network behavior
    """

    def __init__(self):
        self.xgb_model = None
        self.scaler = StandardScaler()
        self.is_trained = False

        if XGBOOST_AVAILABLE:
            self.xgb_model = xgb.XGBClassifier(
                max_depth=6,
                learning_rate=0.1,
                n_estimators=100,
                objective='multi:softmax',
                num_class=5,  # 5 threat classes
                random_state=42
            )

    def train(self, X_train: np.ndarray, y_train: np.ndarray):
        """
        Train XGBoost classifier
        Args:
            X_train: Static features (ports, protocols, vendors)
            y_train: Threat labels (0=benign, 1=scan, 2=exploit, 3=dos, 4=malware)
        """
        if not XGBOOST_AVAILABLE:
            print("XGBoost not available")
            return False

        try:
            scaled_X = self.scaler.fit_transform(X_train)
            self.xgb_model.fit(scaled_X, y_train)
            self.is_trained = True
            print(f"✓ XGBoost threat classifier trained ({len(X_train)} samples)")
            return True

        except Exception as e:
            print(f"Error training XGBoost: {e}")
            return False

    def classify_threat(self, features: np.ndarray) -> Dict:
        """
        Classify threat level and type
        Returns: Dict with threat_class, confidence, threat_name
        """
        if not XGBOOST_AVAILABLE or not self.is_trained:
            return {
                'threat_detected': False,
                'threat_class': 0,
                'threat_name': 'Unknown',
                'confidence': 0.0
            }

        try:
            if features.ndim == 1:
                features = features.reshape(1, -1)

            scaled_features = self.scaler.transform(features)

            # Predict threat class
            threat_class = self.xgb_model.predict(scaled_features)[0]
            probabilities = self.xgb_model.predict_proba(scaled_features)[0]
            confidence = float(max(probabilities))

            # Map threat class to name
            threat_names = {
                0: 'Benign',
                1: 'Port Scan',
                2: 'Exploit Attempt',
                3: 'Denial of Service',
                4: 'Malware Activity'
            }

            threat_name = threat_names.get(threat_class, 'Unknown')
            threat_detected = (threat_class > 0)

            return {
                'threat_detected': threat_detected,
                'threat_class': int(threat_class),
                'threat_name': threat_name,
                'confidence': confidence,
                'severity': 'CRITICAL' if threat_class >= 3 else 'HIGH' if threat_class >= 2 else 'MEDIUM'
            }

        except Exception as e:
            print(f"Error classifying threat: {e}")
            return {
                'threat_detected': False,
                'threat_class': 0,
                'threat_name': 'Error',
                'confidence': 0.0
            }


class VulnerabilityPredictor:
    """
    Hybrid: Decision Trees + Neural Network placeholder
    Purpose: Predict exploitation likelihood based on CVE data
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.is_trained = False
        self.cve_database = {}

        if SKLEARN_AVAILABLE:
            from sklearn.tree import DecisionTreeClassifier
            self.dt_model = DecisionTreeClassifier(
                max_depth=8,
                random_state=42,
                min_samples_split=5
            )

    def load_cve_database(self, cve_data: Dict):
        """Load CVE database for vulnerability matching"""
        self.cve_database = cve_data
        print(f"✓ Loaded {len(cve_data)} CVE entries")

    def train(self, X_train: np.ndarray, y_train: np.ndarray):
        """
        Train vulnerability prediction model
        Args:
            X_train: Device features (services, versions, configs)
            y_train: Exploitation likelihood (0=low, 1=medium, 2=high)
        """
        if not SKLEARN_AVAILABLE:
            return False

        try:
            scaled_X = self.scaler.fit_transform(X_train)
            self.dt_model.fit(scaled_X, y_train)
            self.is_trained = True
            print(f"✓ Vulnerability predictor trained ({len(X_train)} samples)")
            return True

        except Exception as e:
            print(f"Error training predictor: {e}")
            return False

    def predict_vulnerability(self, features: np.ndarray, services: List[str]) -> Dict:
        """
        Predict vulnerability exploitation likelihood
        Returns: Dict with risk_score, matched_cves, recommendations
        """
        if not SKLEARN_AVAILABLE:
            return {
                'risk_score': 0.0,
                'risk_level': 'UNKNOWN',
                'matched_cves': [],
                'exploitable': False
            }

        try:
            # Match services against CVE database
            matched_cves = []
            for service in services:
                for cve_id, cve_info in self.cve_database.items():
                    if service.lower() in cve_info.get('affected_services', []):
                        matched_cves.append({
                            'cve_id': cve_id,
                            'severity': cve_info.get('severity', 'MEDIUM'),
                            'cvss_score': cve_info.get('cvss_score', 5.0)
                        })

            # Predict using Decision Tree if trained
            risk_score = 0.0
            if self.is_trained and features is not None:
                if features.ndim == 1:
                    features = features.reshape(1, -1)
                scaled_features = self.scaler.transform(features)
                prediction = self.dt_model.predict(scaled_features)[0]
                risk_score = float(prediction) / 2.0  # Normalize to 0-1

            # Adjust risk based on CVEs
            if matched_cves:
                max_cvss = max([cve['cvss_score'] for cve in matched_cves])
                cve_risk = max_cvss / 10.0  # Normalize CVSS to 0-1
                risk_score = max(risk_score, cve_risk)

            # Determine risk level
            if risk_score >= 0.7:
                risk_level = 'CRITICAL'
            elif risk_score >= 0.5:
                risk_level = 'HIGH'
            elif risk_score >= 0.3:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'

            return {
                'risk_score': float(risk_score),
                'risk_level': risk_level,
                'matched_cves': matched_cves[:5],  # Top 5
                'exploitable': risk_score >= 0.5,
                'cve_count': len(matched_cves)
            }

        except Exception as e:
            print(f"Error predicting vulnerability: {e}")
            return {
                'risk_score': 0.0,
                'risk_level': 'UNKNOWN',
                'matched_cves': [],
                'exploitable': False
            }


class ProtocolAnalysisHybrid:
    """
    Hybrid: K-Means Clustering + SVM
    Purpose: Detect protocol anomalies in OT/ICS communications
    """

    def __init__(self, n_clusters=5):
        self.n_clusters = n_clusters
        self.kmeans = None
        self.svm = None
        self.scaler = StandardScaler()
        self.is_trained = False

        if SKLEARN_AVAILABLE:
            self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            self.svm = SVC(kernel='rbf', probability=True, random_state=42)

    def train_clustering(self, protocol_features: np.ndarray):
        """
        Train K-Means to group similar device behaviors
        Args:
            protocol_features: Protocol-specific features (packet sizes, timing, etc.)
        """
        if not SKLEARN_AVAILABLE:
            return False

        try:
            scaled_features = self.scaler.fit_transform(protocol_features)
            self.kmeans.fit(scaled_features)
            print(f"✓ K-Means clustering trained ({self.n_clusters} clusters)")
            return True

        except Exception as e:
            print(f"Error training clustering: {e}")
            return False

    def train_classifier(self, X_train: np.ndarray, y_train: np.ndarray):
        """
        Train SVM for protocol anomaly classification
        Args:
            X_train: Protocol features
            y_train: Labels (0=normal, 1=anomaly)
        """
        if not SKLEARN_AVAILABLE:
            return False

        try:
            scaled_X = self.scaler.transform(X_train)
            self.svm.fit(scaled_X, y_train)
            self.is_trained = True
            print(f"✓ SVM protocol classifier trained ({len(X_train)} samples)")
            return True

        except Exception as e:
            print(f"Error training SVM: {e}")
            return False

    def analyze_protocol(self, features: np.ndarray, protocol_name: str) -> Dict:
        """
        Analyze protocol behavior for anomalies
        Returns: Dict with cluster_id, anomaly_detected, protocol_name
        """
        if not SKLEARN_AVAILABLE:
            return {
                'protocol': protocol_name,
                'anomaly_detected': False,
                'cluster_id': -1,
                'confidence': 0.0
            }

        try:
            if features.ndim == 1:
                features = features.reshape(1, -1)

            scaled_features = self.scaler.transform(features)

            # Cluster assignment
            cluster_id = -1
            if self.kmeans:
                cluster_id = int(self.kmeans.predict(scaled_features)[0])

            # Anomaly detection with SVM
            anomaly_detected = False
            confidence = 0.0
            if self.is_trained:
                prediction = self.svm.predict(scaled_features)[0]
                probabilities = self.svm.predict_proba(scaled_features)[0]
                confidence = float(max(probabilities))
                anomaly_detected = (prediction == 1)

            return {
                'protocol': protocol_name,
                'anomaly_detected': anomaly_detected,
                'cluster_id': cluster_id,
                'confidence': confidence,
                'severity': 'HIGH' if anomaly_detected and confidence > 0.8 else 'MEDIUM' if anomaly_detected else 'LOW'
            }

        except Exception as e:
            print(f"Error analyzing protocol: {e}")
            return {
                'protocol': protocol_name,
                'anomaly_detected': False,
                'cluster_id': -1,
                'confidence': 0.0
            }


# Integrated Hybrid Security System
class HybridSecuritySystem:
    """
    Integrated system combining all hybrid models
    """

    def __init__(self):
        self.anomaly_detector = AnomalyDetectionHybrid()
        self.threat_classifier = ThreatClassificationHybrid()
        self.vulnerability_predictor = VulnerabilityPredictor()
        self.protocol_analyzer = ProtocolAnalysisHybrid()

        # Sample CVE database (normally loaded from external source)
        self.init_cve_database()

    def init_cve_database(self):
        """Initialize with sample CVE data"""
        sample_cves = {
            'CVE-2023-1234': {
                'severity': 'CRITICAL',
                'cvss_score': 9.8,
                'affected_services': ['modbus', 'scada', 'ot'],
                'description': 'Remote code execution in Modbus protocol'
            },
            'CVE-2023-5678': {
                'severity': 'HIGH',
                'cvss_score': 8.1,
                'affected_services': ['ethernet/ip', 'plc'],
                'description': 'Authentication bypass in EtherNet/IP'
            },
            'CVE-2023-9012': {
                'severity': 'HIGH',
                'cvss_score': 7.5,
                'affected_services': ['dnp3', 'rtu'],
                'description': 'Buffer overflow in DNP3 implementation'
            }
        }
        self.vulnerability_predictor.load_cve_database(sample_cves)

    def train_all_models(self, training_data: Dict) -> Dict:
        """
        Train all models with provided training data
        Args:
            training_data: Dictionary containing training data for all models
                Format from OTTrainingDataGenerator.generate_complete_training_set()
        Returns:
            Dictionary with training results for each model
        """
        results = {
            'anomaly_detection': {'success': False, 'message': ''},
            'threat_classification': {'success': False, 'message': ''},
            'vulnerability_prediction': {'success': False, 'message': ''},
            'protocol_analysis': {'success': False, 'message': ''},
            'overall_success': False
        }

        print("\n" + "="*60)
        print("Training Hybrid Security Models")
        print("="*60)

        try:
            # 1. Train Anomaly Detection (Isolation Forest + Random Forest)
            print("\n[1/4] Training Anomaly Detection models...")
            if 'anomaly_detection' in training_data:
                data = training_data['anomaly_detection']

                # Train Isolation Forest with baseline
                baseline_success = self.anomaly_detector.establish_baseline(data['baseline'])

                # Train Random Forest classifier
                classifier_success = self.anomaly_detector.train_classifier(data['X'], data['y'])

                if baseline_success and classifier_success:
                    results['anomaly_detection']['success'] = True
                    results['anomaly_detection']['message'] = 'Successfully trained'
                    print("   ✓ Anomaly detection models trained")
                else:
                    results['anomaly_detection']['message'] = 'Training failed'
                    print("   ✗ Anomaly detection training failed")

            # 2. Train Threat Classification (XGBoost)
            print("\n[2/4] Training Threat Classification model...")
            if 'threat_classification' in training_data:
                data = training_data['threat_classification']

                threat_success = self.threat_classifier.train(data['X'], data['y'])

                if threat_success:
                    results['threat_classification']['success'] = True
                    results['threat_classification']['message'] = 'Successfully trained'
                    print("   ✓ Threat classification model trained")
                else:
                    results['threat_classification']['message'] = 'Training failed'
                    print("   ✗ Threat classification training failed")

            # 3. Train Vulnerability Predictor (Decision Trees)
            print("\n[3/4] Training Vulnerability Prediction model...")
            if 'vulnerability_prediction' in training_data:
                data = training_data['vulnerability_prediction']

                vuln_success = self.vulnerability_predictor.train(data['X'], data['y'])

                if vuln_success:
                    results['vulnerability_prediction']['success'] = True
                    results['vulnerability_prediction']['message'] = 'Successfully trained'
                    print("   ✓ Vulnerability prediction model trained")
                else:
                    results['vulnerability_prediction']['message'] = 'Training failed'
                    print("   ✗ Vulnerability prediction training failed")

            # 4. Train Protocol Analysis (K-Means + SVM)
            print("\n[4/4] Training Protocol Analysis models...")
            if 'protocol_analysis' in training_data:
                data = training_data['protocol_analysis']

                # Train K-Means clustering
                cluster_success = self.protocol_analyzer.train_clustering(data['baseline'])

                # Train SVM classifier
                svm_success = self.protocol_analyzer.train_classifier(data['X'], data['y'])

                if cluster_success and svm_success:
                    results['protocol_analysis']['success'] = True
                    results['protocol_analysis']['message'] = 'Successfully trained'
                    print("   ✓ Protocol analysis models trained")
                else:
                    results['protocol_analysis']['message'] = 'Training failed'
                    print("   ✗ Protocol analysis training failed")

            # Check overall success
            all_success = all(results[key]['success'] for key in results if key != 'overall_success')
            results['overall_success'] = all_success

            print("\n" + "="*60)
            if all_success:
                print("All Models Trained Successfully!")
            else:
                print("Some Models Failed to Train (see details above)")
            print("="*60 + "\n")

            return results

        except Exception as e:
            print(f"\n✗ Training error: {e}")
            results['error'] = str(e)
            return results

    def is_trained(self) -> Dict[str, bool]:
        """Check training status of all models"""
        return {
            'anomaly_detection': self.anomaly_detector.is_trained and self.anomaly_detector.baseline_established,
            'threat_classification': self.threat_classifier.is_trained,
            'vulnerability_prediction': self.vulnerability_predictor.is_trained,
            'protocol_analysis': self.protocol_analyzer.is_trained
        }

    def analyze_device(self, device_features: np.ndarray, protocol: str = 'unknown',
                      services: List[str] = None) -> Dict:
        """
        Comprehensive device analysis using all hybrid models
        Returns: Combined analysis results
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'protocol': protocol,
            'anomaly_detection': {},
            'threat_classification': {},
            'vulnerability_prediction': {},
            'protocol_analysis': {},
            'overall_risk': 'LOW'
        }

        try:
            # 1. Anomaly Detection
            results['anomaly_detection'] = self.anomaly_detector.detect_anomaly(device_features)

            # 2. Threat Classification
            results['threat_classification'] = self.threat_classifier.classify_threat(device_features)

            # 3. Vulnerability Prediction
            if services:
                results['vulnerability_prediction'] = self.vulnerability_predictor.predict_vulnerability(
                    device_features, services
                )

            # 4. Protocol Analysis
            results['protocol_analysis'] = self.protocol_analyzer.analyze_protocol(
                device_features, protocol
            )

            # Determine overall risk
            risk_levels = []
            if results['anomaly_detection'].get('anomaly_detected'):
                risk_levels.append(results['anomaly_detection'].get('severity', 'LOW'))
            if results['threat_classification'].get('threat_detected'):
                risk_levels.append(results['threat_classification'].get('severity', 'LOW'))
            if results['vulnerability_prediction'].get('exploitable'):
                risk_levels.append(results['vulnerability_prediction'].get('risk_level', 'LOW'))
            if results['protocol_analysis'].get('anomaly_detected'):
                risk_levels.append(results['protocol_analysis'].get('severity', 'LOW'))

            # Highest risk level wins
            if 'CRITICAL' in risk_levels:
                results['overall_risk'] = 'CRITICAL'
            elif 'HIGH' in risk_levels:
                results['overall_risk'] = 'HIGH'
            elif 'MEDIUM' in risk_levels:
                results['overall_risk'] = 'MEDIUM'
            else:
                results['overall_risk'] = 'LOW'

            return results

        except Exception as e:
            print(f"Error in device analysis: {e}")
            results['error'] = str(e)
            return results


if __name__ == "__main__":
    # Test the hybrid security system
    print("=== Hybrid Security System Test ===\n")

    system = HybridSecuritySystem()

    # Simulate device features (11 features as in device_feature_extractor)
    test_features = np.array([
        10,  # port_count
        2,   # ot_protocol_count
        1,   # critical_protocol_present
        3,   # vulnerable_service_count
        1,   # critical_severity_vuln_count
        2,   # high_severity_vuln_count
        0,   # medium_severity_vuln_count
        1,   # has_http
        0,   # has_ssh
        1,   # has_telnet
        0.7  # device_exposure_score
    ])

    services = ['modbus', 'http', 'telnet']

    results = system.analyze_device(test_features, protocol='modbus', services=services)

    print(json.dumps(results, indent=2))
    print(f"\n✓ Overall Risk: {results['overall_risk']}")
