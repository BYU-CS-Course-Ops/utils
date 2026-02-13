import os
from argparse import ArgumentParser

from .formatting.pypi_format import format_notification
from .send_notification import send_notification


def main(ntype, author, author_icon, action_url, success=None, version=None, cicd_role_id=None):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise EnvironmentError("DISCORD_WEBHOOK_URL environment variable is not set.")

    notification = format_notification(
        ntype=ntype,
        author=author,
        author_icon=author_icon,
        action_url=action_url,
        success=success,
        version=version,
    )

    if not success and cicd_role_id:
        notification.content = f"<@&{cicd_role_id}>"

    send_notification(webhook_url, notification)


if __name__ == "__main__":
    parser = ArgumentParser(description="Send PyPI update notifications to Discord.")
    parser.add_argument("--type", required=True, choices=["mdxcanvas", "markdowndata", "byu_pytest_utils"],
                        help="Type of notification")
    parser.add_argument("--author", required=True, help="Name of the author")
    parser.add_argument("--author-icon", required=True, help="URL of the author's icon")
    parser.add_argument("--action-url", required=True, help="URL to the GHA")
    parser.add_argument("--success", nargs='?', const=None, default=None, help="Bool indicating success or failure")
    parser.add_argument("--version", nargs='?', const=None, default=None, help="PyPi version")
    parser.add_argument("--cicd-id", nargs='?', const=None, default=None, help="CI/CD Role ID")

    args = parser.parse_args()

    main(args.type, args.author, args.author_icon, args.action_url, args.success, args.version, args.cicd_id)
