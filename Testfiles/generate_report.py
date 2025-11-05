import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scanner.network_scanner import EnterpriseNetworkScanner
from datetime import datetime
import json

# Scan targets
targets = [
    "192.168.12.228",  # PLC
    "192.168.12.161",  # VPN device
    "192.168.12.162",  # Network device
    "192.168.12.174",  # Cisco router
    "192.168.12.190",  # Research server
]

scanner = EnterpriseNetworkScanner()
results = []

print("[*] Scanning all devices for report generation...")

for ip in targets:
    print(f"  Scanning {ip}...")
    result = scanner.scan_target(ip)
    results.append(result)

# Generate HTML Report
html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>OT/ICS Security Assessment Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 40px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 4px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .device {{
            border: 1px solid #bdc3c7;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .critical {{
            background: #e74c3c;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-weight: bold;
        }}
        .high {{
            background: #e67e22;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-weight: bold;
        }}
        .medium {{
            background: #f39c12;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-weight: bold;
        }}
        .online {{
            color: #27ae60;
            font-weight: bold;
        }}
        .offline {{
            color: #95a5a6;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background: #3498db;
            color: white;
        }}
        .ot-protocol {{
            background: #9b59b6;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            display: inline-block;
            margin: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏭 OT/ICS Security Assessment Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Network:</strong> 192.168.12.0/24</p>
        <p><strong>Scanner:</strong> Enterprise OT Network Scanner v1.0</p>
        
        <div class="summary">
            <h2>📊 Executive Summary</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Devices Scanned</td>
                    <td>{len(results)}</td>
                </tr>
                <tr>
                    <td>Online Devices</td>
                    <td>{sum(1 for r in results if r['status'] == 'online')}</td>
                </tr>
                <tr>
                    <td>OT/ICS Devices Found</td>
                    <td>{sum(1 for r in results if r['ot_protocols'])}</td>
                </tr>
                <tr>
                    <td>Critical Vulnerabilities</td>
                    <td style="color: red; font-weight: bold;">
                        {sum(len([v for v in r['vulnerabilities'] if v['severity'] == 'critical']) for r in results)}
                    </td>
                </tr>
                <tr>
                    <td>High Vulnerabilities</td>
                    <td style="color: orange; font-weight: bold;">
                        {sum(len([v for v in r['vulnerabilities'] if v['severity'] == 'high']) for r in results)}
                    </td>
                </tr>
            </table>
        </div>
        
        <h2>🔍 Detailed Findings</h2>
"""

for result in results:
    status_class = 'online' if result['status'] == 'online' else 'offline'
    
    html += f"""
        <div class="device">
            <h3>🖥️ {result['hostname']}</h3>
            <p><strong>IP:</strong> {result['ip']}</p>
            <p><strong>Status:</strong> <span class="{status_class}">{result['status'].upper()}</span></p>
            <p><strong>MAC:</strong> {result['mac_address']}</p>
            <p><strong>Vendor:</strong> {result['vendor']}</p>
    """
    
    if result['ot_protocols']:
        html += "<p><strong>OT/ICS Protocols:</strong><br>"
        for proto in result['ot_protocols']:
            html += f'<span class="ot-protocol">🏭 {proto["protocol"]} (Port {proto["port"]})</span>'
        html += "</p>"
    
    if result['open_ports']:
        html += "<p><strong>Open Ports:</strong></p><table>"
        html += "<tr><th>Port</th><th>Service</th><th>Protocol</th></tr>"
        for port in result['open_ports']:
            html += f"<tr><td>{port['port']}</td><td>{port['service']}</td><td>{port['protocol']}</td></tr>"
        html += "</table>"
    
    if result['vulnerabilities']:
        html += "<p><strong>⚠️ Vulnerabilities:</strong></p><ul>"
        for vuln in result['vulnerabilities']:
            severity_class = vuln['severity']
            html += f'''<li>
                <span class="{severity_class}">{vuln['severity'].upper()}</span> 
                {vuln['description']}<br>
                <em>Recommendation: {vuln['recommendation']}</em>
            </li>'''
        html += "</ul>"
    
    html += "</div>"

html += """
        <h2>🛡️ Recommendations</h2>
        <ol>
            <li><strong>Immediate:</strong> Implement firewall rules to restrict access to EtherNet/IP (port 44818)</li>
            <li><strong>Immediate:</strong> Disable Telnet on Siemens device, use SSH only</li>
            <li><strong>High Priority:</strong> Apply MS17-010 patch to Windows server</li>
            <li><strong>High Priority:</strong> Implement network segmentation (IT vs OT networks)</li>
            <li><strong>Medium Priority:</strong> Enable authentication on all OT protocols</li>
        </ol>
    </div>
</body>
</html>
"""

# Save report
report_path = Path("../reports") / f"OT_Security_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
report_path.parent.mkdir(exist_ok=True)
report_path.write_text(html, encoding='utf-8')

print(f"\n[OK] Report generated: {report_path}")
print(f"[*] Open in browser: {report_path.absolute()}")

# Also save JSON
json_path = report_path.with_suffix('.json')
json_path.write_text(json.dumps(results, indent=2), encoding='utf-8')
print(f"[OK] JSON data saved: {json_path}")

