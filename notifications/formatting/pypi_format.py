from datetime import datetime

from notifications.resources import Notification, Embed, Field, Author, Footer, WebhookMessage
from notifications.formatting.formatting_utils import spacer, get_pypi_style, hex_to_int


def format_notification(
    ntype,
    author,
    author_icon,
    action_url,
    success,
    version,
    old_version=None,
) -> Notification:
    style = get_pypi_style(ntype)
    pypi_name = style.get("pypi_name", ntype)

    if success:
        if old_version:
            description = f"**`{old_version}`** \u2192 **`{version}`**"
        else:
            description = f"Updated to version **`{version}`**"
    else:
        description = f"An **error occurred** while updating {style['display_name']}."

    fields: list[Field] = [spacer()]

    if success and version:
        fields.append(
            Field(
                name="**PyPI Package:**",
                value=f"[{pypi_name} v{version}](https://pypi.org/project/{pypi_name}/{version}/)",
                inline=False,
            )
        )
        fields.append(spacer())

    fields.append(
        Field(
            name="**GitHub Action:**",
            value=f"[View Here]({action_url})",
            inline=False,
        )
    )
    fields.append(spacer())

    return Notification(
        username=style["username"],
        messages=[
            WebhookMessage(
                embeds=[
                    Embed(
                        title=style["title"],
                        description=description,
                        color=hex_to_int(style["hex_color"]),
                        timestamp=datetime.now().isoformat(),
                        author=Author(name=author, icon_url=author_icon),
                        footer=Footer(
                            text=style["footer_text"],
                            icon_url=style["footer_icon_url"],
                        ),
                        fields=fields,
                    )
                ],
            )
        ],
    )
