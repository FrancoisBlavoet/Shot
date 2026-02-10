# Per-pixel color tolerance (colorTolerance)

This fork adds **per-pixel color tolerance** to Shot's screenshot comparison, similar to ImageMagick's `-fuzz` option. It reduces flakiness from anti-aliasing and sub-pixel rendering differences across devices/CI.

## How it works

- **`tolerance`** (existing): Percentage of pixels that are *allowed* to differ before the test fails (e.g. `0.1` = 0.1%).
- **`colorTolerance`** (new): Percentage of the color range (0–100). Two pixels are considered **equal** if each ARGB channel differs by at most `(colorTolerance/100 * 255)`. So small rendering differences (e.g. font edges) don't count as "different" pixels.

Example: `colorTolerance = 2.0` → per-channel threshold ≈ 5; pixels within 5 units per channel are treated as equal. With 2% color fuzz, many "visually identical" screenshots that previously failed (e.g. 13% pixel diff with strict comparison) can pass because most of those pixels are within the color threshold.

## Usage

In your `build.gradle` (or `shot.gradle`):

```groovy
shot {
    tolerance = 0.1f
    // Per-pixel color fuzz (0–100). 0 = strict; 2.0 ≈ ImageMagick -fuzz 2%.
    colorTolerance = 2.0
}
```

## Building and publishing this fork

Requires Java 11 or 17 (Gradle 7.6 does not support Java 21).

```bash
# Build and publish to local Maven (~/.m2)
./gradlew publishToMavenLocal
```

### Using the fork from instacart-android

1. Publish the fork: from `shot-android-fork`, run `./gradlew publishToMavenLocal` (use Java 11 or 17).
2. In instacart-android root `build.gradle.kts`, ensure `mavenLocal()` is in `buildscript { repositories { ... } }` (usually already there).
3. In `gradle/libs.versions.toml`, set the Shot version to the fork's version (e.g. `shot = "6.1.0-color"` or the version in the fork's `gradle.properties`).
4. In `gradle/shot.gradle`, add `colorTolerance = 2.0` inside the `shot { }` block.
5. Publish the fork's plugin so the buildscript classpath resolves to it (same group `com.karumi`, artifact `shot`, version from the fork).

## Validation

- **Shell script** (ImageMagick): `scripts/validate_color_tolerance.sh <baseline.png> <actual.png>` — uses `compare -fuzz 2%` and checks that the differing pixel count is under 0.1% of total. The two instacart screenshot images validate as "CONSIDERED EQUAL" with colorTolerance=2.
- **Python script** (optional): `scripts/validate_color_tolerance.py` — replicates the algorithm; requires `pip install Pillow`.
- **Unit tests**: `core/src/test/scala/com/karumi/shot/screenshots/ScreenshotsComparatorTest.scala` — "consider two nearly identical images equal with colorTolerance 2.0 and tolerance 0.1%" uses the same two validation images and asserts no errors; "consider the same two nearly identical images different with colorTolerance 0" asserts they fail without color tolerance. Run with `./gradlew :core:test --tests "com.karumi.shot.screenshots.ScreenshotsComparatorTest"`.

## Files changed

- **core**: `ScreenshotsComparator.scala` – pixel comparison uses ARGB and per-channel threshold when `colorTolerance > 0`; `domain/model.scala` – `Config.defaultColorTolerance`.
- **shot** (plugin): `ShotExtension.scala` – `colorTolerance` property; `ShotPlugin.scala` – (no change, extension uses default); `tasks/Tasks.scala` – passes `colorTolerance` into verification; **Shot.scala** (core) – `verifyScreenshots` takes `colorTolerance` and passes to comparator.
