#!/bin/bash
set -euo pipefail

# This script is meant to be run after pushing a new tag to GitHub. It updates the Homebrew formula with the new version and the SHA of the tarball for the new tag.
TAG=$(git describe --tags --abbrev=0)

# compute the SHA of the tarball for the current tag, which is needed for the Homebrew formula
TARBALL_URL="https://github.com/dfla-me/scrop/archive/refs/tags/$TAG.tar.gz"

# compute the SHA of the tarball for the current tag, which is needed for the Homebrew formula
SHA=$(curl -fsSL "$TARBALL_URL" | shasum -a 256 | awk '{print $1}')

# check that the SHA is not empty or the SHA of an empty file (which would indicate that the tarball download failed)
if [ -z "$SHA" ] || [ "$SHA" = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" ]; then
  echo "ERROR: empty tarball downloaded — is the tag pushed?" >&2
  exit 1
fi

# copy the formula to the homebrew tap... we assume the tap is checked out at ../homebrew-scrop
cp ./packaging/scrop.rb ../homebrew-scrop/Formula/scrop.rb

# put the SHA in the formula
sed -i '' "s/REPLACE_WITH_SHA256_OF_TAGGED_TARBALL/$SHA/g" ../homebrew-scrop/Formula/scrop.rb

# put the current tag in the formula
sed -i '' "s/REPLACE_WITH_TAG/$TAG/g" ../homebrew-scrop/Formula/scrop.rb

# REMEMBER!!!
echo "REMEMBER TO COMMIT AND PUSH THE CHANGES TO ../homebrew-scrop/Formula/scrop.rb"
