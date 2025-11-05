"""
Custom Alert Rules Engine - Integrated with NetworkMonitor
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import time

logger = logging.getLogger(__name__)


class AlertRule:
    """Single alert rule"""
    
    def __init__(self, rule_data: Dict[str, Any]):
        self.id = rule_data.get('id', 'unknown')
        self.name = rule_data.get('name', 'Unnamed Rule')
        self.description = rule_data.get('description', '')
        self.enabled = rule_data.get('enabled', True)
        self.severity = rule_data.get('severity', 'MEDIUM')
        self.category = rule_data.get('category', 'CUSTOM_RULE')
        self.conditions = rule_data.get('conditions', {})
        
        # Tracking for rate-based rules
        self.event_tracker = defaultdict(list)
        
    def evaluate(self, packet_data: Dict[str, Any]) -> bool:
        """Check if packet matches this rule"""
        if not self.enabled:
            return False
            
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
        if not blacklist:  # Empty blacklist = no alerts
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
        
        # Add current event
        self.event_tracker[src_ip].append(current_time)
        
        # Remove old events
        self.event_tracker[src_ip] = [
            t for t in self.event_tracker[src_ip]
            if current_time - t <= timeframe
        ]
        
        # Check threshold
        event_count = len(self.event_tracker[src_ip])
        
        # Only alert once when threshold first exceeded
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
        
        # Alert once when threshold exceeded
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


class AlertRulesEngine:
    """Manages custom alert rules"""
    
    def __init__(self, config_path: str = "config/alert_rules.json"):
        self.config_path = Path(config_path)
        self.rules: List[AlertRule] = []
        self.enabled = True
        self.logger = logging.getLogger(__name__)
        
        self.load_rules()
    
    def load_rules(self) -> bool:
        """Load rules from configuration"""
        try:
            if not self.config_path.exists():
                self.logger.warning(f"Alert rules config not found: {self.config_path}")
                return False
            
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            self.enabled = config.get('enabled', True)
            
            self.rules = []
            for rule_data in config.get('rules', []):
                rule = AlertRule(rule_data)
                self.rules.append(rule)
            
            self.logger.info(f"Loaded {len(self.rules)} custom alert rules")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading alert rules: {e}")
            return False
    
    def evaluate_packet(self, packet_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate packet against all rules, return triggered alerts"""
        if not self.enabled:
            return []
        
        triggered_alerts = []
        
        for rule in self.rules:
            if rule.evaluate(packet_data):
                alert = {
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'description': rule.description,
                    'severity': rule.severity,
                    'category': rule.category,
                    'source_ip': packet_data.get('src_ip'),
                    'dest_ip': packet_data.get('dst_ip'),
                    'dest_port': packet_data.get('dst_port')
                }
                triggered_alerts.append(alert)
                
                self.logger.info(
                    f"Custom rule triggered: {rule.name} ({rule.severity}) - "
                    f"{packet_data.get('src_ip')} -> {packet_data.get('dst_ip')}:{packet_data.get('dst_port')}"
                )
        
        return triggered_alerts
    
    def get_rule_summary(self) -> Dict[str, Any]:
        """Get summary of loaded rules"""
        enabled_count = sum(1 for r in self.rules if r.enabled)
        
        by_severity = defaultdict(int)
        for rule in self.rules:
            if rule.enabled:
                by_severity[rule.severity] += 1
        
        return {
            'total_rules': len(self.rules),
            'enabled_rules': enabled_count,
            'by_severity': dict(by_severity),
            'engine_enabled': self.enabled
        }
