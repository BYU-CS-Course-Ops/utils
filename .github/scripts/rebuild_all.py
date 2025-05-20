from pathlib import Path

EXCLUDED = [
    'build-cs235-autograder-base.sh',
    'build-xues-cling-kernel-docker.sh',
    'old-labs'
]

def has_include(files: str) -> bool:
    """
    Check if the touched files include the `include` folder.

    :param files: The list of changed files in the repository.
    :return: bool
    """
    for file in files.split():
        file = Path(file)
        if 'include' in file.parts:
            return True
    return False


def find_all_scripts(dir: Path, docker_files) -> set[Path]:
    """
    Find all docker scripts in the given directory.

    :param dir:
    :param docker_files:
    :return:
    """
    if dir.is_dir():
        if dir.name in EXCLUDED:
            return docker_files
        for item in dir.iterdir():
            find_all_scripts(item, docker_files)
    elif (
            dir.is_file()
            and dir.name not in EXCLUDED
            and dir.name.startswith('build')
            and dir.name.endswith('docker.sh')
    ):
        docker_files.add(dir.absolute())
    return docker_files


def rebuild_all() -> set[Path]:
    """
    Get all docker scripts in the repository.

    :return: A set of docker scripts.
    """
    docker_files = set()
    root = Path(__file__).parent.parent.parent.absolute()
    return find_all_scripts(root, docker_files)
