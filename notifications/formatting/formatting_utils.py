from markdowndata import load
from pathlib import Path


STYLE_PATH = Path(__file__).parent / "style.md"


def hex_to_int(hex_color: str) -> int:
    return int(hex_color.lstrip('#'), 16)


def _load_styles():
    with open(STYLE_PATH) as f:
        return load(f)


def get_course_style(ntype: str) -> dict[str, str]:
    styles = _load_styles()
    for row in styles.get("Course", []):
        if row.get("type") == ntype:
            return row
    return {}


def truncate_error(error: str, max_chars: int = 900) -> str:
    if not error:
        return "```\nNo error output available.\n```"

    lines = error.splitlines()

    traceback_indices = [
        i for i, line in enumerate(lines)
        if line.strip().startswith("Traceback (most recent call last):")
    ]

    if traceback_indices:
        tb_start = traceback_indices[-1]
        relevant = lines[tb_start:]

        MAX_LINES = 12
        if len(relevant) > MAX_LINES:
            relevant = ["... (traceback truncated) ..."] + relevant[-MAX_LINES:]

        message = "\n".join(relevant)
    else:
        message = "\n".join(lines[-15:])

    if len(message) > max_chars:
        message = message[-max_chars:]
        message = "... (truncated) ...\n" + message

    return f"```\n{message}\n```"
