#!/usr/bin/env bash

set -ex
IMAGE=$1


##
# Step 1: Generate new version
##
previous_version=$(semversioner current-version)
semversioner release
new_version=$(semversioner current-version)


##
# Step 2: Generate CHANGELOG.md
##
echo "Generating CHANGELOG.md file..."
semversioner changelog > CHANGELOG.md


##
# Step 4: Commit back to the repository
##
echo "Committing updated files to the repository..."
git add .
git commit -m "Update files for new version '${new_version}' [skip ci]"
git push origin ${BITBUCKET_BRANCH}


##
# Step 5: Tag the repository
##
echo "Tagging for release ${new_version}" "${new_version}"
git tag -a -m "Tagging for release ${new_version}" "${new_version}"
git push origin ${new_version}
