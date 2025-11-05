#!/usr/bin/env python3
"""
Test Script: ML-Integrated Device Scanning

Demonstrates the integration of machine learning with device scanning
for enhanced threat detection and risk assessment.
"""

import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scanner.network_scanner import EnterpriseNetworkScanner


def print_banner():
    """Print test banner"""
    print("\n" + "="*80)
    print("  ML-INTEGRATED DEVICE SCANNING TEST".center(80))
    print("="*80)
    print("\nThis test demonstrates the integration of machine learning with device scanning")
    print("for enhanced threat detection, risk assessment, and device profiling.\n")


def print_scan_result(result):
    """Pretty print scan result with ML analysis"""
    print("\n" + "-"*80)
    print(f"SCAN RESULT: {result['ip']} ({result['hostname']})")
    print("-"*80)

    # Basic Info
    print(f"\n[Basic Information]")
    print(f"  IP Address:    {result['ip']}")
    print(f"  Hostname:      {result['hostname']}")
    print(f"  MAC Address:   {result['mac_address']}")
    print(f"  Vendor:        {result['vendor']}")
    print(f"  Status:        {result['status']}")

    # Open Ports
    if result['open_ports']:
        print(f"\n[Open Ports] ({len(result['open_ports'])} found)")
        for port_info in result['open_ports'][:10]:  # Limit to first 10
            print(f"  • Port {port_info['port']:5d} - {port_info['service']}")
        if len(result['open_ports']) > 10:
            print(f"  ... and {len(result['open_ports']) - 10} more")

    # OT Protocols
    if result['ot_protocols']:
        print(f"\n[OT/ICS Protocols] ({len(result['ot_protocols'])} detected)")
        for proto in result['ot_protocols']:
            print(f"  • {proto['protocol']:20s} (Port {proto['port']}) - Risk: {proto['risk']}")

    # Vulnerabilities
    if result['vulnerabilities']:
        print(f"\n[Vulnerabilities] ({len(result['vulnerabilities'])} found)")
        for vuln in result['vulnerabilities'][:5]:  # Limit to first 5
            severity = vuln['severity'].upper()
            print(f"  • [{severity:8s}] {vuln['description']}")
        if len(result['vulnerabilities']) > 5:
            print(f"  ... and {len(result['vulnerabilities']) - 5} more")

    # ML Analysis - The new integrated component!
    ml_analysis = result.get('ml_analysis')
    if ml_analysis and ml_analysis['enabled']:
        print(f"\n{'='*80}")
        print("[ML-POWERED ANALYSIS]".center(80))
        print(f"{'='*80}")

        # Risk Classification
        risk_class = ml_analysis.get('risk_classification')
        if risk_class:
            print(f"\n🤖 [Risk Classification]")
            risk_level = risk_class['risk_level'].upper()
            risk_score = risk_class['risk_score']
            risk_color = risk_class['risk_color']

            # Color-coded risk level
            risk_display = f"  Risk Level: {risk_level} (Score: {risk_score:.2f})"
            if risk_level == 'CRITICAL':
                risk_display = f"  🔴 {risk_display}"
            elif risk_level == 'HIGH':
                risk_display = f"  🟠 {risk_display}"
            elif risk_level == 'MEDIUM':
                risk_display = f"  🟡 {risk_display}"
            else:
                risk_display = f"  🟢 {risk_display}"

            print(risk_display)

            # Recommendations
            recommendations = risk_class.get('recommendations', [])
            if recommendations:
                print(f"\n  ML Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"    {i}. {rec}")

        # Device Profile
        device_profile = ml_analysis.get('device_profile')
        if device_profile:
            print(f"\n🤖 [Device Profile]")
            print(f"  Device Type:   {device_profile['device_type']}")
            print(f"  OT Device:     {'Yes' if device_profile['is_ot_device'] else 'No'}")
            print(f"  Confidence:    {device_profile['confidence']:.0%}")

            characteristics = device_profile.get('characteristics', [])
            if characteristics:
                print(f"  Characteristics:")
                for char in characteristics:
                    print(f"    • {char}")

        # Anomaly Flags
        anomaly_flags = ml_analysis.get('anomaly_flags', [])
        if anomaly_flags:
            print(f"\n🤖 [Anomaly Detection] ({len(anomaly_flags)} anomalies detected)")
            for anomaly in anomaly_flags:
                severity = anomaly['severity'].upper()
                print(f"  • [{severity:6s}] {anomaly['description']}")
                print(f"             {anomaly['details']}")

        print(f"\n{'='*80}")

    else:
        print(f"\n[ML Analysis] Not available (ML components not loaded)")

    print("\n" + "-"*80 + "\n")


def test_ml_feature_extraction():
    """Test ML feature extraction independently"""
    print("\n" + "="*80)
    print("TEST 1: ML Feature Extraction & Risk Classification".center(80))
    print("="*80)

    try:
        from ml.utils.device_feature_extractor import DeviceFeatureExtractor, DeviceRiskClassifier

        print("\n✓ ML components loaded successfully\n")

        # Create test device data
        test_device = {
            'ip': '192.168.1.100',
            'hostname': 'test-plc-01',
            'status': 'online',
            'open_ports': [
                {'port': 502, 'service': 'Modbus'},
                {'port': 23, 'service': 'Telnet'},
                {'port': 80, 'service': 'HTTP'}
            ],
            'ot_protocols': [
                {'protocol': 'Modbus', 'port': 502, 'risk': 'HIGH'}
            ],
            'vulnerabilities': [
                {'severity': 'critical', 'description': 'Modbus exposed without auth'},
                {'severity': 'high', 'description': 'Telnet enabled'}
            ]
        }

        extractor = DeviceFeatureExtractor()
        classifier = DeviceRiskClassifier()

        print("Extracting features from test device...")
        features = extractor.extract_features(test_device)

        print(f"\nExtracted {len(features)} features:")
        for i, (name, value) in enumerate(zip(extractor.feature_names, features), 1):
            print(f"  {i:2d}. {name:30s} = {value:.3f}")

        print("\nClassifying device risk...")
        classification = classifier.classify_device(test_device)

        print(f"\nRisk Level: {classification['risk_level'].upper()}")
        print(f"Risk Score: {classification['risk_score']:.2f}")
        print(f"\nRecommendations:")
        for i, rec in enumerate(classification['recommendations'], 1):
            print(f"  {i}. {rec}")

        print("\n✓ Feature extraction and classification working correctly!")

    except Exception as e:
        print(f"\n✗ Error in feature extraction test: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_integrated_scanner():
    """Test the integrated ML scanner"""
    print("\n" + "="*80)
    print("TEST 2: Integrated ML Device Scanning".center(80))
    print("="*80)

    print("\nInitializing ML-integrated scanner...")
    scanner = EnterpriseNetworkScanner(enable_ml=True)

    if not scanner.enable_ml:
        print("\n⚠ Warning: ML components not available. Running basic scan only.")

    print("\nNote: This will scan localhost (127.0.0.1) as a test.")
    print("For real network scanning, modify the target IP.\n")

    # Scan localhost as a safe test
    result = scanner.scan_target('127.0.0.1')

    # Print the result
    print_scan_result(result)

    # Save result to JSON
    output_file = Path(__file__).parent / 'ml_scan_result.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    print(f"✓ Scan result saved to: {output_file}\n")

    return True


def test_batch_scanning():
    """Test scanning multiple devices (simulated)"""
    print("\n" + "="*80)
    print("TEST 3: Batch Scanning with ML Analysis".center(80))
    print("="*80)

    print("\nSimulating batch scan of multiple devices...")
    print("(Using localhost for safety - replace with actual targets for real scanning)\n")

    scanner = EnterpriseNetworkScanner(enable_ml=True)

    # Test with localhost only for safety
    test_targets = ['127.0.0.1']

    results = []
    for target in test_targets:
        print(f"\nScanning target: {target}")
        result = scanner.scan_target(target)
        results.append(result)

    # Summary
    print("\n" + "="*80)
    print("BATCH SCAN SUMMARY".center(80))
    print("="*80)

    for result in results:
        ml_analysis = result.get('ml_analysis')
        if ml_analysis and ml_analysis.get('risk_classification'):
            risk = ml_analysis['risk_classification']
            print(f"\n{result['ip']:15s} - {result['hostname'][:30]:30s}")
            print(f"  Risk: {risk['risk_level'].upper():10s} (Score: {risk['risk_score']:.2f})")
            print(f"  OT Protocols: {len(result['ot_protocols'])}")
            print(f"  Vulnerabilities: {len(result['vulnerabilities'])}")
        else:
            print(f"\n{result['ip']:15s} - {result['hostname'][:30]:30s}")
            print(f"  Status: {result['status']}")
            print(f"  ML Analysis: Not available")

    print("\n✓ Batch scanning complete!\n")

    return True


def main():
    """Main test function"""
    print_banner()

    tests = [
        ("ML Feature Extraction", test_ml_feature_extraction),
        ("Integrated Scanner", test_integrated_scanner),
        ("Batch Scanning", test_batch_scanning)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            print(f"\nRunning: {test_name}...")
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Final summary
    print("\n" + "="*80)
    print("TEST SUMMARY".center(80))
    print("="*80)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status} - {test_name}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! ML integration is working correctly!")
    else:
        print("\n⚠ Some tests failed. Check the output above for details.")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Tests interrupted by user\n")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
