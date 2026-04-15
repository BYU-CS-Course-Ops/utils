"""
Send a test Discord notification from a JSON payload file.

Usage:
    source ~/.env
    python send_test_notification.py --type canvas --payload path/to/payload.json
    python send_test_notification.py --type docker --payload path/to/payload.json
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from notifications.send_course import main as send_course


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a test Discord notification.")
    parser.add_argument("--type", required=True, choices=["canvas", "docker"])
    parser.add_argument("--payload", required=True, help="Path to payload JSON file")
    args = parser.parse_args()

    if not os.path.isfile(args.payload):
        print(f"Error: payload file not found at {args.payload}", file=sys.stderr)
        sys.exit(1)

    send_course(
        ntype=args.type,
        payload=args.payload,
        course_id="000",
        course_name="Test Course",
        course_url="https://example.com",
        author="test-user",
        author_icon="https://github.com/ghost.png",
        branch_name="test-branch",
        action_url="https://github.com/actions/runs/0",
        cicd_role_id=1373077186072019024,
    )
