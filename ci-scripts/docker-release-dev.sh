#!/usr/bin/env bash
#
# Release dev version to dockerhub registry.
#
# Required globals:
#   REGISTRY_USERNAME
#   REGISTRY_PASSWORD
#   REGISTRY_URL

set -ex

validate() {
  # mandatory parameters
  : REGISTRY_USERNAME="${REGISTRY_USERNAME:?'REGISTRY_USERNAME variable missing.'}"
  : REGISTRY_PASSWORD="${REGISTRY_PASSWORD:?'REGISTRY_PASSWORD variable missing.'}"
  : REGISTRY_URL="${REGISTRY_URL:?'REGISTRY_URL variable missing.'}"
}

IMAGE=$1
VERSION=$(semversioner current-version)

validate
echo "${REGISTRY_PASSWORD}" | docker login --username "$REGISTRY_USERNAME" --password-stdin "$REGISTRY_URL"

docker tag "${IMAGE}" "${REGISTRY_URL}/${IMAGE}:${VERSION}.${BITBUCKET_BUILD_NUMBER}-dev"
docker push "${REGISTRY_URL}/${IMAGE}:${VERSION}.${BITBUCKET_BUILD_NUMBER}-dev"
