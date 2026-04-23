# Re-export for scripts that expect `import pca9685` on the device root
# (deploy copies all of `src/` to the filesystem; drivers live in `drivers/`).
from drivers.pca9685 import PCA9685  # noqa: F401

__all__ = ("PCA9685",)
