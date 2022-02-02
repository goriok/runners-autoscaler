#!/usr/bin/env bash

# Bump versions using semversioner

set -ex

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
# Step 3: Use new version in the README.md examples and CLI version
##
echo "Replace version '$previous_version' to '$new_version' in README.md ..."
sed -i "s/:$previous_version/:$new_version/g" README.md

echo "Replace version '$previous_version' to '$new_version' in autoscaler/__version__.py ..."
echo "__version__ = '$new_version'" > autoscaler/__version__.py