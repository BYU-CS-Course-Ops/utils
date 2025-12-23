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


def truncate_error_message(error: str, action_url: str, max_length: int = 1800) -> str:
    """
    Format error for Discord. Uses code blocks for long/multi-line errors only.
    """
    # Check if error is short and simple (single line)
    is_short = len(error) <= 200 and '\n' not in error.strip()

    if is_short:
        # Short error: just return as-is (no code block)
        return error

    # Long error: use code block formatting
    if len(error) <= max_length:
        # Wrap in code block
        return f"```text\n{error}\n```"

    # Extract last exception (most important)
    lines = error.split('\n')

    # Find the last "Error:" or "Exception:" line
    last_exception_idx = -1
    for i in range(len(lines) - 1, -1, -1):
        if 'Error' in lines[i] or 'Exception' in lines[i] or 'Traceback' in lines[i]:
            last_exception_idx = i
            break

    # Show last 20-25 lines (usually captures the final exception)
    if last_exception_idx > 0:
        start_idx = max(0, len(lines) - 25)
        truncated_lines = lines[start_idx:]
        truncated = '\n'.join(truncated_lines)
    else:
        # Fallback: just take last N chars
        truncated = error[-max_length:]

    # Ensure it fits
    if len(truncated) > max_length - 200:  # Leave room for message
        truncated = truncated[-(max_length - 200):]

    # Format with code block and link
    result = f"```text\n{truncated}\n```\n\n[View full error in GitHub Action logs]({action_url})"

    return result


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
