## Example usage for docker_automation.yaml

```yaml
name: Trigger Docker Workflow

on:
  push:
    branches: [main]
  pull_request:
    types: [closed]

jobs:
  call-shared:
    uses: BYU-CS-Course-Ops/utils/.github/workflows/docker_automation.yaml@main
    with:
      discord_role: ${{ secrets.CICD_NOTIFY_DISCORD_ROLE }}
      course_id: "235"
    secrets:
      docker_user: ${{ secrets.DOCKER_USER }}
      docker_password: ${{ secrets.DOCKER_PASSWORD }}
      discord_webhook_url: ${{ secrets.GHA_235_DISCORD_WEBHOOK }}
```

## Example usage for mdxcanvas_automation.yaml

```yaml
name: Update Canvas Material on Push

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
    types: [closed]

jobs:
  update-canvas:
    uses: BYU-CS-Course-Ops/utils/.github/workflows/mdxcanvas_automation.yaml
    with:
      discord_role: ${{ secrets.CICD_NOTIFY_DISCORD_ROLE }}
      course_id: "110"
    secrets:
      canvas_api_token: ${{ secrets.CANVAS_API_TOKEN }}
      discord_webhook_url: ${{ secrets.GHA_235_DISCORD_WEBHOOK }}
```
