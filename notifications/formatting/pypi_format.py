from datetime import datetime

from notifications.resources import Notification, Embed, Field, Author, Footer
from notifications.formatting.formatting_utils import spacer, get_pypi_style, hex_to_int


def format_notification(ntype, author, author_icon, action_url, success, version) -> Notification:
    style = get_pypi_style(ntype)

    if success:
        description = f"Updated to version **`{version}`**"
    else:
        description = f"An **error occurred** while updating {style['display_name']}."

    return Notification(
        username=style["username"],
        embeds=[Embed(
            title=style["title"],
            description=description,
            color=hex_to_int(style["hex_color"]),
            timestamp=datetime.now().isoformat(),
            author=Author(name=author, icon_url=author_icon),
            footer=Footer(
                text=style["footer_text"],
                icon_url=style["footer_icon_url"],
            ),
            fields=[
                spacer(),
                Field(
                    name="GitHub Action:",
                    value=f"[View Here]({action_url})",
                    inline=False,
                ),
                spacer(),
            ],
        )],
    )
