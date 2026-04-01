from markdowndata import load
from pathlib import Path

# ── Resource type badge emoji mapping ────────────────────────────────────────
# Keys are lowercase for case-insensitive matching.
RESOURCE_EMOJI: dict[str, str] = {
    "page":         "📄",
    "quiz":         "📝",
    "assignment":   "📎",
    "module":       "📦",
    "module_item":  "📂",
    "discussion":   "💬",
    "file":         "📁",
    "externalurl":  "🔗",
    "external_url": "🔗",
    "announcement": "📢",
    "syllabus":     "📋",
}


def emoji_for(resource_type: str) -> str:
    return RESOURCE_EMOJI.get(resource_type.lower(), "📌")


# ── Field chunking (Discord field value limit: 1024 chars) ──────────────────
MAX_FIELD_CHARS = 1024


def chunk_field_lines(
    lines: list[str],
    max_chars: int = MAX_FIELD_CHARS,
) -> list[str]:
    """Split a list of formatted lines into chunks that fit Discord's field value limit.

    Returns a list of joined strings, each under *max_chars*.
    """
    chunks: list[str] = []
    current_lines: list[str] = []
    current_len = 0

    for line in lines:
        needed = len(line) + (1 if current_lines else 0)  # +1 for newline
        if current_lines and current_len + needed > max_chars:
            chunks.append("\n".join(current_lines))
            current_lines = [line]
            current_len = len(line)
        else:
            current_lines.append(line)
            current_len += needed

    if current_lines:
        chunks.append("\n".join(current_lines))

    return chunks


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


def get_pypi_style(ntype: str) -> dict[str, str]:
    styles = _load_styles()
    for row in styles.get("PyPi Packages", []):
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
