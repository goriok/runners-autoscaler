#!/usr/bin/env bash
#
# Release to dockerhub.
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
docker tag "${IMAGE}" "${IMAGE}:${VERSION}"
docker push "${IMAGE}"

sed -i "s/bitbucketpipelines\/runners-autoscaler:.*/bitbucketpipelines\/runners-autoscaler:$VERSION/g" config/runners-autoscaler-job.template.yaml
