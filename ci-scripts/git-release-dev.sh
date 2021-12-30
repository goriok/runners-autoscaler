#!/usr/bin/env bash

# Release new git version

set -ex

##
# Step 1: Get version tag
##
tag=$(semversioner current-version)

##
# Step 2: Commit back to the repository
##
echo "Committing updated files to the repository..."
git add .
git commit -m "Update files for new version '${tag}' [skip ci]"
git push origin "${BITBUCKET_BRANCH}"
