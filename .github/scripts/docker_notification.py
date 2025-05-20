from datetime import datetime
from send_notification import Field, space, generate_field

'''
Example payload (15 Apr 2025 - docker_notification.py):

{
    "updated_images": [],
    "failed_images": [],
    "error": ""
}
'''


def check_docker_payload(data) -> bool:
    """
    More specific check if we add more content types to the payload.
    The notification is only sent if there is an updated image, failed
    image or if there is an error.
    """
    return (
            data['updated_images']
            or data['failed_images']
            or data['error']
    )


def docker_format(data, course_id, author, author_icon, branch, cicd_id, action_url):
    cicd_role = f'<@&{cicd_id}>\n' if cicd_id else ''

    updated_images = (
        '\n'.join(f'- {image}'
                    for image in data['updated_images'])) \
        if data['updated_images'] \
        else '*No updated images*'


    failed_images = (
            cicd_role +
            '\n'.join(f'- {image}'
                      for image in data['failed_images'])) \
        if data['failed_images'] \
        else '*No items to review*'

    error = cicd_role + data["error"] if data['error'] else '*No errors*'

    return {
        "username": "Gradescope Notifications",
        "avatar_url": "https://tinyurl.com/mr2fyjse",
        "embeds": [{
            "author": {"name": author, "icon_url": author_icon},
            "title": f"CS {course_id} - Docker Updates",
            "description": f'**`{branch}`**',
            "color": 238076,
            "fields": [
                space(),
                *generate_field(
                    name='**Updated Image(s):**',
                    value=updated_images,
                    inline=True
                ),
                space(),
                *generate_field(
                    name='**Failed Image(s):**',
                    value=failed_images,
                    inline=True
                ),
                space(),
                *generate_field(
                    name='**Error:**',
                    value=error,
                    inline=False
                ),
                space(),
                Field(
                    name=f'**GitHub Action:**',
                    value=f'[View here]({action_url})',
                    inline=False
                ),
                space()
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "Docker GitHub Action",
                "icon_url": "https://tinyurl.com/32ffdfss"
            }
        }]
    }
