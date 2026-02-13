from datetime import datetime

from notifications.resources import Notification, Embed, Field, Author, Footer
from notifications.formatting.formatting_utils import spacer, generate_fields, truncate_error, get_course_style, hex_to_int


def has_content(data) -> bool:
    return bool(
        data['updated_images']
        or data['failed_images']
        or data['error']
    )


def requires_review(data) -> bool:
    return bool(data["failed_images"] or data["error"])


def format_notification(data, course_id, author, author_icon, branch, action_url) -> Notification:
    style = get_course_style("docker")

    updated_images = (
        '\n'.join(f'- {image}'
                  for image in data['updated_images'])) \
        if data['updated_images'] \
        else '*No updated images*'

    failed_images = (
        '\n'.join(f'- {image}'
                  for image in data['failed_images'])) \
        if data['failed_images'] \
        else '*No items to review*'

    error = data["error"] if data['error'] else '*No errors*'
    if error != '*No errors*':
        error = truncate_error(error)

    return Notification(
        username=style["username"],
        avatar_url=style["avatar_url"],
        embeds=[Embed(
            title=style["title_template"].format(course_id=course_id),
            description=f'**`{branch}`**',
            color=hex_to_int(style["hex_color"]),
            timestamp=datetime.now().isoformat(),
            author=Author(name=author, icon_url=author_icon),
            footer=Footer(
                text=style["footer_text"],
                icon_url=style["footer_icon_url"],
            ),
            fields=[
                spacer(),
                *generate_fields(
                    name='**Updated Image(s):**',
                    value=updated_images,
                    inline=True,
                ),
                spacer(),
                *generate_fields(
                    name='**Failed Image(s):**',
                    value=failed_images,
                    inline=True,
                ),
                spacer(),
                *generate_fields(
                    name='**Error:**',
                    value=error,
                    inline=False,
                ),
                spacer(),
                Field(
                    name='**GitHub Action:**',
                    value=f'[View here]({action_url})',
                    inline=False,
                ),
                spacer(),
            ],
        )],
    )
