import argparse
from dataclasses import dataclass, field
from pathlib import Path
import subprocess
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
    :return: A set of docker scripts.
    """
    docker_images = set()

    # Find the assignment folders from the list of changed files
    changed_assignments = find_assignments(files)

    for assignment in changed_assignments:
        docker_image = find_build_docker_scripts(assignment)

        if docker_image:
            docker_images.add(docker_image)

    return docker_images


def is_base_image(docker_script: Path) -> bool:
    """
    Determines if a docker script is for a base image.

    :param docker_script: Path to the docker build script
    :return: True if this is a base image script
    """
    script_name = docker_script.name.lower()
    parent_name = docker_script.parent.name.lower()

    return 'base' in script_name or 'base' in parent_name


def separate_base_and_assignment_images(docker_scripts: set[Path]) -> tuple[list[Path], list[Path]]:
    """
    Separates docker scripts into base images and assignment images.

    :param docker_scripts: Set of all docker build scripts
    :return: Tuple of (base_images, assignment_images)
    """
    base_images = []
    assignment_images = []

    for script in docker_scripts:
        if is_base_image(script):
            base_images.append(script)
        else:
            assignment_images.append(script)

    return base_images, assignment_images


def build_docker_image(docker_script: Path, result: DockerBuildResult) -> bool:
    """
    Builds a single docker image synchronously.

    :param docker_script: Path to the docker build script
    :param result: Result object to track success/failure
    :return: True if build succeeded, False otherwise
    """
    print(f"Building: {docker_script.name}")

    process = subprocess.Popen(
        ['bash', str(docker_script)],
        cwd=docker_script.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    stdout, stderr = process.communicate()

    if process.returncode == 0:
        result.add_updated_image(docker_script)
        print(f"✓ Successfully built: {docker_script.name}")
        return True
    else:
        result.add_failed_image(docker_script)
        print(f"✗ Failed to build: {docker_script.name}")
        print(stderr)
        return False


def build_images_parallel(docker_scripts: list[Path], result: DockerBuildResult):
    """
    Builds multiple docker images in parallel.

    :param docker_scripts: List of docker build scripts
    :param result: Result object to track success/failure
    """
    if not docker_scripts:
        return

    processes = []

    print(f"Building {len(docker_scripts)} images in parallel...")

    for docker_script in docker_scripts:
        process = subprocess.Popen(
            ['bash', str(docker_script)],
            cwd=docker_script.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        processes.append((process, docker_script))

    # Wait for all processes to complete
    for process, docker_script in processes:
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            result.add_updated_image(docker_script)
            print(f"✓ Successfully built: {docker_script.name}")
        else:
            result.add_failed_image(docker_script)
            print(f"✗ Failed to build: {docker_script.name}")
            print(stderr)


def run_docker_scripts(docker_scripts: set[Path], result: DockerBuildResult):
    """
    Runs the docker scripts. Base images are built first sequentially,
    then assignment images are built in parallel.

    :param docker_scripts: The set of docker scripts to run.
    :param result: The result object to track build outcomes.
    """
    if not docker_scripts:
        print("No docker scripts to build")
        return

    # Separate base and assignment images
    base_images, assignment_images = separate_base_and_assignment_images(docker_scripts)

    # Build base images first (sequentially)
    if base_images:
        print(f"\n=== Building {len(base_images)} base image(s) first ===")
        for base_image in base_images:
            success = build_docker_image(base_image, result)
            if not success:
                print(f"Warning: Base image {base_image.name} failed to build")

    # Build assignment images in parallel
    if assignment_images:
        print(f"\n=== Building {len(assignment_images)} assignment image(s) ===")
        build_images_parallel(assignment_images, result)

    print("\n=== Build Summary ===")
    print(f"Updated: {len(result.updated_images)}")
    print(f"Failed: {len(result.failed_images)}")


def collect_docker_files(files: str, root: Path) -> set[Path]:
    """
    Collects all docker build scripts that need to be run.

    :param files: Space-separated string of changed files
    :param root: Root directory of the repository
    :return: Set of docker build scripts to run
    """
    # Check if the include folder has been modified
    # If yes, rebuild all docker images
    if has_include(files):
        return rebuild_all(root)

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
    docker_files_from_assignments = find_docker_images(changed_files)

    # Union docker files
    return updated_docker_files | docker_files_from_assignments


def main(files: str, output_file: str, root_dir: str):
    root = Path(root_dir).resolve()

    # Collect all docker files that need to be built
    docker_files = collect_docker_files(files, root)

    # Initialize the output JSON object
    result = DockerBuildResult()

    # Create the output directory if it doesn't exist
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    # Build docker images
    try:
        run_docker_scripts(docker_files, result)
    except Exception as e:
        result.add_error_message(str(e))
        print(f"Error during build process: {e}")

    # Write the output to the specified file
    with open(output_file, 'w') as f:
        f.write(json.dumps(result.output(), indent=4))

    print(f"\nResults written to: {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--files')
    parser.add_argument('--output-file', required=True)
    parser.add_argument('--root-dir', required=True)
    args = parser.parse_args()

    main(files=args.files, output_file=args.output_file, root_dir=args.root_dir)