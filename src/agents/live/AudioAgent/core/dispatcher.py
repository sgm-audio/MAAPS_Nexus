import smtplib
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config


class Dispatcher:
    def __init__(self):
        self.user = Config.SMTP_USER
        self.password = Config.SMTP_PASSWORD
        self.server_host = Config.SMTP_SERVER
        self.server_port = Config.SMTP_PORT

    def fire(self, leads, dry_run=True):
        print(f"\n🚀 DISPATCHER ACTIVATED")
        print(f"🛡️ DRY RUN: {dry_run}")

        server = None
        if not dry_run:
            try:
                server = smtplib.SMTP(self.server_host, self.server_port)
                server.starttls()
                server.login(self.user, self.password)
                print(f"✅ Authenticated as {self.user}")
            except Exception as e:
                print(f"🛑 Auth Failed: {e}")
                return

        for i, lead in enumerate(leads):
            email = lead.get("Email")
            company = lead.get("Company")
            hook = lead.get("Hook", "professional audio workflow")

            if not email or "@" not in email:
                print(f"[{i}] {company}: SKIPPED (No Email)")
                continue

            # Template Logic (Re-implemented for V2)
            subject = f"Question regarding {company} workflow"
            body = f"""
Hi there,

I am an AI Audio Architect (ex-Berklee) building a proprietary processing engine specifically for studios like {company}.

I noticed you are running {hook}.

I’m bypassing the usual "wrapper" tools to build raw Python infrastructure that handles heavy DSP and metadata at scale.

Before I finalize the architecture, I’m asking a few studio owners:
What is the one bottleneck in your current QC or ingestion workflow that you would pay to have "hard-coded" out of existence?

Best,
Scott Mills
            """

            print(f"[{i}] {company} -> {email}")
            print(f"    Subject: {subject}")

            if not dry_run:
                msg = MIMEMultipart()
                msg["From"] = self.user
                msg["To"] = email
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))

                # V3: ATTACH AUDIT REPORT (If Exists)
                report_name = f"{company.replace(' ', '_')}_Audit.pdf"
                report_path = f"AudioAgent/data/reports/{report_name}"

                try:
                    from email.mime.application import MIMEApplication
                    import os

                    if os.path.exists(report_path):
                        with open(report_path, "rb") as f:
                            part = MIMEApplication(f.read(), Name=report_name)
                            part["Content-Disposition"] = (
                                f'attachment; filename="{report_name}"'
                            )
                            msg.attach(part)
                            print(f"    📎 Attached: {report_name}")
                except Exception as e:
                    print(f"    ⚠️ Attachment Failed: {e}")

                try:
                    server.send_message(msg)
                    print("    ✅ SENT")
                    time.sleep(random.uniform(4, 12))
                except Exception as e:
                    print(f"    ❌ FAILED: {e}")

        if server:
            server.quit()
