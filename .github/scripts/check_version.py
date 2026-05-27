import sys


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <build_version> <pypi_version>")
        sys.exit(1)

    build = tuple(int(x) for x in sys.argv[1].split("."))

    if sys.argv[2] == "null":
        print(f"{build} vs (not on PyPI) — first publish")
        return

    pypi = tuple(int(x) for x in sys.argv[2].split("."))
    print(f"{build} vs {pypi}")

    if build > pypi:
        print("Version bumped — safe to publish")
    else:
        print(f"Build version {build} is not newer than PyPI version {pypi}")
        sys.exit(1)


if __name__ == "__main__":
    main()
