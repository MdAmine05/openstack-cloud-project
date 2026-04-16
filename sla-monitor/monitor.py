#!/usr/bin/env python3
"""
OpenStack SLA Monitoring Script
Monitors instance availability every 5 minutes
Checks against 99.5% daily availability target
"""

import json
import os
import datetime
import subprocess
import sys

# OpenStack credentials
OS_AUTH_URL = "http://YOUR_HOST_IP/identity"
OS_USERNAME = "admin"
OS_PASSWORD =  os.environ.get("OS_PASSWORD", "YOUR_PASSWORD_HERE")
OS_PROJECT_NAME = "demo"
OS_USER_DOMAIN_NAME = "Default"
OS_PROJECT_DOMAIN_NAME = "Default"

SLA_FILE = "/home/light01/sla-monitor/sla.json"
LOG_FILE = "/home/light01/sla-monitor/monitor.log"

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def get_instances():
    """Get all instances and their status using OpenStack CLI"""
    env = os.environ.copy()
    env.update({
        "OS_AUTH_URL": OS_AUTH_URL,
        "OS_USERNAME": OS_USERNAME,
        "OS_PASSWORD": OS_PASSWORD,
        "OS_PROJECT_NAME": OS_PROJECT_NAME,
        "OS_USER_DOMAIN_NAME": OS_USER_DOMAIN_NAME,
        "OS_PROJECT_DOMAIN_NAME": OS_PROJECT_DOMAIN_NAME,
        "OS_IDENTITY_API_VERSION": "3"
    })

    result = subprocess.run(
        ["openstack", "server", "list", "--all-projects", "-f", "json"],
        capture_output=True, text=True, env=env
    )

    if result.returncode != 0:
        log(f"ERROR getting instances: {result.stderr}")
        return []

    try:
        return json.loads(result.stdout)
    except:
        log("ERROR parsing instance list")
        return []

def load_sla():
    with open(SLA_FILE, "r") as f:
        return json.load(f)

def save_sla(data):
    with open(SLA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def monitor():
    log("="*50)
    log("Starting SLA monitoring check")

    instances = get_instances()

    if not instances:
        log("No instances found or connection failed")
        return

    total = len(instances)
    active = sum(1 for i in instances if i.get("Status", "").upper() == "ACTIVE")
    error = sum(1 for i in instances if i.get("Status", "").upper() == "ERROR")
    stopped = total - active - error

    availability = (active / total * 100) if total > 0 else 0
    target = 99.5
    sla_met = availability >= target

    log(f"Total instances: {total}")
    log(f"Active: {active} | Stopped: {stopped} | Error: {error}")
    log(f"Availability: {availability:.2f}%")
    log(f"Target: {target}% | SLA Met: {'YES ✅' if sla_met else 'NO ❌'}")

    # Build report entry
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "total_instances": total,
        "active_instances": active,
        "stopped_instances": stopped,
        "error_instances": error,
        "availability_percentage": round(availability, 2),
        "target_percentage": target,
        "sla_met": sla_met,
        "instances": [
            {
                "id": i.get("ID", ""),
                "name": i.get("Name", ""),
                "status": i.get("Status", "")
            } for i in instances
        ]
    }

    # Update SLA file
    sla = load_sla()
    sla["sla"]["reports"].append(report)
    sla["sla"]["last_check"] = datetime.datetime.now().isoformat()
    sla["sla"]["last_availability"] = round(availability, 2)
    sla["sla"]["last_sla_met"] = sla_met

    # Update instances monitored list
    sla["sla"]["instances_monitored"] = [
        {"id": i.get("ID",""), "name": i.get("Name",""), "status": i.get("Status","")}
        for i in instances
    ]

    save_sla(sla)
    log(f"SLA file updated: {SLA_FILE}")
    log("="*50)

if __name__ == "__main__":
    monitor()
