"""
Sends a test notification through AWS SNS to confirm the topic and credentials work.

Usage (from the backend folder, venv active):
    python scripts/test_sns.py                          # send a test alert
    python scripts/test_sns.py --subscribe you@mail.com # subscribe an email (one time)
"""

import argparse
import sys
from pathlib import Path

# Allow `from app...` imports when run as a script from any folder.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.services import sns_service  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--subscribe", metavar="EMAIL", help="Subscribe this email to the topic.")
    args = parser.parse_args()

    if not settings.AWS_SNS_TOPIC_ARN:
        print("AWS_SNS_TOPIC_ARN is empty in backend\\.env. Add the topic ARN and try again.")
        sys.exit(1)

    import boto3
    client = sns_service._client()

    if args.subscribe:
        client.subscribe(TopicArn=settings.AWS_SNS_TOPIC_ARN, Protocol="email", Endpoint=args.subscribe)
        print(f"Subscription requested for {args.subscribe}. Confirm it from the email AWS sends.")
        return

    subject, body = sns_service.format_alert_message({
        "priority": "critical",
        "rule": "Test alert from AegisCloud",
        "container_name": "test-container",
        "command": "n/a",
        "output": "If you can read this, AWS SNS is working.",
    })
    response = client.publish(TopicArn=settings.AWS_SNS_TOPIC_ARN, Subject=subject, Message=body)
    print(f"Sent. MessageId: {response['MessageId']}")
    print("Check your inbox (and spam folder).")


if __name__ == "__main__":
    main()