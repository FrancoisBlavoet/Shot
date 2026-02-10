#!/usr/bin/env python3
"""
Validates that the Shot color-tolerance algorithm would consider two images
equal when colorTolerance=2 and tolerance=0.1%.

Replicates the logic in ScreenshotsComparator:
- threshold = round(colorTolerance/100 * 255), so 2.0 -> 5
- Two pixels "differ" if any ARGB channel differs by more than threshold
- Images are equal if (different_pixel_count / total) * 100 <= tolerance

Usage:
  python3 scripts/validate_color_tolerance.py <baseline.png> <actual.png> [color_tolerance] [tolerance_percent]
  Defaults: color_tolerance=2.0, tolerance_percent=0.1

Requires: pip install Pillow
"""
import sys

try:
    from PIL import Image
except ImportError:
    Image = None


def channel(argb: int, shift: int) -> int:
    return (argb >> shift) & 0xFF


def pixels_differ(argb1: int, argb2: int, threshold: int) -> bool:
    if threshold <= 0:
        return argb1 != argb2
    return (
        abs(channel(argb1, 24) - channel(argb2, 24)) > threshold
        or abs(channel(argb1, 16) - channel(argb2, 16)) > threshold
        or abs(channel(argb1, 8) - channel(argb2, 8)) > threshold
        or abs(channel(argb1, 0) - channel(argb2, 0)) > threshold
    )


def color_tolerance_threshold(color_tolerance_percent: float) -> int:
    if color_tolerance_percent <= 0:
        return 0
    return min(255, round(color_tolerance_percent / 100.0 * 255))


def compare(
    baseline_path: str,
    actual_path: str,
    color_tolerance: float = 2.0,
    tolerance_percent: float = 0.1,
) -> None:
    baseline = Image.open(baseline_path).convert("RGBA")
    actual = Image.open(actual_path).convert("RGBA")
    if baseline.size != actual.size:
        print(f"FAIL: dimensions differ {baseline.size} vs {actual.size}")
        sys.exit(1)

    threshold = color_tolerance_threshold(color_tolerance)
    pixels_b = list(baseline.getdata())
    pixels_a = list(actual.getdata())
    # PIL RGBA is (r,g,b,a) per pixel; pack to ARGB int to match Shot
    def to_argb(p):
        r, g, b, a = p
        return (a << 24) | (r << 16) | (g << 8) | b

    different = sum(
        1
        for pb, pa in zip(pixels_b, pixels_a)
        if pixels_differ(to_argb(pb), to_argb(pa), threshold)
    )
    total = len(pixels_b)
    percentage = (different / total) * 100.0
    considered_equal = percentage <= tolerance_percent

    print(f"Total pixels: {total}")
    print(f"Different pixels (colorTolerance={color_tolerance}, threshold={threshold}): {different}")
    print(f"Percentage different: {percentage:.4f}%")
    print(f"Tolerance (max %% allowed): {tolerance_percent}%")
    print(
        f"Result: {'CONSIDERED EQUAL' if considered_equal else 'CONSIDERED DIFFERENT'}"
    )
    if considered_equal:
        print("Validation PASSED: algorithm would treat these two images as identical.")
    else:
        print("Validation FAILED: algorithm would report a screenshot mismatch.")
    sys.exit(0 if considered_equal else 1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    if Image is None:
        print("Pillow (PIL) is required. Run: pip install Pillow")
        sys.exit(2)
    baseline_path = sys.argv[1]
    actual_path = sys.argv[2]
    color_tolerance = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
    tolerance_percent = float(sys.argv[4]) if len(sys.argv) > 4 else 0.1
    compare(baseline_path, actual_path, color_tolerance, tolerance_percent)
