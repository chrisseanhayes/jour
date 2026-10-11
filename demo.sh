#!/usr/bin/env sh
set -eu

IMAGE="jour-demo"
VOLUME="jour-demo-data"

random_suffix() {
    od -An -N4 -tx1 /dev/urandom | tr -d ' \n'
}

cd "$(dirname "$0")"

echo "==> Building demo image: $IMAGE"
podman build -t "$IMAGE" -f Containerfile .

echo "==> Opening an interactive shell (run 'jour' commands inside)"
podman run --rm -it --name "$IMAGE-$(random_suffix)" \
    -v "$VOLUME:/root/.jour" "$IMAGE" sh
