from __future__ import annotations

import argparse
import os
import re
import sys
import threading
from typing import List, Optional, Tuple, TYPE_CHECKING

# cv2 and numpy are imported lazily inside main() so that:
#   * `scrop --help` and quick-fail paths (bad args, missing file) stay snappy
#   * the actual cv2 import is wrapped in a visible progress indicator,
#     since the first-time native library load can take several seconds
#     while macOS dyld resolves the OpenCV shared object on a cold cache.
if TYPE_CHECKING:
    import cv2  # noqa: F401
    import numpy as np  # noqa: F401
else:
    cv2 = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]

OPENCV_FORMAT_EXTENSIONS = {
    "JPEG": [".jpg", ".jpeg"],
    "WEBP": [".webp"],
    "AVIF": [".avif"],
    "PNG": [".png"],
    "TIFF": [".tif", ".tiff"],
    "JPEG 2000": [".jp2", ".j2k"],
    "OPENEXR": [".exr"],
    "GIF": [".gif"],
    "HDR": [".hdr"],
    "SUNRASTER": [".ras"],
    "PXM": [".pbm", ".pgm", ".ppm", ".pnm"],
    "PFM": [".pfm"],
}

OUTPUT_EXTENSIONS = {
    "jpg": ".jpg",
    "jpeg": ".jpg",
    "png": ".png",
}


def _load_opencv() -> None:
    """Import cv2 and numpy lazily with a visible progress indicator.

    cv2's first import on a cold filesystem cache can take several seconds.
    We print a single line on stderr and append dots every 0.5s from a
    background thread so the user knows the CLI hasn't hung.
    """
    global cv2, np
    if cv2 is not None:
        return

    loaded = threading.Event()

    def _spinner() -> None:
        sys.stderr.write("scrop: loading OpenCV")
        sys.stderr.flush()
        while not loaded.wait(timeout=0.5):
            sys.stderr.write(".")
            sys.stderr.flush()
        sys.stderr.write(" done.\n")
        sys.stderr.flush()

    spinner = threading.Thread(target=_spinner, daemon=True)
    spinner.start()
    try:
        import cv2 as _cv2  # noqa: WPS433
        import numpy as _np  # noqa: WPS433
    finally:
        loaded.set()
        spinner.join(timeout=2.0)

    cv2 = _cv2
    np = _np


def parse_opencv_supported_file_types(build_info: str) -> Tuple[str, List[str]]:
    """Parse OpenCV build information and return supported file type names and extensions."""
    supported_formats = []
    supported_extensions = []
    pattern = re.compile(r"^\s*([A-Za-z0-9 ]+):\s*(.+)$")

    for line in build_info.splitlines():
        match = pattern.match(line)
        if not match:
            continue

        format_name = match.group(1).strip()
        format_value = match.group(2).strip().upper()
        normalized_name = format_name.upper()

        if normalized_name not in OPENCV_FORMAT_EXTENSIONS:
            continue

        if "YES" in format_value or "BUILD" in format_value or "AVIF" in normalized_name:
            supported_formats.append(format_name)
            supported_extensions.extend(OPENCV_FORMAT_EXTENSIONS[normalized_name])

    unique_formats = sorted(dict.fromkeys(supported_formats), key=str.lower)
    unique_extensions = sorted(dict.fromkeys(supported_extensions), key=str.lower)
    return ", ".join(unique_formats), unique_extensions


def is_extension_supported(filename: str, supported_extensions: List[str]) -> bool:
    """Return True if the filename extension is supported by OpenCV based on build info."""
    _, ext = os.path.splitext(filename)
    return ext.lower() in supported_extensions


def deskew_image(image: np.ndarray) -> np.ndarray:
    """Rotate the image so that the receipt content is aligned vertically."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = cv2.findNonZero(thresh)
    if coords is None or len(coords) < 10:
        return image

    rect = cv2.minAreaRect(coords)
    angle = rect[-1]
    if angle < -45:
        angle += 90

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos = abs(M[0, 0])
    sin = abs(M[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]

    return cv2.warpAffine(image, M, (new_w, new_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def crop_rotated_rect(image: np.ndarray, contour: np.ndarray) -> Optional[np.ndarray]:
    rect = cv2.minAreaRect(contour)
    width, height = rect[1]
    if width <= 0 or height <= 0:
        return None

    box = cv2.boxPoints(rect).astype("float32")
    rect_pts = order_points(box)

    (tl, tr, br, bl) = rect_pts
    max_width = int(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl)))
    max_height = int(max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr)))
    if max_width == 0 or max_height == 0:
        return None

    dst = np.array([
        [0.0, 0.0],
        [max_width - 1.0, 0.0],
        [max_width - 1.0, max_height - 1.0],
        [0.0, max_height - 1.0],
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect_pts, dst)
    warped = cv2.warpPerspective(image, M, (max_width, max_height), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return warped


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scrop",
        description="Crop sub-images (photos, sticky notes, receipts) out of a larger scanned composite image.",
    )
    parser.add_argument("input_image", help="Path to the composite input image.")
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=".",
        help="Directory to save cropped images (default: current directory).",
    )
    parser.add_argument(
        "--min-area",
        type=int,
        default=10000,
        help="Minimum contour area in pixels squared to keep as a sub-image (default: 10000).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=200,
        help="Binary threshold 0-255 used to separate sub-images from background (default: 200).",
    )
    parser.add_argument(
        "--format",
        choices=sorted(set(OUTPUT_EXTENSIONS)),
        default="jpg",
        help="Output image format (default: jpg).",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not 0 <= args.threshold <= 255:
        print(f"scrop: --threshold must be between 0 and 255 (got {args.threshold})", file=sys.stderr)
        return 2
    if args.min_area <= 0:
        print(f"scrop: --min-area must be positive (got {args.min_area})", file=sys.stderr)
        return 2

    if not os.path.isfile(args.input_image):
        print(f"scrop: input image not found: {args.input_image}", file=sys.stderr)
        return 1

    # Heavy imports happen here so quick-fail paths above stay instant.
    _load_opencv()

    build_info = cv2.getBuildInformation()
    supported_types, supported_extensions = parse_opencv_supported_file_types(build_info)
    if not is_extension_supported(args.input_image, supported_extensions):
        print(
            f"scrop: unsupported input extension. This OpenCV build can read: {supported_types}",
            file=sys.stderr,
        )
        return 1

    image = cv2.imread(args.input_image)
    if image is None:
        print(
            f"scrop: unable to decode image (file may be corrupt or empty): {args.input_image}",
            file=sys.stderr,
        )
        return 1

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, args.threshold, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    input_filename = os.path.splitext(os.path.basename(args.input_image))[0]
    os.makedirs(args.output_dir, exist_ok=True)
    out_ext = OUTPUT_EXTENSIONS[args.format]

    saved = 0
    for contour in contours:
        if cv2.contourArea(contour) < args.min_area:
            continue
        cropped = crop_rotated_rect(image, contour)
        if cropped is None:
            continue
        out_path = os.path.join(args.output_dir, f"{input_filename}_{saved}{out_ext}")
        if not cv2.imwrite(out_path, cropped):
            print(f"scrop: failed to write {out_path}", file=sys.stderr)
            continue
        saved += 1

    print(f"scrop: saved {saved} crop(s) to {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
