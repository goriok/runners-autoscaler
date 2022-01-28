#!/usr/bin/env bash
#
# Release dev version to dockerhub.
#
# Required globals:
#   DOCKERHUB_USERNAME
#   DOCKERHUB_PASSWORD

set -ex

validate() {
  # mandatory parameters
  : DOCKERHUB_USERNAME="${$DOCKERHUB_USERNAME:?'DOCKERHUB_USERNAME variable missing.'}"
  : DOCKERHUB_PASSWORD="${DOCKERHUB_PASSWORD:?'DOCKERHUB_PASSWORD variable missing.'}"
}

IMAGE=$1
VERSION=$(semversioner current-version)

echo "${DOCKERHUB_PASSWORD}" | docker login --username "$DOCKERHUB_USERNAME" --password-stdin
docker build -t "${IMAGE}" .
docker tag "${IMAGE}" "${IMAGE}:${VERSION}.${BITBUCKET_BUILD_NUMBER}-dev"
docker push "${IMAGE}:${VERSION}.${BITBUCKET_BUILD_NUMBER}-dev"

sed -i "s/bitbucketpipelines\/runners-autoscaler:.*/bitbucketpipelines\/runners-autoscaler:$VERSION\.$BITBUCKET_BUILD_NUMBER-dev/g" controller-spec.yml.template