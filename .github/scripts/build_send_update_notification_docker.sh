# Build the send notification script image

IMAGE_NAME="byucscourseops/send_update_notification"
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

ADD send_notification.py /scripts/send_update_notification.py

EOF
