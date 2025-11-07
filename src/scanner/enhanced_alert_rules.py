"""
Enhanced Alert Rules Engine with ML Integration

This module extends the basic alert rules engine to collaborate with
the improved ML detector (90.6% accuracy) for comprehensive threat detection.

Features:
- Combined ML + Rules scoring
- ML-assisted rule suggestions
- Rule effectiveness tracking
- False positive feedback loop
- Automatic rule refinement
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class EnhancedAlertRule:
    """Alert rule with ML integration capabilities"""

    def __init__(self, rule_data: Dict[str, Any]):
        # Basic rule properties
        self.id = rule_data.get('id', 'unknown')
        self.name = rule_data.get('name', 'Unnamed Rule')
        self.description = rule_data.get('description', '')
        self.enabled = rule_data.get('enabled', True)
        self.severity = rule_data.get('severity', 'MEDIUM')
        self.category = rule_data.get('category', 'CUSTOM_RULE')
        self.conditions = rule_data.get('conditions', {})

        # ML integration properties
        self.ml_weight = rule_data.get('ml_weight', 1.0)  # How much to trust ML for this rule
        self.require_ml_confirmation = rule_data.get('require_ml_confirmation', False)
        self.auto_refine = rule_data.get('auto_refine', False)

        # Tracking for effectiveness
        self.true_positives = 0
        self.false_positives = 0
        self.ml_agreements = 0
        self.ml_disagreements = 0
        self.last_triggered = None

        # Event tracking for rate-based rules
        self.event_tracker = defaultdict(list)

    def evaluate(self, packet_data: Dict[str, Any], ml_result: Optional[Dict] = None) -> Tuple[bool, float]:
        """
        Evaluate packet against rule with ML collaboration.

        Args:
            packet_data: Packet information
            ml_result: ML detection result (if available)

        Returns:
            (triggered, confidence): Whether rule triggered and confidence score (0-1)
        """
        if not self.enabled:
            return False, 0.0

        # Basic rule evaluation
        rule_triggered = self._evaluate_conditions(packet_data)

        if not rule_triggered:
            return False, 0.0

        # Calculate base confidence from rule
        base_confidence = self._calculate_rule_confidence()

        # Integrate with ML if available
        if ml_result:
            final_confidence = self._integrate_ml_result(base_confidence, ml_result)

            # Track ML agreement/disagreement
            if ml_result.get('is_attack'):
                self.ml_agreements += 1
            else:
                self.ml_disagreements += 1
        else:
            final_confidence = base_confidence

        # Check if ML confirmation required
        if self.require_ml_confirmation:
            if not ml_result or not ml_result.get('is_attack'):
                return False, 0.0

        self.last_triggered = datetime.now()
        return True, final_confidence

    def _evaluate_conditions(self, packet_data: Dict[str, Any]) -> bool:
        """Evaluate basic rule conditions"""
        condition_type = self.conditions.get('type')

        try:
            if condition_type == 'port':
                return self._check_port(packet_data)
            elif condition_type == 'ip_blacklist':
                return self._check_ip_blacklist(packet_data)
            elif condition_type == 'connection_rate':
                return self._check_connection_rate(packet_data)
            elif condition_type == 'packet_rate':
                return self._check_packet_rate(packet_data)
            elif condition_type == 'dns_queries':
                return self._check_dns_rate(packet_data)
            else:
                return False
        except Exception as e:
            logger.error(f"Error evaluating rule {self.id}: {e}")
            return False

    def _check_port(self, packet_data: Dict[str, Any]) -> bool:
        """Check port-based conditions"""
        ports = self.conditions.get('values', [])
        dst_port = packet_data.get('dst_port')
        operator = self.conditions.get('operator', 'in')

        if operator == 'in':
            return dst_port in ports
        elif operator == 'not_in':
            return dst_port not in ports
        return False

    def _check_ip_blacklist(self, packet_data: Dict[str, Any]) -> bool:
        """Check if IP is in blacklist"""
        blacklist = self.conditions.get('values', [])
        if not blacklist:
            return False

        src_ip = packet_data.get('src_ip')
        dst_ip = packet_data.get('dst_ip')

        return src_ip in blacklist or dst_ip in blacklist

    def _check_connection_rate(self, packet_data: Dict[str, Any]) -> bool:
        """Check connection rate from single IP"""
        src_ip = packet_data.get('src_ip')
        if not src_ip:
            return False

        threshold = self.conditions.get('value', 20)
        timeframe = self.conditions.get('timeframe', 60)
        current_time = time.time()

        self.event_tracker[src_ip].append(current_time)
        self.event_tracker[src_ip] = [
            t for t in self.event_tracker[src_ip]
            if current_time - t <= timeframe
        ]

        event_count = len(self.event_tracker[src_ip])

        # Alert once when threshold first exceeded
        if event_count == threshold + 1:
            return True
        return False

    def _check_packet_rate(self, packet_data: Dict[str, Any]) -> bool:
        """Check packet rate from single device"""
        src_ip = packet_data.get('src_ip')
        if not src_ip:
            return False

        threshold = self.conditions.get('value', 1000)
        timeframe = self.conditions.get('timeframe', 60)
        current_time = time.time()
        key = f"packet_{src_ip}"

        self.event_tracker[key].append(current_time)
        self.event_tracker[key] = [
            t for t in self.event_tracker[key]
            if current_time - t <= timeframe
        ]

        event_count = len(self.event_tracker[key])

        if event_count == threshold + 1:
            return True
        return False

    def _check_dns_rate(self, packet_data: Dict[str, Any]) -> bool:
        """Check DNS query rate"""
        if packet_data.get('dst_port') != 53:
            return False

        src_ip = packet_data.get('src_ip')
        if not src_ip:
            return False

        threshold = self.conditions.get('value', 50)
        timeframe = self.conditions.get('timeframe', 60)
        current_time = time.time()
        key = f"dns_{src_ip}"

        self.event_tracker[key].append(current_time)
        self.event_tracker[key] = [
            t for t in self.event_tracker[key]
            if current_time - t <= timeframe
        ]

        event_count = len(self.event_tracker[key])

        if event_count == threshold + 1:
            return True
        return False

    def _calculate_rule_confidence(self) -> float:
        """Calculate confidence based on rule type and historical accuracy"""
        base_confidence = {
            'CRITICAL': 0.9,
            'HIGH': 0.8,
            'MEDIUM': 0.6,
            'LOW': 0.4
        }.get(self.severity, 0.5)

        # Adjust based on historical accuracy
        if self.true_positives + self.false_positives > 10:
            accuracy = self.true_positives / (self.true_positives + self.false_positives)
            base_confidence = (base_confidence + accuracy) / 2

        return base_confidence

    def _integrate_ml_result(self, rule_confidence: float, ml_result: Dict) -> float:
        """
        Combine rule confidence with ML prediction.

        Uses weighted average based on ml_weight parameter.
        """
        ml_confidence = ml_result.get('attack_probability', 0.5)

        # Weighted combination
        combined = (rule_confidence * (1 - self.ml_weight) +
                   ml_confidence * self.ml_weight)

        # Boost confidence if both agree
        if ml_result.get('is_attack') and rule_confidence > 0.5:
            combined = min(1.0, combined * 1.2)

        return combined

    def record_feedback(self, was_true_positive: bool):
        """Record feedback for rule effectiveness tracking"""
        if was_true_positive:
            self.true_positives += 1
        else:
            self.false_positives += 1

    def get_effectiveness_score(self) -> float:
        """Calculate rule effectiveness (0-1)"""
        total = self.true_positives + self.false_positives
        if total == 0:
            return 0.5  # No data yet

        accuracy = self.true_positives / total

        # Factor in ML agreement rate
        ml_total = self.ml_agreements + self.ml_disagreements
        if ml_total > 0:
            ml_agreement_rate = self.ml_agreements / ml_total
            # Combine accuracy with ML agreement
            return (accuracy * 0.7 + ml_agreement_rate * 0.3)

        return accuracy


class EnhancedAlertRulesEngine:
    """
    Alert Rules Engine with ML Integration.

    Collaborates with ImprovedMLDetector for comprehensive threat detection.
    """

    def __init__(self, config_path: str = "config/alert_rules.json"):
        self.config_path = Path(config_path)
        self.rules: List[EnhancedAlertRule] = []
        self.enabled = True
        self.logger = logging.getLogger(__name__)

        # ML integration
        self.ml_detector = None
        self.combined_detections = []

        # Statistics
        self.stats = {
            'total_evaluations': 0,
            'rule_only_detections': 0,
            'ml_only_detections': 0,
            'combined_detections': 0,
            'ml_enhanced_detections': 0
        }

        self.load_rules()

    def set_ml_detector(self, ml_detector):
        """Set the ML detector for integration"""
        self.ml_detector = ml_detector
        self.logger.info("ML detector integrated with alert rules engine")

    def load_rules(self) -> bool:
        """Load rules from configuration"""
        try:
            if not self.config_path.exists():
                self.logger.warning(f"Alert rules config not found: {self.config_path}")
                self._create_default_config()
                return False

            with open(self.config_path, 'r') as f:
                config = json.load(f)

            self.enabled = config.get('enabled', True)

            self.rules = []
            for rule_data in config.get('rules', []):
                rule = EnhancedAlertRule(rule_data)
                self.rules.append(rule)

            self.logger.info(f"Loaded {len(self.rules)} custom alert rules with ML integration")
            return True

        except Exception as e:
            self.logger.error(f"Error loading alert rules: {e}")
            return False

    def _create_default_config(self):
        """Create default configuration with ML-integrated rules"""
        default_config = {
            "enabled": True,
            "ml_integration": {
                "enabled": True,
                "confidence_threshold": 0.7,
                "auto_refine_rules": False
            },
            "rules": [
                {
                    "id": "rule_001",
                    "name": "SSH Brute Force Detection",
                    "description": "Detect brute force attacks on SSH (ML-enhanced)",
                    "enabled": True,
                    "severity": "CRITICAL",
                    "category": "BRUTE_FORCE",
                    "ml_weight": 0.6,
                    "require_ml_confirmation": False,
                    "conditions": {
                        "type": "connection_rate",
                        "operator": "greater_than",
                        "value": 20,
                        "timeframe": 60
                    }
                },
                {
                    "id": "rule_002",
                    "name": "Suspicious Port Access",
                    "description": "Access to sensitive OT/ICS ports (ML-verified)",
                    "enabled": True,
                    "severity": "HIGH",
                    "category": "SUSPICIOUS_ACCESS",
                    "ml_weight": 0.7,
                    "require_ml_confirmation": True,
                    "conditions": {
                        "type": "port",
                        "operator": "in",
                        "values": [22, 23, 3389, 502, 102, 20000, 44818, 47808]
                    }
                }
            ]
        }

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)

        self.logger.info(f"Created default alert rules config: {self.config_path}")

    def evaluate_packet(self, packet_data: Dict[str, Any],
                       ml_result: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Evaluate packet against all rules with ML collaboration.

        Args:
            packet_data: Packet information
            ml_result: ML detection result (from ImprovedMLDetector)

        Returns:
            List of triggered alerts with combined confidence scores
        """
        if not self.enabled:
            return []

        self.stats['total_evaluations'] += 1
        triggered_alerts = []

        for rule in self.rules:
            triggered, confidence = rule.evaluate(packet_data, ml_result)

            if triggered:
                # Determine detection source
                if ml_result and ml_result.get('is_attack'):
                    self.stats['combined_detections'] += 1
                    detection_source = "Rule + ML"
                else:
                    self.stats['rule_only_detections'] += 1
                    detection_source = "Rule Only"

                alert = {
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'description': rule.description,
                    'severity': rule.severity,
                    'category': rule.category,
                    'source_ip': packet_data.get('src_ip'),
                    'dest_ip': packet_data.get('dst_ip'),
                    'dest_port': packet_data.get('dst_port'),
                    'confidence': confidence,
                    'detection_source': detection_source,
                    'ml_enhanced': ml_result is not None,
                    'ml_agreement': ml_result.get('is_attack', False) if ml_result else None,
                    'ml_confidence': ml_result.get('attack_probability', 0) if ml_result else None
                }
                triggered_alerts.append(alert)

                self.logger.info(
                    f"Custom rule triggered: {rule.name} ({rule.severity}) - "
                    f"{packet_data.get('src_ip')} -> {packet_data.get('dst_ip')}:{packet_data.get('dst_port')} "
                    f"[Confidence: {confidence:.2f}, Source: {detection_source}]"
                )

        # Track ML-only detections (ML detected but no rule matched)
        if ml_result and ml_result.get('is_attack') and not triggered_alerts:
            self.stats['ml_only_detections'] += 1

        return triggered_alerts

    def get_rule_by_id(self, rule_id: str) -> Optional[EnhancedAlertRule]:
        """Get rule by ID"""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None

    def suggest_rule_from_ml_patterns(self, ml_detections: List[Dict]) -> List[Dict]:
        """
        Analyze ML detections and suggest new rules.

        Args:
            ml_detections: Recent ML detection results

        Returns:
            List of suggested rules
        """
        if not ml_detections:
            return []

        suggestions = []

        # Analyze for common patterns
        port_patterns = defaultdict(int)
        ip_patterns = defaultdict(int)

        for detection in ml_detections[-100:]:  # Last 100 detections
            dst_port = detection.get('dst_port')
            if dst_port:
                port_patterns[dst_port] += 1

            src_ip = detection.get('src_ip')
            if src_ip:
                ip_patterns[src_ip] += 1

        # Suggest port-based rules
        for port, count in port_patterns.items():
            if count >= 10:  # Threshold for suggestion
                suggestions.append({
                    'type': 'port',
                    'name': f"ML-Suggested: Suspicious activity on port {port}",
                    'description': f"ML detected {count} attacks on port {port}. Consider creating a rule.",
                    'severity': 'HIGH',
                    'conditions': {
                        'type': 'port',
                        'operator': 'in',
                        'values': [port]
                    },
                    'ml_weight': 0.8,
                    'confidence': min(0.9, count / 20)
                })

        # Suggest IP blacklist rules
        for ip, count in ip_patterns.items():
            if count >= 15:  # Higher threshold for IP blacklist
                suggestions.append({
                    'type': 'ip_blacklist',
                    'name': f"ML-Suggested: Block suspicious IP {ip}",
                    'description': f"ML detected {count} attacks from {ip}. Consider blacklisting.",
                    'severity': 'CRITICAL',
                    'conditions': {
                        'type': 'ip_blacklist',
                        'operator': 'in',
                        'values': [ip]
                    },
                    'ml_weight': 0.9,
                    'confidence': min(0.95, count / 25)
                })

        return suggestions

    def get_rule_summary(self) -> Dict[str, Any]:
        """Get summary of loaded rules with ML integration stats"""
        enabled_count = sum(1 for r in self.rules if r.enabled)
        ml_integrated = sum(1 for r in self.rules if r.ml_weight > 0.5)
        ml_confirmed_only = sum(1 for r in self.rules if r.require_ml_confirmation)

        by_severity = defaultdict(int)
        for rule in self.rules:
            if rule.enabled:
                by_severity[rule.severity] += 1

        # Calculate rule effectiveness
        effectiveness_scores = [
            r.get_effectiveness_score()
            for r in self.rules
            if r.true_positives + r.false_positives > 0
        ]
        avg_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores) if effectiveness_scores else 0.5

        return {
            'total_rules': len(self.rules),
            'enabled_rules': enabled_count,
            'ml_integrated_rules': ml_integrated,
            'ml_confirmation_required': ml_confirmed_only,
            'by_severity': dict(by_severity),
            'engine_enabled': self.enabled,
            'ml_detector_available': self.ml_detector is not None,
            'statistics': self.stats,
            'average_effectiveness': avg_effectiveness
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics"""
        total = self.stats['total_evaluations']
        if total == 0:
            return self.stats

        return {
            **self.stats,
            'rule_only_percentage': (self.stats['rule_only_detections'] / total) * 100,
            'ml_only_percentage': (self.stats['ml_only_detections'] / total) * 100,
            'combined_percentage': (self.stats['combined_detections'] / total) * 100
        }
