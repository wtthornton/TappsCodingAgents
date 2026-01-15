"""
Visual Regression Testing for Playwright.

Compares screenshots to detect visual regressions and UI changes.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Try to import image comparison libraries
try:
    from PIL import Image, ImageChops, ImageStat
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None
    ImageChops = None
    ImageStat = None


@dataclass
class VisualDiff:
    """Visual difference between two screenshots."""

    baseline_path: Path
    current_path: Path
    diff_path: Path | None = None
    similarity_score: float = 0.0  # 0-100, 100 = identical
    pixel_difference: int = 0
    total_pixels: int = 0
    difference_percentage: float = 0.0
    has_regression: bool = False
    threshold: float = 0.0  # Threshold used for comparison


@dataclass
class VisualBaseline:
    """Visual baseline for comparison."""

    name: str
    path: Path
    hash: str
    created_at: str
    metadata: dict[str, Any] | None = None


class VisualRegressionTester:
    """
    Visual regression testing using screenshot comparison.

    Compares current screenshots with baseline screenshots to detect visual changes.
    """

    def __init__(
        self,
        baseline_dir: Path | None = None,
        diff_dir: Path | None = None,
        threshold: float = 0.01,  # 1% difference allowed
    ):
        """
        Initialize visual regression tester.

        Args:
            baseline_dir: Directory for baseline screenshots (default: .tapps-agents/baselines/)
            diff_dir: Directory for diff images (default: .tapps-agents/diffs/)
            threshold: Difference threshold (0.0-1.0, default: 0.01 = 1%)
        """
        if baseline_dir is None:
            baseline_dir = Path(".tapps-agents") / "baselines"
        if diff_dir is None:
            diff_dir = Path(".tapps-agents") / "diffs"

        self.baseline_dir = Path(baseline_dir)
        self.diff_dir = Path(diff_dir)
        self.threshold = threshold

        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.diff_dir.mkdir(parents=True, exist_ok=True)

        if not HAS_PIL:
            logger.warning(
                "PIL/Pillow not installed. Visual regression testing will be limited. "
                "Install with: pip install Pillow"
            )

    def create_baseline(
        self,
        screenshot_path: Path,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> VisualBaseline:
        """
        Create a baseline screenshot.

        Args:
            screenshot_path: Path to screenshot file
            name: Baseline name
            metadata: Optional metadata

        Returns:
            VisualBaseline
        """
        from datetime import datetime

        screenshot_path = Path(screenshot_path)
        if not screenshot_path.exists():
            raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")

        # Calculate hash
        file_hash = self._calculate_hash(screenshot_path)

        # Copy to baseline directory
        baseline_path = self.baseline_dir / f"{name}.png"
        import shutil

        shutil.copy2(screenshot_path, baseline_path)

        baseline = VisualBaseline(
            name=name,
            path=baseline_path,
            hash=file_hash,
            created_at=datetime.now().isoformat(),
            metadata=metadata,
        )

        logger.info(f"Created baseline: {name} ({baseline_path})")
        return baseline

    def compare(
        self,
        current_screenshot: Path,
        baseline_name: str,
        threshold: float | None = None,
    ) -> VisualDiff:
        """
        Compare current screenshot with baseline.

        Args:
            current_screenshot: Path to current screenshot
            baseline_name: Name of baseline to compare against
            threshold: Optional threshold override

        Returns:
            VisualDiff with comparison results
        """
        if not HAS_PIL:
            logger.error("PIL/Pillow required for visual comparison")
            return VisualDiff(
                baseline_path=Path(),
                current_path=Path(current_screenshot),
                has_regression=True,
            )

        threshold = threshold or self.threshold
        current_path = Path(current_screenshot)
        baseline_path = self.baseline_dir / f"{baseline_name}.png"

        if not baseline_path.exists():
            logger.warning(f"Baseline not found: {baseline_path}")
            return VisualDiff(
                baseline_path=baseline_path,
                current_path=current_path,
                has_regression=True,
                threshold=threshold,
            )

        if not current_path.exists():
            logger.error(f"Current screenshot not found: {current_path}")
            return VisualDiff(
                baseline_path=baseline_path,
                current_path=current_path,
                has_regression=True,
                threshold=threshold,
            )

        try:
            # Load images
            baseline_img = Image.open(baseline_path)
            current_img = Image.open(current_path)

            # Ensure same size
            if baseline_img.size != current_img.size:
                logger.warning(
                    f"Image sizes differ: baseline {baseline_img.size} vs current {current_img.size}"
                )
                # Resize current to match baseline
                current_img = current_img.resize(baseline_img.size, Image.Resampling.LANCZOS)

            # Convert to RGB if needed
            if baseline_img.mode != "RGB":
                baseline_img = baseline_img.convert("RGB")
            if current_img.mode != "RGB":
                current_img = current_img.convert("RGB")

            # Calculate difference
            diff_img = ImageChops.difference(baseline_img, current_img)
            stat = ImageStat.Stat(diff_img)

            # Calculate metrics
            total_pixels = baseline_img.size[0] * baseline_img.size[1]
            pixel_difference = sum(stat.sum) / 3  # Average of RGB channels
            difference_percentage = (pixel_difference / (total_pixels * 255)) * 100
            similarity_score = 100.0 - difference_percentage

            # Determine if regression
            has_regression = difference_percentage > (threshold * 100)

            # Save diff image if regression found
            diff_path = None
            if has_regression:
                diff_filename = f"{baseline_name}_diff_{Path(current_path).stem}.png"
                diff_path = self.diff_dir / diff_filename
                diff_img.save(diff_path)
                logger.info(f"Visual regression detected. Diff saved: {diff_path}")

            return VisualDiff(
                baseline_path=baseline_path,
                current_path=current_path,
                diff_path=diff_path,
                similarity_score=similarity_score,
                pixel_difference=int(pixel_difference),
                total_pixels=total_pixels,
                difference_percentage=difference_percentage,
                has_regression=has_regression,
                threshold=threshold,
            )

        except Exception as e:
            logger.error(f"Visual comparison failed: {e}")
            return VisualDiff(
                baseline_path=baseline_path,
                current_path=current_path,
                has_regression=True,
                threshold=threshold,
            )

    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def list_baselines(self) -> list[VisualBaseline]:
        """
        List all baseline screenshots.

        Returns:
            List of VisualBaseline objects
        """
        baselines = []
        for baseline_file in self.baseline_dir.glob("*.png"):
            try:
                baseline = VisualBaseline(
                    name=baseline_file.stem,
                    path=baseline_file,
                    hash=self._calculate_hash(baseline_file),
                    created_at="",  # Would need to store this separately
                )
                baselines.append(baseline)
            except Exception as e:
                logger.warning(f"Failed to process baseline {baseline_file}: {e}")

        return baselines

    def update_baseline(
        self,
        screenshot_path: Path,
        baseline_name: str,
        metadata: dict[str, Any] | None = None,
    ) -> VisualBaseline:
        """
        Update an existing baseline.

        Args:
            screenshot_path: Path to new screenshot
            baseline_name: Name of baseline to update
            metadata: Optional metadata

        Returns:
            Updated VisualBaseline
        """
        return self.create_baseline(screenshot_path, baseline_name, metadata)
