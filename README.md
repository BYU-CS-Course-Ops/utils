## Example usage for docker_automation.yaml

```yaml
name: Update Docker Image on Push

on:
  workflow_dispatch:
  push:
    branches: [main]

jobs:
  docker_automation:
    uses: BYU-CS-Course-Ops/utils/.github/workflows/docker_automation.yaml@main
    with:
      course_id: "235"
      course_info_path: "_canvas-material/course-info/cs235_sp2025.json"  # Optional
      global_args_path: "_canvas-material/global_args.json"  # Optional
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

jobs:
  update-canvas:
    uses: BYU-CS-Course-Ops/utils/.github/workflows/mdxcanvas_automation.yaml@main
    with:
      course_id: "235"
      mdxcanvas_version: "0.3.0"
      course_info_path: "_canvas-material/course-info/cs235_sp2025.json"
      global_args_path: "_canvas-material/global_args.json"
      canvas_css_path: "_canvas-material/canvas.css"  # Optional
      template_path: "_canvas-material/course.canvas.md.xml.jinja"
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

> **Important:** This workflow uses PyPI OIDC trusted publishers instead of API tokens.
> The calling workflow **must** include `permissions: id-token: write` or publishing
> will fail with a `startup_failure` error and no logs.

```yaml
name: MDXCanvas Publish

on:
  workflow_dispatch:
  push:
    branches: [main]

permissions:
  id-token: write

jobs:
  mdxcanvas_publish:
    uses: BYU-CS-Course-Ops/utils/.github/workflows/poetry_publish.yaml@main
    with:
      pypi_package: "mdxcanvas"
    secrets:
      discord_webhook_url: ${{ secrets.GHA_BEANLAB_DISCORD_WEBHOOK }}
      discord_role: ${{ secrets.CICD_NOTIFY_DISCORD_ROLE }}
```

## Migrating poetry_publish.yaml to OIDC

The `poetry_publish.yaml` workflow now uses [PyPI trusted publishers](https://docs.pypi.org/trusted-publishers/) (OIDC) instead of username/password API tokens.

### Steps to migrate

1. **Configure a trusted publisher on PyPI**
   - Go to your package on [pypi.org](https://pypi.org) > Manage > Publishing
   - Add a new "GitHub Actions" publisher:
     - **Owner:** your GitHub org (e.g., `BYU-CS-Course-Ops`)
     - **Repository:** the repo that calls the workflow
     - **Workflow name:** the filename of your *calling* workflow (e.g., `publish.yaml`), **not** `poetry_publish.yaml`
     - **Environment:** leave blank

2. **Add `permissions: id-token: write` to your calling workflow**
   - This must be at the **workflow level**, not the job level
   - Without this, GitHub Actions returns a `startup_failure` with no logs

3. **Remove old secrets**
   - Delete the `pypi_user` and `pypi_password` lines from your workflow's `secrets:` block
   - Optionally remove the `PYPI_USER` and `PYPI_PASSWORD` repository secrets from GitHub Settings

4. **Keep Discord secrets** — `discord_webhook_url` and `discord_role` are still required

## Post-merge cleanup

After merging PR #7, update the testing repo (`testkapua/testing-repo`) workflow refs from `@claude/wonderful-lovelace` to `@main`:
- `.github/workflows/mdxcanvas_automation.yaml`
- `.github/workflows/docker_automation.yaml`
- `.github/workflows/poetry_publish.yaml`
