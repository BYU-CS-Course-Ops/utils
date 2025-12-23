from argparse import ArgumentParser
import json
import os
from typing import TypedDict
from discord_webhook import DiscordWebhook, DiscordEmbed


class Field(TypedDict):
    name: str
    value: str
    inline: bool


def space(inline=False) -> Field:
    return Field(name="\u200b", value="\u200b", inline=inline)


def generate_field(name: str, value: str, inline: bool = False) -> list[Field]:
    # Check if this is a code block
    if value.startswith('```') and value.endswith('```'):
        # Extract content from code block
        lines = value.split('\n', 1)
        if len(lines) > 1:
            # Has content after opening ```
            rest = lines[1].rsplit('\n```', 1)[0]  # Remove closing ```

            if len(rest) > 1000:  # Leave room for ``` markers
                # Split content and wrap each chunk in code block
                chunks = []
                chunk_size = 1000
                for i in range(0, len(rest), chunk_size):
                    chunk = rest[i:i + chunk_size]
                    chunks.append(f"```\n{chunk}\n```")

                return [
                    Field(
                        name=name if i == 0 else f"{name} (continued)",
                        value=chunk_value,
                        inline=inline
                    ) for i, chunk_value in enumerate(chunks)
                ]

    # Original logic for non-code-block values
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


def truncate_error_message(error: str, max_chars: int = 900) -> str:
    """
    Extracts the most relevant error information for Discord:
    - If a traceback exists, keep only the last traceback
    - Trim to the final few stack frames
    - Always include the exception message
    """

    if not error:
        return f"```\nNo error output available.\n```"

    lines = error.splitlines()

    # Find all traceback starts
    traceback_indices = [
        i for i, line in enumerate(lines)
        if line.strip().startswith("Traceback (most recent call last):")
    ]

    if traceback_indices:
        # Use only the LAST traceback
        tb_start = traceback_indices[-1]
        relevant = lines[tb_start:]

        # Keep only the last N stack frames + exception
        # Stack frames usually come in pairs: File + code line
        MAX_LINES = 12
        if len(relevant) > MAX_LINES:
            relevant = ["... (traceback truncated) ..."] + relevant[-MAX_LINES:]

        message = "\n".join(relevant)
    else:
        # No traceback → take last meaningful chunk
        message = "\n".join(lines[-15:])

    # Hard cap for Discord
    if len(message) > max_chars:
        message = message[-max_chars:]
        message = "... (truncated) ...\n" + message

    return f"```\n{message}\n```"



def send_parsed_discord_embed(webhook_url: str, notification: dict, requires_review:bool, cicd_id: int = None):
    webhook = DiscordWebhook(
        url=webhook_url,
        username=notification.get("username"),
        avatar_url=notification.get("avatar_url"),
        content=f"<@&{cicd_id}>" if requires_review and cicd_id else None,
    )

    for embed_data in notification.get("embeds", []):
        embed = DiscordEmbed(
            title=embed_data.get("title"),
            description=embed_data.get("description"),
            color=embed_data.get("color"),
            timestamp=embed_data.get("timestamp")
        )

        # Optional author
        author = embed_data.get("author", {})
        if author:
            embed.set_author(
                name=author.get("name", ""),
                icon_url=author.get("icon_url", "")
            )

        # Optional footer
        footer = embed_data.get("footer", {})
        if footer:
            embed.set_footer(
                text=footer.get("text", ""),
                icon_url=footer.get("icon_url", "")
            )

        # Fields
        for field in embed_data.get("fields", []):
            field_name = field.get("name", "\u200b")
            field_value = field.get("value", "\u200b")

            # Ensure neither name nor value is empty (Discord requirement)
            if not field_name or not field_name.strip():
                field_name = "\u200b"
            if not field_value or not field_value.strip():
                field_value = "\u200b"

            embed.add_embed_field(
                name=field_name,
                value=field_value,
                inline=field.get("inline", False)
            )

        webhook.add_embed(embed)

    # Calculate approximate embed size
    total_size = 0
    for embed_data in notification.get("embeds", []):
        total_size += len(str(embed_data.get("title", "")))
        total_size += len(str(embed_data.get("description", "")))
        for field in embed_data.get("fields", []):
            total_size += len(field.get("name", ""))
            total_size += len(field.get("value", ""))

    if total_size > 4800:  # 80% of 6000 limit
        print(f"⚠️  Warning: Embed size ({total_size} chars) approaching Discord's 6000 char limit")
    if total_size > 6000:
        print(f"❌ Error: Embed size ({total_size} chars) exceeds Discord's 6000 char limit")

    response = webhook.execute()
    if response.status_code >= 400:
        print(f"❌ Discord returned status {response.status_code}: {response.text}")
    else:
        print("✅ Sent message successfully.")


def main(ntype, payload, course_id, author, author_icon, branch_name, action_url, cicd_id):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise EnvironmentError("DISCORD_WEBHOOK_URL environment variable is not set.")

    # Import formatter and checker
    if ntype == "canvas":
        from canvas_notification import canvas_format, check_canvas_payload, requires_canvas_review
        format_notification = canvas_format
        has_info = check_canvas_payload
        requires_review = requires_canvas_review
    elif ntype == "docker":
        from docker_notification import docker_format, check_docker_payload, requires_docker_review
        format_notification = docker_format
        has_info = check_docker_payload
        requires_review = requires_docker_review
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
        action_url=action_url,
    )

    send_parsed_discord_embed(webhook_url, notification, requires_review(data), cicd_id=cicd_id)

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
