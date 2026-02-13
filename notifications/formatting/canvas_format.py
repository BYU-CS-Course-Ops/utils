from datetime import datetime

from notifications.resources import Notification, Embed, Field, Author, Footer
from notifications.formatting.formatting_utils import spacer, generate_fields, truncate_error, get_course_style, hex_to_int


def has_content(data) -> bool:
    return bool(
        data['deployed_content']
        or data['content_to_review']
        or data['error']
    )


def requires_review(data) -> bool:
    return bool(data["content_to_review"] or data["error"])


def format_notification(data, course_id, author, author_icon, branch, action_url) -> Notification:
    style = get_course_style("canvas")

    deployed_content = (
        '\n'.join(f'- **{rtype}**: [{content}]({link})' if link else f'- **{rtype}**: {content}'
                  for rtype, content, link in data['deployed_content'])) \
        if data['deployed_content'] \
        else '*No items deployed*'

    content_to_review = (
        '\n'.join(f'- [{dat[0]}]({dat[1]})'
                  for dat in data['content_to_review'])) \
        if data['content_to_review'] \
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
                    name='**Deployed Content:**',
                    value=deployed_content,
                    inline=False,
                ),
                spacer(),
                *generate_fields(
                    name='**Content to Review:**',
                    value=content_to_review,
                    inline=False,
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
