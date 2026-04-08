from discord_webhook import DiscordWebhook, DiscordEmbed

from .discord_limits import CONTENT_LIMIT, split_content
from .resources import Embed, Notification


def _build_discord_embed(embed_data: Embed) -> DiscordEmbed:
    embed = DiscordEmbed(
        title=embed_data.title,
        description=embed_data.description,
        color=embed_data.color,
        timestamp=embed_data.timestamp or None,
    )

    if embed_data.author:
        embed.set_author(
            name=embed_data.author.name,
            icon_url=embed_data.author.icon_url,
        )

    if embed_data.footer:
        embed.set_footer(
            text=embed_data.footer.text,
            icon_url=embed_data.footer.icon_url,
        )

    for field in embed_data.fields:
        embed.add_embed_field(
            name=field.name or "\u200b",
            value=field.value or "\u200b",
            inline=field.inline,
        )

    return embed


def _execute_webhook(webhook_url: str, notification: Notification, content: str | None = None, embeds: list[Embed] | None = None):
    webhook = DiscordWebhook(
        url=webhook_url,
        username=notification.username,
        avatar_url=notification.avatar_url,
        content=content,
    )

    for embed_data in embeds or []:
        webhook.add_embed(_build_discord_embed(embed_data))

    return webhook.execute()


def send_notification(webhook_url: str, notification: Notification):
    for message in notification.messages:
        content_chunks = split_content(message.content, CONTENT_LIMIT) if message.content else [None]

        for index, content in enumerate(content_chunks):
            try:
                response = _execute_webhook(
                    webhook_url=webhook_url,
                    notification=notification,
                    content=content,
                    embeds=message.embeds if index == 0 else [],
                )
            except Exception as e:
                print(f"Error sending notification: {e}")
                continue

            if response.status_code >= 400:
                print(f"Discord returned status {response.status_code}: {response.text}")
            else:
                print("Sent message successfully.")
