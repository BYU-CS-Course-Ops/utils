from notifications.resources import Field
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


def get_pypi_style(ntype: str) -> dict[str, str]:
    styles = _load_styles()
    for row in styles.get("PyPi Packages", []):
        if row.get("type") == ntype:
            return row
    return {}


def spacer(inline=False) -> Field:
    return Field(name="\u200b", value="\u200b", inline=inline)


def generate_fields(name: str, value: str, inline: bool = False) -> list[Field]:
    # Check if this is a code block
    if value.startswith('```') and value.endswith('```'):
        lines = value.split('\n', 1)
        if len(lines) > 1:
            rest = lines[1].rsplit('\n```', 1)[0]

            if len(rest) > 1000:
                chunks = []
                chunk_size = 1000
                for i in range(0, len(rest), chunk_size):
                    chunk = rest[i:i + chunk_size]
                    chunks.append(f"```\n{chunk}\n```")

                return [
                    Field(
                        name=name if i == 0 else f"{name} (continued)",
                        value=chunk_value,
                        inline=inline
                    ) for i, chunk_value in enumerate(chunks)
                ]

    # Original logic for non-code-block values
    if len(value) > 1024:
        chunks = [value[i:i + 1024] for i in range(0, len(value), 1024)]
        return [
            Field(
                name=name if i == 0 else f"{name} (continued)",
                value=chunk,
                inline=inline
            ) for i, chunk in enumerate(chunks)
        ]
    else:
        return [Field(name=name, value=value, inline=inline)]


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
