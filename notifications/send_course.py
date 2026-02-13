import json
import os
from argparse import ArgumentParser

from .formatting import canvas_format, docker_format
from .send_notification import send_notification


FORMATTERS = {
    "canvas": (canvas_format.format_notification, canvas_format.has_content, canvas_format.requires_review),
    "docker": (docker_format.format_notification, docker_format.has_content, docker_format.requires_review),
}


def main(ntype, payload, course_id, author, author_icon, branch_name, action_url, cicd_role_id):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise EnvironmentError("DISCORD_WEBHOOK_URL environment variable is not set.")

    if ntype not in FORMATTERS:
        raise ValueError("Invalid notification type. Use 'canvas' or 'docker'.")

    format_notification, has_content, requires_review = FORMATTERS[ntype]

    with open(payload, 'r') as file:
        data = json.load(file)

    if not data or not has_content(data):
        print("No information to send.")
        return

    notification = format_notification(
        data=data,
        course_id=course_id,
        author=author,
        author_icon=author_icon,
        branch=branch_name,
        action_url=action_url,
    )

    if requires_review(data) and cicd_role_id:
        notification.content = f"<@&{cicd_role_id}>"

    send_notification(webhook_url, notification)


if __name__ == "__main__":
    parser = ArgumentParser(description="Send Canvas or Docker notifications to Discord.")
    parser.add_argument("--type", required=True, choices=["canvas", "docker"], help="Type of notification")
    parser.add_argument("--payload", required=True, help="Path to the payload JSON file")
    parser.add_argument("--course-id", required=True, help="Course ID")
    parser.add_argument("--author", required=True, help="Name of the author")
    parser.add_argument("--author-icon", required=True, help="URL of the author's icon")
    parser.add_argument("--branch", required=True, help="Branch name")
    parser.add_argument("--action-url", required=True, help="URL to the GHA")
    parser.add_argument("--cicd-id", nargs='?', const=None, default=None, help="CI/CD Role ID")

    args = parser.parse_args()

    main(args.type, args.payload, args.course_id, args.author, args.author_icon, args.branch, args.action_url, args.cicd_id)
