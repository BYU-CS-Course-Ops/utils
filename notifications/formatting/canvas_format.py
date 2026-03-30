from datetime import datetime

from notifications.resources import Notification, Embed, Field, Author, Footer
from notifications.formatting.formatting_utils import (
    spacer, generate_fields, truncate_error, get_course_style, hex_to_int,
    build_resource_summary, resource_count_fields, course_info_field,
)


def has_content(data) -> bool:
    return bool(
        data['deployed_content']
        or data['content_to_review']
        or data['error']
    )


def requires_review(data) -> bool:
    return bool(data["content_to_review"] or data["error"])


def format_notification(data, course_id, author, author_icon, branch, action_url,
                        course_name=None, course_url=None) -> Notification:
    style = get_course_style("canvas")

    # Build fields list with actionable items first
    fields: list[Field] = []

    # Course info
    ci_field = course_info_field(course_name, course_url)
    if ci_field:
        fields.append(ci_field)

    # Resource type summary counts
    if data['deployed_content']:
        counts = build_resource_summary(data['deployed_content'])
        fields.append(spacer())
        fields.append(Field(name="**Deployment Summary:**", value="\u200b", inline=False))
        fields.extend(resource_count_fields(counts))

    # Content to Review -- actionable, shown first
    content_to_review = (
        '\n'.join(f'- [{dat[0]}]({dat[1]})'
                  for dat in data['content_to_review'])) \
        if data['content_to_review'] \
        else '*No items to review*'

    fields.append(spacer())
    fields.extend(generate_fields(
        name='**Content to Review:**',
        value=content_to_review,
        inline=False,
    ))

    # Deployed Content links
    deployed_content = (
        '\n'.join(f'- **{rtype}**: [{content}]({link})' if link else f'- **{rtype}**: {content}'
                  for rtype, content, link in data['deployed_content'])) \
        if data['deployed_content'] \
        else '*No items deployed*'

    fields.append(spacer())
    fields.extend(generate_fields(
        name='**Deployed Content:**',
        value=deployed_content,
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
