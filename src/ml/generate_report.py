#!/usr/bin/env python3
"""
ML Performance Report Generator

Generates comprehensive HTML reports from model evaluation results.
Includes visualizations, metrics, and recommendations.

Usage:
    python generate_report.py --model data/models/unsw_nb15_model
    python generate_report.py --results evaluation_results.json --output report.html
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.models.hybrid_detector import HybridAnomalyDetector


class MLPerformanceReportGenerator:
    """Generate comprehensive HTML reports for ML performance"""

    def __init__(self):
        self.results = {}
        self.timestamp = datetime.now()

    def evaluate_model(self, model_path: str, test_data_path: str) -> Dict:
        """Evaluate model and get results"""
        print(f"Evaluating model: {model_path}")
        print(f"Test data: {test_data_path}")

        # Load test data
        df_test = pd.read_csv(test_data_path)

        # Prepare features
        exclude_cols = ['label', 'is_attack', 'attack_category', 'attack_cat',
                       'srcip', 'dstip', 'proto', 'service', 'state', 'Label']
        feature_cols = [col for col in df_test.columns if col not in exclude_cols]

        X_test = df_test[feature_cols].values
        y_test = df_test['is_attack'].values if 'is_attack' in df_test.columns else df_test['label'].values

        # Get attack categories
        if 'attack_category' in df_test.columns:
            attack_categories = df_test['attack_category'].values
        else:
            attack_categories = None

        # Load model
        detector = HybridAnomalyDetector()
        detector.load(model_path)

        # Predict
        results = detector.predict(X_test)
        y_pred = results['is_anomaly']

        # Calculate metrics
        tp = np.sum((y_test == 1) & (y_pred == 1))
        tn = np.sum((y_test == 0) & (y_pred == 0))
        fp = np.sum((y_test == 0) & (y_pred == 1))
        fn = np.sum((y_test == 1) & (y_pred == 0))

        accuracy = (tp + tn) / len(y_test)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

        # Per-category performance
        category_performance = {}
        if attack_categories is not None:
            category_names = {
                0: 'Normal', 1: 'Generic', 2: 'Exploits', 3: 'Fuzzers',
                4: 'DoS', 5: 'Reconnaissance', 6: 'Analysis',
                7: 'Backdoor', 8: 'Shellcode', 9: 'Worms'
            }

            for cat_id, cat_name in category_names.items():
                if cat_id == 0:  # Skip normal
                    continue

                mask = attack_categories == cat_id
                if np.sum(mask) > 0:
                    cat_detected = np.sum(y_pred[mask] == 1)
                    cat_total = np.sum(mask)
                    category_performance[cat_name] = {
                        'detected': int(cat_detected),
                        'total': int(cat_total),
                        'rate': cat_detected / cat_total if cat_total > 0 else 0
                    }

        self.results = {
            'timestamp': self.timestamp.isoformat(),
            'model_path': model_path,
            'test_data_path': test_data_path,
            'total_samples': len(y_test),
            'metrics': {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'fpr': fpr
            },
            'confusion_matrix': {
                'tp': int(tp),
                'tn': int(tn),
                'fp': int(fp),
                'fn': int(fn)
            },
            'category_performance': category_performance
        }

        return self.results

    def generate_html_report(self, output_path: str):
        """Generate HTML report"""
        html = self._generate_html()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n✓ Report generated: {output_path}")

    def _generate_html(self) -> str:
        """Generate HTML content"""
        metrics = self.results['metrics']
        cm = self.results['confusion_matrix']
        cat_perf = self.results['category_performance']

        # Generate category chart data
        cat_labels = []
        cat_values = []
        cat_colors = []

        for cat_name, perf in sorted(cat_perf.items(), key=lambda x: x[1]['rate'], reverse=True):
            cat_labels.append(cat_name)
            cat_values.append(perf['rate'] * 100)

            # Color code by performance
            rate = perf['rate']
            if rate >= 0.7:
                cat_colors.append('#27ae60')  # Green
            elif rate >= 0.5:
                cat_colors.append('#f39c12')  # Orange
            else:
                cat_colors.append('#e74c3c')  # Red

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ML IDS/IPS Performance Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-label {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        .good {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .bad {{ color: #e74c3c; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #34495e;
            color: white;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .confusion-matrix {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}
        .cm-cell {{
            padding: 30px;
            border-radius: 8px;
            text-align: center;
        }}
        .cm-tp {{ background: #d5f4e6; border: 2px solid #27ae60; }}
        .cm-tn {{ background: #d5f4e6; border: 2px solid #27ae60; }}
        .cm-fp {{ background: #fadbd8; border: 2px solid #e74c3c; }}
        .cm-fn {{ background: #fadbd8; border: 2px solid #e74c3c; }}
        .cm-value {{
            font-size: 32px;
            font-weight: bold;
        }}
        .cm-label {{
            font-size: 14px;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        .bar-chart {{
            margin: 20px 0;
        }}
        .bar {{
            margin: 10px 0;
        }}
        .bar-label {{
            display: inline-block;
            width: 150px;
            font-weight: 500;
        }}
        .bar-fill {{
            display: inline-block;
            height: 30px;
            background: #3498db;
            border-radius: 4px;
            text-align: right;
            padding: 5px 10px;
            color: white;
            font-weight: bold;
        }}
        .recommendation {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ ML-Based IDS/IPS Performance Report</h1>

        <p><strong>Generated:</strong> {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Model:</strong> {self.results['model_path']}</p>
        <p><strong>Test Samples:</strong> {self.results['total_samples']:,}</p>

        <h2>📊 Overall Performance Metrics</h2>

        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">ACCURACY</div>
                <div class="metric-value {'good' if metrics['accuracy'] >= 0.7 else 'warning' if metrics['accuracy'] >= 0.5 else 'bad'}">
                    {metrics['accuracy'] * 100:.1f}%
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-label">PRECISION</div>
                <div class="metric-value {'good' if metrics['precision'] >= 0.7 else 'warning' if metrics['precision'] >= 0.5 else 'bad'}">
                    {metrics['precision'] * 100:.1f}%
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-label">RECALL</div>
                <div class="metric-value {'good' if metrics['recall'] >= 0.7 else 'warning' if metrics['recall'] >= 0.5 else 'bad'}">
                    {metrics['recall'] * 100:.1f}%
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-label">F1-SCORE</div>
                <div class="metric-value {'good' if metrics['f1'] >= 0.7 else 'warning' if metrics['f1'] >= 0.5 else 'bad'}">
                    {metrics['f1'] * 100:.1f}%
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-label">FALSE POSITIVE RATE</div>
                <div class="metric-value {'good' if metrics['fpr'] <= 0.1 else 'warning' if metrics['fpr'] <= 0.3 else 'bad'}">
                    {metrics['fpr'] * 100:.1f}%
                </div>
            </div>
        </div>

        <h2>🎯 Confusion Matrix</h2>

        <div class="confusion-matrix">
            <div class="cm-cell cm-tp">
                <div class="cm-value">{cm['tp']:,}</div>
                <div class="cm-label">True Positives<br>(Attacks Detected)</div>
            </div>
            <div class="cm-cell cm-fp">
                <div class="cm-value">{cm['fp']:,}</div>
                <div class="cm-label">False Positives<br>(Normal Flagged as Attack)</div>
            </div>
            <div class="cm-cell cm-fn">
                <div class="cm-value">{cm['fn']:,}</div>
                <div class="cm-label">False Negatives<br>(Attacks Missed)</div>
            </div>
            <div class="cm-cell cm-tn">
                <div class="cm-value">{cm['tn']:,}</div>
                <div class="cm-label">True Negatives<br>(Normal Correctly ID'd)</div>
            </div>
        </div>

        <h2>🔍 Detection Rate by Attack Category</h2>

        <div class="bar-chart">
            {''.join([f'''
            <div class="bar">
                <span class="bar-label">{label}</span>
                <span class="bar-fill" style="width: {value}%; background: {color};">
                    {value:.1f}%
                </span>
            </div>
            ''' for label, value, color in zip(cat_labels, cat_values, cat_colors)])}
        </div>

        <h2>📋 Detailed Category Performance</h2>

        <table>
            <thead>
                <tr>
                    <th>Attack Category</th>
                    <th>Detected</th>
                    <th>Total</th>
                    <th>Detection Rate</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f'''
                <tr>
                    <td>{cat_name}</td>
                    <td>{perf['detected']:,}</td>
                    <td>{perf['total']:,}</td>
                    <td>{perf['rate'] * 100:.1f}%</td>
                    <td class="{'good' if perf['rate'] >= 0.7 else 'warning' if perf['rate'] >= 0.5 else 'bad'}">
                        {'✓ Excellent' if perf['rate'] >= 0.7 else '⚠ Moderate' if perf['rate'] >= 0.5 else '✗ Poor'}
                    </td>
                </tr>
                ''' for cat_name, perf in sorted(cat_perf.items(), key=lambda x: x[1]['rate'], reverse=True)])}
            </tbody>
        </table>

        <h2>💡 Recommendations</h2>

        {self._generate_recommendations()}

        <div class="footer">
            <p>OT/ICS Network Security & Asset Management System</p>
            <p>ML-Based Intrusion Detection & Prevention</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _generate_recommendations(self) -> str:
        """Generate recommendations based on results"""
        recommendations = []

        metrics = self.results['metrics']
        cat_perf = self.results['category_performance']

        # FPR recommendations
        if metrics['fpr'] > 0.5:
            recommendations.append(
                '<div class="recommendation">'
                '<strong>⚠ High False Positive Rate ({}%)</strong><br>'
                'Consider: Adjusting contamination parameter to 0.3-0.4, '
                'establishing better baseline with more normal traffic samples, '
                'or retraining with balanced dataset.'
                '</div>'.format(int(metrics['fpr'] * 100))
            )

        # Accuracy recommendations
        if metrics['accuracy'] < 0.6:
            recommendations.append(
                '<div class="recommendation">'
                '<strong>⚠ Low Overall Accuracy ({}%)</strong><br>'
                'Consider: Increasing training epochs to 50+, '
                'adding more diverse training data, '
                'or using automated hyperparameter tuning.'
                '</div>'.format(int(metrics['accuracy'] * 100))
            )

        # Category-specific recommendations
        poor_categories = [name for name, perf in cat_perf.items() if perf['rate'] < 0.5]

        if poor_categories:
            recommendations.append(
                '<div class="recommendation">'
                '<strong>⚠ Poor Detection for: {}</strong><br>'
                'Consider: Enhanced feature engineering for these categories, '
                'training separate specialized models, '
                'or collecting more training samples for underrepresented attacks.'
                '</div>'.format(', '.join(poor_categories))
            )

        # Positive feedback
        if metrics['accuracy'] >= 0.7 and metrics['fpr'] <= 0.3:
            recommendations.append(
                '<div class="recommendation" style="background: #d4edda; border-color: #28a745;">'
                '<strong>✓ Good Overall Performance!</strong><br>'
                'The model is performing well. Consider deploying to production with '
                'continuous monitoring and periodic retraining.'
                '</div>'
            )

        return '\n'.join(recommendations) if recommendations else '<p>No specific recommendations at this time.</p>'

    def save_json(self, output_path: str):
        """Save results as JSON"""
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"✓ JSON results saved: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate ML performance report'
    )

    parser.add_argument(
        '--model',
        default='data/models/unsw_nb15_model',
        help='Path to trained model'
    )

    parser.add_argument(
        '--test-data',
        default='data/datasets/unsw-nb15_test.csv',
        help='Path to test dataset'
    )

    parser.add_argument(
        '--output',
        default='ml_performance_report.html',
        help='Output HTML file'
    )

    parser.add_argument(
        '--json',
        help='Also save results as JSON'
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  ML PERFORMANCE REPORT GENERATOR")
    print("=" * 70)
    print()

    # Generate report
    generator = MLPerformanceReportGenerator()
    generator.evaluate_model(args.model, args.test_data)
    generator.generate_html_report(args.output)

    if args.json:
        generator.save_json(args.json)

    print(f"\n✓ Report generation complete!")
    print(f"\n📄 Open in browser: {Path(args.output).absolute()}")
    print()


if __name__ == "__main__":
    main()
