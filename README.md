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
      course_name: "CS 235 Spring 2025"
      course_url: "https://example.com/courses/cs235"
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
      course_name: "CS 235 Spring 2025"
      course_url: "https://example.com/courses/cs235"
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

```yaml
name: MDXCanvas Publish

on:
  workflow_dispatch:
  push:
    branches: [main]

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

## Example usage for release_notify.yaml

`release_notify.yaml` is a reusable release-focused Discord notification workflow. It checks out the calling repository and posts a notification for the current commit.

Inputs:

- `project_name` (**required**): Name displayed in the notification.
- `version` (optional): Explicit version. This takes precedence over automatic detection.
- `version_source` (optional): `toml` or `file`; defaults to `toml`.
- `version_path` (optional): Plaintext version-file path when `version_source` is `file`; defaults to `VERSION`.
- `changelog_path` (optional): Changelog path. The matching `## VERSION` section is included when present. Omit this for projects without a changelog.
- `success` (optional): Whether the release succeeded; defaults to `true`.

Required and optional secrets:

- `discord_webhook_url` (**required**): Discord webhook URL.
- `discord_role` (optional): Discord role ID to mention.

### Project using TOML version metadata

```yaml
jobs:
  notify-release:
    uses: BYU-CS-Course-Ops/utils/.github/workflows/release_notify.yaml@main
    with:
      project_name: "myteam"
      changelog_path: "src/myteam/CHANGELOG.md"
    secrets:
      discord_webhook_url: ${{ secrets.DISCORD_WEBHOOK_URL }}
      discord_role: ${{ secrets.DISCORD_ROLE_ID }}
```

When `version` is omitted, the workflow reads `[project].version` or `[tool.poetry].version` from `pyproject.toml`.

### Project using a plaintext VERSION file

```yaml
jobs:
  notify-release:
    uses: BYU-CS-Course-Ops/utils/.github/workflows/release_notify.yaml@main
    with:
      project_name: "MDXCanvas"
      version_source: "file"
      version_path: "mdxcanvas/VERSION"
    secrets:
      discord_webhook_url: ${{ secrets.DISCORD_WEBHOOK_URL }}
```

### Passing a version from an earlier job

A client workflow can read the version in an earlier job and pass it explicitly. The notification job must depend on that job with `needs`:

```yaml
jobs:
  get-version:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
    steps:
      - uses: actions/checkout@v4
      - id: version
        run: echo "version=$(cat VERSION)" >> "$GITHUB_OUTPUT"

  notify-release:
    needs: get-version
    uses: BYU-CS-Course-Ops/utils/.github/workflows/release_notify.yaml@main
    with:
      project_name: "MDXCanvas"
      version: ${{ needs.get-version.outputs.version }}
    secrets:
      discord_webhook_url: ${{ secrets.DISCORD_WEBHOOK_URL }}
```

The caller does not need a separate checkout for the reusable workflow. Projects without a changelog should omit `changelog_path`; the changelog section is omitted from the Discord message.

## Example usage for publish.yaml

`publish.yaml` is a reusable publishing workflow that checks release state, builds and publishes a package when the version is new, then invokes `release_notify.yaml`. Set `publisher` to either `uv` or `poetry`. It compares the current version with the previous commit and checks PyPI, so ordinary commits and already-published versions are skipped.

### Publishing with uv

Both publishing modes use a project-scoped PyPI API token. The workflow builds with the selected tool and uploads the resulting `dist/` files with the PyPA publishing action.

```yaml
jobs:
  publish:
    uses: BYU-CS-Course-Ops/utils/.github/workflows/publish.yaml@main
    with:
      pypi_package: "myteam"
      publisher: "uv"
      project_name: "myteam"              # Optional; defaults to pypi_package
      changelog_path: "src/myteam/CHANGELOG.md" # Optional
    secrets:
      pypi_token: ${{ secrets.PYPI_TOKEN }}
      discord_webhook_url: ${{ secrets.DISCORD_WEBHOOK_URL }}
      discord_role: ${{ secrets.DISCORD_ROLE_ID }} # Optional
```

### Publishing with Poetry and a VERSION file

```yaml
jobs:
  publish:
    uses: BYU-CS-Course-Ops/utils/.github/workflows/publish.yaml@main
    with:
      pypi_package: "mdxcanvas"
      publisher: "poetry"
      version_source: "file"
      version_path: "mdxcanvas/VERSION"
    secrets:
      pypi_token: ${{ secrets.PYPI_TOKEN }}
      discord_webhook_url: ${{ secrets.DISCORD_WEBHOOK_URL }}
      discord_role: ${{ secrets.DISCORD_ROLE_ID }} # Optional
```

Inputs forwarded to the release notification include `project_name`, `version`, `version_source`, `version_path`, and `changelog_path`. All projects must provide `pypi_token`. The selected publisher controls only how the package is built; both builds are uploaded with `pypa/gh-action-pypi-publish`. A notification is sent only when a new version needs publishing, including when the publish job fails.
