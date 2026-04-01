from notifications.resources import Notification, Embed, Author, Footer, WebhookMessage
from notifications.formatting.formatting_utils import get_pypi_style, hex_to_int


def format_notification(ntype, author, author_icon, action_url, success, version) -> Notification:
    style = get_pypi_style(ntype)

    if success:
        description = f"Updated to version **`{version}`**\n\n-# [Action Log]({action_url})"
    else:
        description = f"An **error occurred** while updating {style['display_name']}.\n\n-# [Action Log]({action_url})"

    return Notification(
        username=style["username"],
        messages=[
            WebhookMessage(
                embeds=[
                    Embed(
                        title=style["title"],
                        description=description,
                        color=hex_to_int(style["hex_color"]),
                        timestamp="",
                        author=Author(name=author, icon_url=author_icon),
                        footer=Footer(
                            text=style["footer_text"],
                            icon_url=style["footer_icon_url"],
                        ),
                        fields=[],
                    )
                ],
            )
        ],
    )
