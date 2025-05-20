from argparse import ArgumentParser
import json
import os
import requests
from typing import TypedDict


class Field(TypedDict):
    name: str
    value: str
    inline: bool


def space(inline=False) -> Field:
    return Field(name="", value="\u200b", inline=inline)


def generate_field(name: str, value: str, inline: bool = False) -> list[Field]:
    if len(value) > 1024:
        chunks = [value[i:i + 1024] for i in range(0, len(value), 1024)]
        return [
            Field(
                name=name if i == 0 else f"{name} (continued)",
                value=chunk,
                inline=inline
            ) for i, chunk in enumerate(chunks)
        ]
    else:
        return [Field(name=name, value=value, inline=inline)]


def send_discord_message(webhook_url: str, message: dict):
    response = requests.post(webhook_url, json=message)
    response.raise_for_status()
    print("✅ Sent message successfully.")


def main(ntype, payload, course_id, author, author_icon, branch_name, action_url, cicd_id):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise EnvironmentError("DISCORD_WEBHOOK_URL environment variable is not set.")

    # Import formatter and checker
    if ntype == "canvas":
        from canvas_notification import canvas_format, check_canvas_payload
        format_notification = canvas_format
        has_info = check_canvas_payload
    elif ntype == "docker":
        from docker_notification import docker_format, check_docker_payload
        format_notification = docker_format
        has_info = check_docker_payload
    else:
        raise ValueError("Invalid notification type. Use 'canvas' or 'docker'.")

    with open(payload, 'r') as file:
        data = json.load(file)

    if not data or not has_info(data):
        print("No information to send.")
        return

    notification = format_notification(
        data=data,
        course_id=course_id,
        author=author,
        author_icon=author_icon,
        branch=branch_name,
        cicd_id=cicd_id,
        action_url=action_url,
    )

    print(json.dumps(notification, indent=4))

    send_discord_message(webhook_url, notification)

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
