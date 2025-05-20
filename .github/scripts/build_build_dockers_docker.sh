# Build the build_dockers script image

IMAGE_NAME="byucscourseops/build_dockers"
IMAGE_TAG="latest"

docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${IMAGE_NAME}:${IMAGE_TAG} \
    --push \
    -f - . <<EOF
FROM python:3.11-slim

RUN apt-get update && apt-get install -y jq && rm -rf /var/lib/apt/lists/*

WORKDIR /scripts

ADD build_dockers.py /scripts/build_dockers.py

ENTRYPOINT ["/bin/bash"]
EOF
