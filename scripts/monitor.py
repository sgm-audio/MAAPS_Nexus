#!/usr/bin/env python3
"""
MAAPS Production Monitoring Script
Continuously monitors system health and alerts on issues

Usage: python scripts/monitor.py
Add to systemd or run in background: nohup python scripts/monitor.py &
"""

import time
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.system import create_system


class MAAPSMonitor:
    def __init__(self, check_interval=60, alert_threshold=70):
        self.check_interval = check_interval
        self.alert_threshold = alert_threshold
        self.alert_count = 0
        self.last_alert_time = None

    def log(self, level, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        sys.stdout.flush()

    def check_health(self, system):
        """Check system health and return status"""
        try:
            health = system.get_health()
            metrics = system.get_resource_metrics()

            status = {
                'health_score': health.get('health_score', 0),
                'agents_healthy': health.get('agents_healthy', 0),
                'agents_total': health.get('agents_total', 0),
                'cpu': metrics['metrics'].get('cpu_usage_percent', 0),
                'memory': metrics['metrics'].get('memory_usage_percent', 0),
                'uptime': health.get('system_uptime_seconds', 0)
            }

            return status

        except Exception as e:
            self.log('ERROR', f"Health check failed: {e}")
            return None

    def should_alert(self, status):
        """Determine if alert should be sent"""
        if status is None:
            return True, "System health check failed"

        if status['health_score'] < self.alert_threshold:
            return True, f"Health score below threshold: {status['health_score']}%"

        if status['cpu'] > 90:
            return True, f"CPU usage critical: {status['cpu']:.1f}%"

        if status['memory'] > 90:
            return True, f"Memory usage critical: {status['memory']:.1f}%"

        if status['agents_healthy'] < status['agents_total']:
            unhealthy = status['agents_total'] - status['agents_healthy']
            return True, f"{unhealthy} agent(s) unhealthy"

        return False, None

    def send_alert(self, message):
        """Send alert notification"""
        self.log('ALERT', message)
        self.alert_count += 1
        self.last_alert_time = time.time()

        # TODO: Add email/SMS/Slack notification here
        # Example:
        # import smtplib
        # send_email(subject="MAAPS Alert", body=message)

    def run(self):
        """Main monitoring loop"""
        self.log('INFO', "Starting MAAPS monitoring...")
        self.log('INFO', f"Check interval: {self.check_interval}s")
        self.log('INFO', f"Alert threshold: {self.alert_threshold}%")

        system = create_system()
        system.start()

        try:
            while True:
                # Check system health
                status = self.check_health(system)

                if status:
                    # Log status
                    self.log('INFO',
                        f"Health: {status['health_score']:.1f}% | "
                        f"Agents: {status['agents_healthy']}/{status['agents_total']} | "
                        f"CPU: {status['cpu']:.1f}% | "
                        f"Memory: {status['memory']:.1f}% | "
                        f"Uptime: {status['uptime']:.0f}s"
                    )

                    # Check if alert needed
                    should_alert, alert_msg = self.should_alert(status)
                    if should_alert:
                        self.send_alert(alert_msg)

                # Sleep until next check
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.log('INFO', "Monitoring stopped by user")
        except Exception as e:
            self.log('ERROR', f"Monitoring error: {e}")
        finally:
            system.stop()
            self.log('INFO', f"Total alerts sent: {self.alert_count}")


if __name__ == "__main__":
    # Configuration
    CHECK_INTERVAL = int(os.getenv('MONITOR_INTERVAL', '60'))
    ALERT_THRESHOLD = int(os.getenv('ALERT_THRESHOLD', '70'))

    # Start monitoring
    monitor = MAAPSMonitor(
        check_interval=CHECK_INTERVAL,
        alert_threshold=ALERT_THRESHOLD
    )
    monitor.run()
