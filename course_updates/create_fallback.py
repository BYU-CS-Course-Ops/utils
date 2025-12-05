import json
from json import JSONDecodeError
from argparse import ArgumentParser


def has_valid_output(output_path: str, output_type: str) -> bool:
    try:
        data = json.load(open(output_path))
        if output_type == 'MDXCanvas':
            return all(key in data for key in ['deployed_content', 'content_to_review', 'error'])
        elif output_type == 'Docker':
            return all(key in data for key in ['updated_images', 'failed_images', 'error'])
    except (FileNotFoundError, JSONDecodeError):
        return False


def read_log_file(log_path: str) -> str | None:
    with open(log_path, 'r') as f:
        content = f.read().strip()
        return content if content else None


def create_fallback_output(output_type: str, output_path: str, stdout_log: str, stderr_log: str, action_url: str):
    if has_valid_output(output_path, output_type):
        return

    error_message = (
        read_log_file(stderr_log) or
        read_log_file(stdout_log) or
        f"{output_type} updates failed with no error output. Check the action logs: {action_url}"
    )

    if output_type == 'MDXCanvas':
        fallback_data = {"deployed_content": [], "content_to_review": [], "error": error_message}
    elif output_type == 'Docker':
        fallback_data = {"updated_images": [], "failed_images": [], "error": error_message}

    with open(output_path, 'w') as f:
        json.dump(fallback_data, f)


if __name__ == "__main__":
    parser = ArgumentParser(description="Create fallback output for MDXCanvas.")
    parser.add_argument("--output-type", required=True, choices=['Docker', 'MDXCanvas'])
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--stdout-log", required=True)
    parser.add_argument("--stderr-log", required=True)
    parser.add_argument("--action-url", required=True)
    args = parser.parse_args()

    create_fallback_output(args.output_type, args.output_path, args.stdout_log, args.stderr_log, args.action_url)
