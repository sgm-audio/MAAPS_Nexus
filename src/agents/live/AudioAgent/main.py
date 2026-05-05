import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import csv
import time
from core.hunter import Hunter
from core.dispatcher import Dispatcher
from config import Config


def main():
    print(f"==================================================")
    print(f"   AUDIO ARCHITECT v2.0 | THE SUBSTANTIATED AGENT")
    print(f"==================================================")

    if len(sys.argv) < 2:
        print("Usage: python main.py [hunt | audit | listen | fire]")
        return

    cmd = sys.argv[1]

    if cmd == "hunt":
        hunter = Hunter(headless=False)
        leads = hunter.hunt()
        save_leads(leads)

    elif cmd == "test":
        print("🧪 Testing Bloodhound on known target...")
        hunter = Hunter(headless=True)
        leads = hunter.hunt(["Nashville"])
        save_leads(leads)

    elif cmd == "fire":
        # Load leads
        filename = "AudioAgent/data/leads_v2.csv"
        try:
            with open(filename, "r", encoding="utf-8") as f:
                leads = list(csv.DictReader(f))
        except FileNotFoundError:
            print(f"❌ No leads found at {filename}. Run 'hunt' first.")
            return

        dispatcher = Dispatcher()
        dry = "--live" not in sys.argv
        dispatcher.fire(leads, dry_run=dry)

    elif cmd == "audit":
        # V3: The Auditor
        from core.auditor import Auditor

        filename = "AudioAgent/data/leads_v2.csv"
        try:
            with open(filename, "r", encoding="utf-8") as f:
                leads = list(csv.DictReader(f))
        except FileNotFoundError:
            print(f"❌ No leads found at {filename}. Run 'hunt' first.")
            return

        auditor = Auditor()
        print("🕵️  STARTING INFRASTRUCTURE AUDIT...")

        for lead in leads:
            company = lead.get("Company")
            website = lead.get("Website")

            if not website:
                print(f"   ⏩ Skipping {company} (No Website)")
                continue

            print(f"   🔍 Auditing: {company}")
            metrics = auditor.scan_site(website)

            safe_name = company.replace(" ", "_")
            output = f"AudioAgent/data/reports/{safe_name}_Audit.pdf"
            auditor.generate_report(company, metrics, output)

        print("\n✅ AUDIT COMPLETE. Reports generated in data/reports/")

    elif cmd == "listen":
        # V4: The Acoustic Analyst
        from core.listener import Listener

        filename = "AudioAgent/data/leads_v2.csv"
        try:
            with open(filename, "r", encoding="utf-8") as f:
                leads = list(csv.DictReader(f))
        except FileNotFoundError:
            print(f"❌ No leads found at {filename}.")
            return

        listener = Listener()
        updated_leads = []
        count = 0

        print("🦻 ACTIVATING BIO-DIGITAL LISTENER...")

        for lead in leads:
            company = lead.get("Company")
            website = lead.get("Website")

            # Default to keep old hook if we fail
            updated_leads.append(lead)

            if not website:
                continue

            audio_url = listener.scan_for_audio(website)
            if audio_url:
                print(f"   🎯 Audio Detected: {audio_url}")
                path = listener.download_asset(audio_url)
                if path:
                    metrics = listener.analyze_asset(path)
                    if metrics:
                        # SUPERIORITY HOOK
                        fname = audio_url.split("/")[-1]
                        if len(fname) > 20:
                            fname = "your audio asset"

                        hook = listener.generate_hook(fname, metrics)
                        lead["Hook"] = hook
                        print(f"      ✅ NEW HOOK: {hook}")
                        count += 1

            # Save progressively? No, batch save better for CSV safety

        # Resave
        save_leads(updated_leads)
        print(f"\n🎧 FORENSIC ANALYSIS COMPLETE. Updated {count} hooks.")


def save_leads(leads):
    path = Config.TARGET_CITIES
    filename = "AudioAgent/data/leads_v2.csv"

    keys = leads[0].keys() if leads else ["Company", "Email"]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(leads)

    print(f"\n💾 SAVED {len(leads)} LEADS TO {filename}")


if __name__ == "__main__":
    main()
