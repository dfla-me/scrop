# scrop

Crop sub-images (photos, sticky notes, receipts) out of a larger scanned
composite image. Built on OpenCV.

## Install (macOS, Homebrew)

```sh
brew tap dfla-me/scrop
brew install scrop
```

Homebrew handles Python, OpenCV, and NumPy — you don't need to install any of
them manually. `scrop` lands on your `PATH`.

## Uninstall

```sh
brew uninstall scrop
brew untap dfla-me/scrop
```

## Usage

```sh
scrop INPUT_IMAGE [OUTPUT_DIR] [--min-area N] [--threshold T] [--format jpg|png]
```

- `INPUT_IMAGE` — composite image to scan (jpg, png, webp, tiff, …)
- `OUTPUT_DIR` — where to write the crops (default: current directory)
- `--min-area` — minimum contour area in px² to keep (default: 10000)
- `--threshold` — 0–255 binary threshold separating sub-images from the
  background. Lower if your background is darker than pure white.
  (default: 200)
- `--format` — `jpg` or `png` (default: `jpg`)

Example:

```sh
scrop ~/Desktop/scan.jpg ~/Desktop/crops --min-area 20000 --threshold 220
```

Crops are written as `<input>_<index>.<ext>`.

## Publishing a new release

This repo is the source. Distribution goes through a separate
[Homebrew tap repo](https://github.com/dfla-me/homebrew-scrop).

1. Bump `version` in [pyproject.toml](pyproject.toml).
2. Commit, tag, and push:
   ```sh
   git tag v0.2.6
   git push origin main --tags
   ```
3. Use the `publish.sh` script to:
3a. Grab the tarball SHA:
   ```sh
   curl -sL https://github.com/dfla-me/scrop/archive/refs/tags/v0.2.6.tar.gz | shasum -a 256
   ```
3b. In the `homebrew-scrop` tap repo, update `Formula/scrop.rb` with the new
   `url` (tag) and `sha256`. Push.

### Bumping Python wheel resources

The formula declares `numpy` and `opencv-python-headless` as per-platform
wheel resources (macOS arm64/x86_64, Linux x86_64/aarch64). To refresh
them when you want a newer version:

```sh
# replace <pkg> and <version>
curl -s https://pypi.org/pypi/<pkg>/<version>/json | jq -r '
  .urls[] | select(.filename | endswith(".whl")) |
  "\(.filename)\n  url: \(.url)\n  sha256: \(.digests.sha256)\n"'
```

Pick the wheels matching `cp314-cp314-macosx_*_arm64`,
`cp314-cp314-macosx_*_x86_64`, `cp314-cp314-manylinux_2_28_x86_64`,
`cp314-cp314-manylinux_2_28_aarch64` (or the `cp37-abi3` equivalents for
opencv-python-headless) and paste into the formula. The comment block
at the top of `packaging/scrop.rb` has the same pointer.

## Setting up the tap repo (one-time — DONE!)

1. Create a new public GitHub repo named exactly **`homebrew-scrop`** under
   the `dfla-me` account.
2. Inside it, create `Formula/scrop.rb` and paste the contents of
   [packaging/scrop.rb](packaging/scrop.rb), filling in the real `sha256`.
3. Push. Users can now `brew tap dfla-me/scrop`.

## Development

Requires Python 3.10 or newer. This project pins a dev Python via
[pyenv](https://github.com/pyenv/pyenv) (see `.python-version`).

```sh
# one-time: install the pinned interpreter
pyenv install   # reads .python-version

# if you previously had opencv-python installed, remove it first — it
# conflicts with opencv-python-headless (both provide cv2)
pip uninstall -y opencv-python || true

# install scrop and its deps into the current environment in editable mode
pip install -e .

# run it
scrop tests/sample.jpg /tmp/out
```

The dev Python version is independent of the Homebrew formula's
`python@3.14` — they don't need to match.

### Why `opencv-python-headless`?

scrop only needs cv2's image I/O and geometry primitives, not GUI windows,
video codecs, or HighGUI. The `-headless` wheel is a ~80 MB self-contained
binary that gives us the same `import cv2` API without dragging in Qt,
ffmpeg, VTK, or the rest of the Homebrew `opencv` dependency tree
(~2 GB). It's also much faster to import on first launch.
