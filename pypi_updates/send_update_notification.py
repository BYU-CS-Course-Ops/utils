import os
from typing import TypedDict
from datetime import datetime
from argparse import ArgumentParser
from discord_webhook import DiscordWebhook, DiscordEmbed

BEAN_LAB_LOGO = None


class Field(TypedDict):
    name: str
    value: str
    inline: bool


def space(inline=False) -> Field:
    return Field(name="", value="\u200b", inline=inline)


def main(ntype, author, author_icon, action_url, success=None, version=None, cicd_id=None):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise EnvironmentError("DISCORD_WEBHOOK_URL environment variable is not set.")

    type_vars = {
        "mdxcanvas": {
            "username": "MDXCanvas Notifications",
            "title": "MDXCanvas Update",
            "success_description": lambda x: f"Updated to version **`{x}`**",
            "failure_description": "An **error occurred** while updating MDXCanvas.",
            "color": 16081462,
            "footer_text": "MDXCanvas GitHub Action",
            "footer_icon_url": "https://tinyurl.com/4ky2afzx"
        },
        "markdowndata": {
            "username": "MarkdownData Notifications",
            "title": "MarkdownData Update",
            "success_description": lambda x: f"Updated to version **`{x}`**",
            "failure_description": "An **error occurred** while updating MarkdownData.",
            "color": 1301590,
            "footer_text": "MarkdownData GitHub Action",
            "footer_icon_url": "https://tinyurl.com/4ky2afzx"
        },
        "byu_pytest_utils": {
            "username": "BYU Pytest Utils Notifications",
            "title": "BYU Pytest Utils Update",
            "success_description": lambda x: f"Updated to version **`{x}`**",
            "failure_description": "An **error occurred** while updating BYU Pytest Utils.",
            "color": 3447003,
            "footer_text": "BYU Pytest Utils GitHub Action",
            "footer_icon_url": "https://tinyurl.com/4dyna5du"
        }
    }

    if success:
        description = type_vars[ntype]["success_description"](version)
    else:
        description = type_vars[ntype]["failure_description"]

    webhook = DiscordWebhook(
        url=webhook_url,
        username=type_vars[ntype]["username"],
        avatar_url=BEAN_LAB_LOGO,
        content=f"<@&{cicd_id}>" if not success and cicd_id else None,
    )

    embed = DiscordEmbed(
        title=type_vars[ntype]["title"],
        description=description,
        color=type_vars[ntype]["color"],
        timestamp=datetime.now().isoformat()
    )

    embed.set_author(
        name=author,
        icon_url=author_icon,
    )

    embed.add_embed_field(
        name="\u200b",
        value="\u200b",
        inline=False
    )

    embed.add_embed_field(
        name="GitHub Action:",
        value=f"[View Here]({action_url})",
        inline=False
    )

    embed.add_embed_field(
        name="\u200b",
        value="\u200b",
        inline=False
    )

    embed.set_footer(
        text=type_vars[ntype]["footer_text"],
        icon_url=type_vars[ntype]["footer_icon_url"]
    )

    webhook.add_embed(embed)

    response = webhook.execute()
    if response.status_code >= 400:
        print(f"❌ Discord returned status {response.status_code}: {response.text}")
    else:
        print("✅ Sent message successfully.")


if __name__ == "__main__":
    parser = ArgumentParser(description="Send Canvas or Docker notifications to Discord.")
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
