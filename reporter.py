import os
from datetime import datetime

class CortexReporter:
    def __init__(self, report_dir="reports"):
        self.report_dir = report_dir
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)

    def generate_report(self, url, task, status, error=None, screenshot=None):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_path = os.path.join(self.report_dir, f"report_{timestamp}.html")
        
        status_color = "#28a745" if status == "PASSED" else "#dc3545"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="uk">
        <head>
            <meta charset="UTF-8">
            <title>Cortex-SDET Test Report</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{ background-color: #f8f9fa; padding: 40px; }}
                .report-card {{ background: white; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); padding: 30px; }}
                .status-badge {{ padding: 10px 20px; border-radius: 50px; color: white; font-weight: bold; background-color: {status_color}; }}
                .screenshot-img {{ max-width: 100%; border: 2px solid #ddd; border-radius: 10px; margin-top: 20px; }}
                pre {{ background: #eee; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="report-card">
                    <h1 class="mb-4">🧠 Cortex-SDET Test Report</h1>
                    <div class="row mb-4">
                        <div class="col-md-8">
                            <p><strong>URL:</strong> <a href="{url}" target="_blank">{url}</a></p>
                            <p><strong>Завдання:</strong> {task}</p>
                            <p><strong>Час:</strong> {timestamp}</p>
                        </div>
                        <div class="col-md-4 text-end">
                            <span class="status-badge">{status}</span>
                        </div>
                    </div>
                    
                    {f'<h3>❌ Помилка:</h3><pre>{error}</pre>' if error else ''}
                    
                    {f'<h3>📸 Скриншот:</h3><img src="../{screenshot}" class="screenshot-img">' if screenshot and os.path.exists(screenshot) else ''}
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"\n[📊] ЗВІТ СГЕНЕРОВАНО: {report_path}")
        return report_path