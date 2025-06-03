# Build the send notification script image

IMAGE_NAME="byucscourseops/send_course_notification"
IMAGE_TAG="latest"

docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${IMAGE_NAME}:${IMAGE_TAG} \
    --push \
    -f - . <<EOF
FROM python:3.11-slim

RUN apt-get update && apt-get install -y jq && rm -rf /var/lib/apt/lists/*

RUN pip install discord_webhook

WORKDIR /scripts

ADD canvas_notification.py /scripts/canvas_notification.py
ADD docker_notification.py /scripts/docker_notification.py
ADD send_course_notification.py /scripts/send_course_notification.py

EOF
