#!/bin/bash
set -euo pipefail

TARBALL_URL="https://github.com/dfla-me/scrop/archive/refs/tags/v0.1.0.tar.gz"

SHA=$(curl -fsSL "$TARBALL_URL" | shasum -a 256 | awk '{print $1}')

if [ -z "$SHA" ] || [ "$SHA" = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" ]; then
  echo "ERROR: empty tarball downloaded — is the tag pushed?" >&2
  exit 1
fi

cp ./packaging/scrop.rb ../homebrew-scrop/Formula/scrop.rb
sed -i '' "s/REPLACE_WITH_SHA256_OF_TAGGED_TARBALL/$SHA/g" ../homebrew-scrop/Formula/scrop.rb

echo "REMEMBER TO COMMIT AND PUSH THE CHANGES TO ../homebrew-scrop/Formula/scrop.rb"
