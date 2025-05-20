## Example usage for docker_automation.yaml

```yaml
name: Update Docker Image on Push

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
    uses: byucscourseops/shared-workflows/.github/workflows/canvas-notify.yml@main
    with:
      discord_role: ${{ secrets.CICD_NOTIFY_DISCORD_ROLE }}
      course_id: "cs235_sp2025"
      course_info_path: "${{ github.workspace }}/_canvas-material/course-info/cs235_sp2025.json"
      global_args_path: "${{ github.workspace }}/_canvas-material/global_args.json"
      canvas_css_path: "${{ github.workspace }}/_canvas-material/canvas.css"  # Optional
      template_path: "${{ github.workspace }}/_canvas-material/course.canvas.md.xml.jinja"
      output_path: "${{ github.workspace }}/.github/logs/mdxcanvas_output.json"
    secrets:
      canvas_api_token: ${{ secrets.CANVAS_API_TOKEN }}
      discord_webhook_url: ${{ secrets.GHA_235_DISCORD_WEBHOOK }}
```
