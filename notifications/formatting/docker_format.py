from datetime import datetime

from notifications.resources import Notification, Embed, Field, Author, Footer
from notifications.formatting.formatting_utils import (
    spacer, generate_fields, truncate_error, get_course_style, hex_to_int,
    course_info_field,
)


def has_content(data) -> bool:
    return bool(
        data['updated_images']
        or data['failed_images']
        or data['error']
    )


def requires_review(data) -> bool:
    return bool(data["failed_images"] or data["error"])


def format_notification(data, course_id, author, author_icon, branch, action_url,
                        course_name=None, course_url=None) -> Notification:
    style = get_course_style("docker")

    # Build fields list with actionable items first
    fields: list[Field] = []

    # Course info
    ci_field = course_info_field(course_name, course_url)
    if ci_field:
        fields.append(ci_field)

    # Summary counts
    updated_count = len(data['updated_images'])
    failed_count = len(data['failed_images'])
    fields.append(spacer())
    fields.append(Field(name="Updated", value=f"**{updated_count}**", inline=True))
    fields.append(Field(name="Failed", value=f"**{failed_count}**", inline=True))

    # Failed Images -- actionable, shown first
    failed_images = (
        '\n'.join(f'- {image}'
                  for image in data['failed_images'])) \
        if data['failed_images'] \
        else '*No failed images*'

    fields.append(spacer())
    fields.extend(generate_fields(
        name='**Failed Image(s):**',
        value=failed_images,
        inline=False,
    ))

    # Updated Images
    updated_images = (
        '\n'.join(f'- {image}'
                  for image in data['updated_images'])) \
        if data['updated_images'] \
        else '*No updated images*'

    fields.append(spacer())
    fields.extend(generate_fields(
        name='**Updated Image(s):**',
        value=updated_images,
        inline=False,
    ))

    # Error
    error = data["error"] if data['error'] else '*No errors*'
    if error != '*No errors*':
        error = truncate_error(error)

    fields.append(spacer())
    fields.extend(generate_fields(
        name='**Error:**',
        value=error,
        inline=False,
    ))

    # GitHub Action link
    fields.append(spacer())
    fields.append(Field(
        name='**GitHub Action:**',
        value=f'[View here]({action_url})',
        inline=False,
    ))
    fields.append(spacer())

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
            fields=fields,
        )],
    )
