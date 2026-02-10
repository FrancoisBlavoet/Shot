#!/usr/bin/env bash
# Validates that two images would be considered equal by Shot with colorTolerance=2 and tolerance=0.1%.
# Uses ImageMagick compare with -fuzz 2% (equivalent to colorTolerance=2) and checks that
# the number of differing pixels is less than 0.1% of total.
set -e
BASELINE="${1:?usage: $0 <baseline.png> <actual.png>}"
ACTUAL="${2:?usage: $0 <baseline.png> <actual.png>}"
TOTAL_PIXELS=$(identify -format "%w*%h" "$BASELINE" | bc)
MAX_DIFF_PIXELS=$(echo "scale=0; $TOTAL_PIXELS * 0.001 / 1" | bc)  # 0.1% of total
# ImageMagick compare returns "COUNT (normalized)" and exit 1 when images differ
DIFF_OUTPUT=$(compare -metric AE -fuzz 2% "$BASELINE" "$ACTUAL" null: 2>&1) || true
DIFF_COUNT=$(echo "$DIFF_OUTPUT" | sed -n 's/^\([0-9]*\).*/\1/p')
if [ -z "$DIFF_COUNT" ]; then DIFF_COUNT=999999; fi
if [ "$DIFF_COUNT" -le "$MAX_DIFF_PIXELS" ]; then
  echo "Total pixels: $TOTAL_PIXELS"
  echo "Different pixels (with 2% fuzz): $DIFF_COUNT"
  echo "Max allowed (0.1%): $MAX_DIFF_PIXELS"
  echo "Result: CONSIDERED EQUAL - validation PASSED"
  exit 0
else
  echo "Different pixels: $DIFF_COUNT > $MAX_DIFF_PIXELS (0.1%)"
  echo "Result: CONSIDERED DIFFERENT - validation FAILED"
  exit 1
fi
