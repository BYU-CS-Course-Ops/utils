from datetime import datetime
from send_notification import Field, space, generate_field

'''
Example payload (mdxcanvas -v 0.3.27):

{
    "deployed_content": [
        [
            "file",
            "beanlab.png",
            null
        ],
        [
            "page",
            "Example Page",
            "https://byu.instructure.com/courses/20736/pages/example-page-13"
        ]
    ],
    "content_to_review": [
        [
            "HW 7a - Set Performance",
            "https://byu.instructure.com/courses/27547/quizzes/493001"
        ]
    ],
    "error": ""
}
'''


def check_canvas_payload(data) -> bool:
    """
    More specific check if we add more content types to the payload.
    The notification is only sent if there is something to deploy,
    review or if there is an error.
    """
    return (
            data['deployed_content']
            or data['content_to_review']
            or data['error']
    )


def canvas_format(data, course_id, author, author_icon, branch, cicd_id, action_url):
    cicd_role = f'<@&{cicd_id}>\n' if cicd_id else ''

    deployed_content = (
        '\n'.join(f'- **{rtype}**: [{content}]({link})' if link else f'- **{rtype}**: {content}'
                  for rtype, content, link in data['deployed_content'])) \
        if data['deployed_content'] \
        else '*No items deployed*'

    content_to_review = (
            cicd_role +
            '\n'.join(f'- [{dat[0]}]({dat[1]})'
                      for dat in data['content_to_review'])) \
        if data['content_to_review'] \
        else '*No items to review*'

    error = cicd_role + data["error"] if data['error'] else '*No errors*'

    return {
        "username": "Canvas Notifications",
        "avatar_url": "https://tinyurl.com/ek4ytkan",
        "embeds": [{
            "author": {"name": author, "icon_url": author_icon},
            "title": f"CS {course_id} - Course Updates",
            "description": f'**`{branch}`**',
            "color": 15861021,
            "fields": [
                space(),
                *generate_field(
                    name='**Deployed Content:**',
                    value=deployed_content,
                    inline=False
                ),
                space(),
                *generate_field(
                    name='**Content to Review:**',
                    value=content_to_review,
                    inline=False
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
                "text": "MDXCanvas GitHub Action",
                "icon_url": "https://tinyurl.com/4ky2afzx"
            }
        }]
    }
