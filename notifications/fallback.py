import json
from json import JSONDecodeError
from argparse import ArgumentParser
from typing import Optional


REQUIRED_KEYS = {
    "MDXCanvas": {"deployed_content", "content_to_review", "error"},
    "Docker": {"updated_images", "failed_images", "error"},
}


def has_valid_output(output_path: str, output_type: str) -> bool:
    try:
        with open(output_path, "r") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return False

        return REQUIRED_KEYS[output_type].issubset(data.keys())

    except (FileNotFoundError, JSONDecodeError):
        return False


def read_log_file(log_path: str) -> Optional[str]:
    try:
        with open(log_path, "r") as f:
            content = f.read().strip()
            return content or None
    except FileNotFoundError:
        return None


def create_fallback_output(
    output_type: str,
    output_path: str,
    stdout_log: str,
    stderr_log: str,
    action_url: str,
):
    if has_valid_output(output_path, output_type):
        print("Valid output detected — skipping fallback generation.")
        return

    log_content = read_log_file(stderr_log) or read_log_file(stdout_log)

    error_message = (
        log_content
        or f"{output_type} updates failed with no error output. "
           f"Check the action logs: {action_url}"
    )

    if output_type == "MDXCanvas":
        fallback_data = {
            "deployed_content": [],
            "content_to_review": [],
            "error": error_message,
        }
    else:  # Docker
        fallback_data = {
            "updated_images": [],
            "failed_images": [],
            "error": error_message,
        }

    with open(output_path, "w") as f:
        json.dump(fallback_data, f, indent=2)

    print(f"Fallback output written to {output_path}")


if __name__ == "__main__":
    parser = ArgumentParser(description="Create fallback output for MDXCanvas or Docker.")
    parser.add_argument("--output-type", required=True, choices=["Docker", "MDXCanvas"])
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--stdout-log", required=True)
    parser.add_argument("--stderr-log", required=True)
    parser.add_argument("--action-url", required=True)
    args = parser.parse_args()

    create_fallback_output(
        args.output_type,
        args.output_path,
        args.stdout_log,
        args.stderr_log,
        args.action_url,
    )
