import argparse
from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import os
import json

from rebuild_all import has_include, rebuild_all


@dataclass
class DockerBuildResult:
    updated_images: list[str] = field(default_factory=list)
    failed_images: list[str] = field(default_factory=list)
    error: str = ""

    def add_updated_image(self, docker_image: Path):
        self.updated_images.append(docker_image.name)

    def add_failed_image(self, docker_image: Path):
        self.failed_images.append(docker_image.name)

    def add_error_message(self, error: str):
        self.error = error

    def output(self):
        return {
            "updated_images": self.updated_images,
            "failed_images": self.failed_images,
            "error": self.error,
        }


def find_build_docker_scripts(dir: Path) -> Path | None:
    """
    Finds the build docker scripts in the given directory.

    :param dir: The directory to search in. (Ideally, this is an assignment folder)
    """
    for file in dir.iterdir():
        if file.is_file() and file.name.startswith('build') and file.name.endswith('docker.sh'):
            return file.absolute()
    return None


def find_assignments(files: list[Path]) -> set[Path]:
    """
    Finds the assignment directories from the list of changed files.

    :param files: The list of changed files.
    :return: A set of assignment folders.
    """
    assignments = set()
    for file in files:
        file = Path(file)

        # Check if the file is in a solution folder
        if 'solution' in file.parent.name:
            assignments.add(file.parent.parent)

        # Check if the file is a test file
        elif 'worlds' in file.parent.name or 'test_files' in file.parent.name:
            assignments.add(file.parent.parent.parent)

        # Check if the file is in an activities json file
        elif 'activities' in file.name:
            assignments.add(file.parent)

    return assignments


def find_docker_images(files: list[Path]) -> set[Path]:
    """
    Finds the docker scripts for the changed assignments.

    :param files: The list of changed files in the repository.
    :return: A list of docker scripts.
    """
    docker_images = set()

    # Find the assignment folders from the list of changed files
    changed_assignments = find_assignments(files)

    for assignment in changed_assignments:
        docker_image = find_build_docker_scripts(assignment)

        if docker_image:
            docker_images.add(docker_image)

    return docker_images


def run_docker_scripts(docker_scripts: set[Path], result):
    """
    Runs the docker scripts and prints their output.

    :param docker_scripts: The list of docker scripts to run.
    :param result: The result JSON object.
    """
    processes = []

    for docker_image in docker_scripts:
        r_fd, w_fd = os.pipe()  # Create a pipe

        # Run script with stdout redirected to write pipe
        p = subprocess.Popen(
            ['bash', str(docker_image)], cwd=docker_image.parent,
            stdout=w_fd, stderr=subprocess.PIPE, universal_newlines=True
        )

        os.close(w_fd)
        processes.append((p, r_fd, docker_image))

    for p, read_pipe, docker_image in processes:
        stderr = p.stderr.read()  # Read stderr
        p.stderr.close()
        p.wait()

        if p.returncode == 0:
            result.add_updated_image(docker_image)
        else:
            result.add_failed_image(docker_image)
            print(stderr)


def main(files: str, output_file: str, root_dir: str):
    root = Path(root_dir).resolve()

    # Check if the include folder has been modified
    # If yes, rebuild all docker images
    if has_include(files):
        docker_files = rebuild_all(root)

    # If no, find the docker images for the changed assignments
    else:
        # Pathify the diff files
        changed_files = [
            (root / file).resolve()
            for file in files.split()
        ]

        # Get updated scripts from the changed files
        updated_docker_files = {
            file.resolve()
            for file in changed_files
            if file.is_file and file.name.startswith('build') and file.name.endswith('docker.sh')
        }

        # Get docker files from changed assignments
        docker_files = find_docker_images(changed_files)

        # Union docker files
        docker_files = updated_docker_files | docker_files

    # Initialize the output JSON object
    result = DockerBuildResult()

    # Create the output directory if it doesn't exist
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    # Build docker images
    try:
        run_docker_scripts(docker_files, result)
    except Exception as e:
        result.add_error_message(str(e))

    # Write the output to the specified file
    with open(output_file, 'w') as f:
        f.write(json.dumps(result.output(), indent=4))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--files')
    parser.add_argument('--output-file', required=True)
    parser.add_argument('--root-dir', required=True)
    args = parser.parse_args()

    main(files=args.files, output_file=args.output_file, root_dir=args.root_dir)
