import os
import html
from datetime import datetime

class CortexReporter:
    def __init__(self, report_dir="reports"):
        self.report_dir = report_dir
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)

    def generate_report(self, url, task, status, error=None, screenshot=None, repair_details=None):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_path = os.path.join(self.report_dir, f"report_{timestamp}.html")
        
        status_color = "#28a745" if status == "PASSED" else "#dc3545"

        # Self-Healing execution log (shown only when a repair happened)
        repair_html = ""
        if repair_details:
            diagnosis = html.escape(repair_details.get("diagnosis", "N/A"))
            notes = html.escape(repair_details.get("notes", "N/A"))
            repair_html = f"""
            <div class="card p-3 mb-4 border-primary">
                <h3 class="text-primary">🛠️ Self-Healing Execution Log</h3>
                <p class="mb-2"><strong>🧠 AI Diagnosis (what was found):</strong></p>
                <pre>{diagnosis}</pre>
                <p class="mb-2 mt-3"><strong>🔧 Action taken (how it was fixed):</strong></p>
                <pre>{notes}</pre>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Cortex-SDET Test Report</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{ background-color: #f8f9fa; padding: 40px; }}
                .report-card {{ background: white; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); padding: 30px; }}
                .status-badge {{ padding: 10px 20px; border-radius: 50px; color: white; font-weight: bold; background-color: {status_color}; }}
                .screenshot-img {{ max-width: 100%; border: 2px solid #ddd; border-radius: 10px; margin-top: 20px; }}
                pre {{ background: #eee; padding: 15px; border-radius: 5px; white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="report-card">
                    <h1 class="mb-4">🧠 Cortex-SDET Test Report</h1>
                    <div class="row mb-4">
                        <div class="col-md-8">
                            <p><strong>URL:</strong> <a href="{url}" target="_blank">{url}</a></p>
                            <p><strong>Task:</strong> {task}</p>
                            <p><strong>Time:</strong> {timestamp}</p>
                        </div>
                        <div class="col-md-4 text-end">
                            <span class="status-badge">{status}</span>
                        </div>
                    </div>
                    
                    {repair_html}
                    
                    {f'<h3>❌ Error:</h3><pre>{html.escape(error) if error else ""}</pre>' if error else ''}
                    
                    {f'<h3>📸 Screenshot:</h3><img src="../{screenshot}" class="screenshot-img">' if screenshot and os.path.exists(screenshot) else ''}
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"\n[📊] REPORT GENERATED: {report_path}")
        return report_path