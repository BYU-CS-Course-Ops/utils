## Example usage for docker_automation.yaml

```yaml
name: Update Docker Image on Push

on:
  workflow_dispatch:
  push:
    branches: [main]
  pull_request:
    branches: [main]
    types: [merged]

jobs:
  docker_automation:
    uses: BYU-CS-Course-Ops/utils/.github/workflows/docker_automation.yaml@main
    with:
      course_id: "235"
    secrets:
      discord_role: ${{ secrets.CICD_NOTIFY_DISCORD_ROLE }}
      docker_user: ${{ secrets.DOCKER_USER }}
      docker_password: ${{ secrets.DOCKER_PASSWORD }}
      discord_webhook_url: ${{ secrets.GHA_235_DISCORD_WEBHOOK }}
```

## Example usage for mdxcanvas_automation.yaml

```yaml
name: Update Canvas Material on Push

on:
  workflow_dispatch:
  push:
    branches: [main]
  pull_request:
    branches: [main]
    types: [merged]

jobs:
  update-canvas:
    uses: BYU-CS-Course-Ops/utils/.github/workflows/mdxcanvas_automation.yaml@main
    with:
      course_id: "235"
      course_info_path: "_canvas-material/course-info/cs235_sp2025.json"
      global_args_path: "_canvas-material/global_args.json"
      canvas_css_path: "_canvas-material/canvas.css"  # Optional
      template_path: "_canvas-material/course.canvas.md.xml.jinja"
      output_path: ".github/logs/mdxcanvas_output.json"
    secrets:
      discord_role: ${{ secrets.CICD_NOTIFY_DISCORD_ROLE }}
      canvas_api_token: ${{ secrets.CANVAS_API_TOKEN }}
      discord_webhook_url: ${{ secrets.GHA_235_DISCORD_WEBHOOK }}
```

## Example usage for poetry_prebuild.yaml

```yaml
name: MDXCanvas Prebuild

on:
  workflow_dispatch: 
  pull_request:
    branches: [main]
    types: [opened, synchronize]

jobs:
  mdxcanvas_prebuild:
    uses: BYU-CS-Course-Ops/utils/.github/workflows/poetry_prebuild.yaml@main
    with:
      pypi_package: "mdxcanvas"
```

## Example usage for poetry_publish.yaml

```yaml
name: MDXCanvas Publish

on:
  workflow_dispatch:
  push:
    branches: [main]
  pull_request:
    branches: [main]
    types: [merged]

jobs:
  mdxcanvas_publish:
    uses: BYU-CS-Course-Ops/utils/.github/workflows/poetry_publish.yaml@main
    with:
      pypi_package: "mdxcanvas"
    secrets:
      pypi_user: ${{ secrets.PYPI_USER }}
      pypi_password: ${{ secrets.PYPI_PASSWORD }}
      discord_webhook_url: ${{ secrets.GHA_BEANLAB_DISCORD_WEBHOOK }}
      discord_role: ${{ secrets.CICD_NOTIFY_DISCORD_ROLE }}
```
