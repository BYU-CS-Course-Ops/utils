"""Read the course id and Canvas URL out of a course's course-info file.

    CANVAS_COURSE_ID -> course_id
    CANVAS_API_URL   -> course_url, as "<api_url>courses/<id>"

Course-info files are YAML, except CS 235's which is JSON. JSON is valid YAML,
so one parser covers both. The course name is not read here: it is a
COURSE_SETTINGS XML fragment in some files and a COURSE_NAME field in others.

Usage, from a workflow step:

    python3 notifications/course_facts.py <course-info-path> >> "$GITHUB_OUTPUT"
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml


class CourseFactsError(ValueError):
    """The file cannot answer the question, with a reason a caller can act on."""


def course_facts(path: Path) -> dict[str, str]:
    """Return {'course_id', 'course_url'} read from a course-info file."""
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise CourseFactsError(f"{path} is neither valid YAML nor JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise CourseFactsError(f"{path} does not contain a mapping")

    course_id = data.get("CANVAS_COURSE_ID")
    api_url = data.get("CANVAS_API_URL")
    missing = [k for k, v in (("CANVAS_COURSE_ID", course_id),
                              ("CANVAS_API_URL", api_url)) if v in (None, "")]
    if missing:
        raise CourseFactsError(f"{path} does not set {' and '.join(missing)}")

    # rstrip so a file without the usual trailing slash does not double it.
    return {
        "course_id": str(course_id).strip(),
        "course_url": f"{str(api_url).strip().rstrip('/')}/courses/{str(course_id).strip()}",
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    try:
        for key, value in course_facts(Path(argv[1])).items():
            print(f"{key}={value}")
    except (CourseFactsError, OSError) as exc:
        print(f"cannot derive course facts: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
