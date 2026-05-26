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
   git tag v0.1.0
   git push origin main --tags
   ```
3. Use the `publish.sh` script to:
3a. Grab the tarball SHA:
   ```sh
   curl -sL https://github.com/dfla-me/scrop/archive/refs/tags/v0.1.0.tar.gz | shasum -a 256
   ```
3b. In the `homebrew-scrop` tap repo, update `Formula/scrop.rb` with the new
   `url` (tag) and `sha256`. Push.

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

# install scrop and its deps into the current environment in editable mode
pip install -e .

# run it
scrop tests/sample.jpg /tmp/out
```

The dev Python version is independent of the Homebrew formula's
`python@3.13` — they don't need to match.
