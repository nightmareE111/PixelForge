
"""
PixelForge 2.0
Professional Image-to-Pixel-Art Processing Engine

Requirements:
    pip install Pillow
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from PIL import Image, ImageEnhance, ImageOps, ImageDraw


# ============================================================
# Exceptions
# ============================================================

class PixelForgeError(Exception):
    """Base exception for PixelForge."""


class ConversionCancelled(PixelForgeError):
    """Raised when the conversion is cancelled."""


# ============================================================
# Validation
# ============================================================

def _validate_int(name: str, value: int, minimum: int, maximum: int):
    if not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(
            f"{name} must be between {minimum} and {maximum}."
        )


def _validate_float(name: str, value: float, minimum: float, maximum: float):
    if not minimum <= value <= maximum:
        raise ValueError(
            f"{name} must be between {minimum} and {maximum}."
        )


def _report(progress_callback, value: int, message: str):
    if progress_callback:
        progress_callback(value, message)


def _check_cancel(cancel_callback):
    if cancel_callback and cancel_callback():
        raise ConversionCancelled("Conversion cancelled by user.")


# ============================================================
# Image Loading
# ============================================================

def load_image(
    input_path: str | Path,
    max_side: int = 12000
) -> Image.Image:

    path = Path(input_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    _validate_int("max_side", max_side, 100, 30000)

    try:
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source)
            image.load()

            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA")

            if max(image.size) > max_side:
                image.thumbnail(
                    (max_side, max_side),
                    Image.Resampling.LANCZOS
                )

            return image.copy()

    except Exception as error:
        raise PixelForgeError(
            f"Could not load image: {error}"
        ) from error


# ============================================================
# Image Enhancement
# ============================================================

def enhance_image(
    image: Image.Image,
    brightness: float = 1.0,
    contrast: float = 1.08,
    saturation: float = 1.08,
    sharpness: float = 1.15
) -> Image.Image:

    _validate_float("brightness", brightness, 0.1, 3.0)
    _validate_float("contrast", contrast, 0.1, 3.0)
    _validate_float("saturation", saturation, 0.0, 3.0)
    _validate_float("sharpness", sharpness, 0.0, 3.0)

    has_alpha = image.mode == "RGBA"

    if has_alpha:
        alpha = image.getchannel("A")
        image = image.convert("RGB")
    else:
        alpha = None
        image = image.convert("RGB")

    image = ImageEnhance.Brightness(image).enhance(brightness)
    image = ImageEnhance.Contrast(image).enhance(contrast)
    image = ImageEnhance.Color(image).enhance(saturation)
    image = ImageEnhance.Sharpness(image).enhance(sharpness)

    if alpha is not None:
        image.putalpha(alpha)

    return image


# ============================================================
# Pixel Grid Generation
# ============================================================

def make_pixel_grid(
    image: Image.Image,
    columns: int = 160,
    sampling: str = "lanczos"
) -> Image.Image:

    _validate_int("columns", columns, 8, 2048)

    filters = {
        "box": Image.Resampling.BOX,
        "bilinear": Image.Resampling.BILINEAR,
        "bicubic": Image.Resampling.BICUBIC,
        "lanczos": Image.Resampling.LANCZOS,
        "nearest": Image.Resampling.NEAREST,
    }

    if sampling.lower() not in filters:
        raise ValueError(
            f"Unsupported sampling filter: {sampling}"
        )

    width, height = image.size

    if width <= 0 or height <= 0:
        raise PixelForgeError("Invalid image dimensions.")

    rows = max(1, round(height * columns / width))

    if image.mode == "RGBA":
        alpha = image.getchannel("A")
        rgb = image.convert("RGB")

        small_rgb = rgb.resize(
            (columns, rows),
            filters[sampling.lower()]
        )

        small_alpha = alpha.resize(
            (columns, rows),
            Image.Resampling.BOX
        )

        small_rgb.putalpha(small_alpha)
        return small_rgb

    return image.resize(
        (columns, rows),
        filters[sampling.lower()]
    )


# ============================================================
# Color Reduction
# ============================================================

def reduce_palette(
    image: Image.Image,
    colors: int = 64,
    dither: str = "none"
) -> Image.Image:

    _validate_int("colors", colors, 2, 256)

    dither_modes = {
        "none": Image.Dither.NONE,
        "floyd": Image.Dither.FLOYDSTEINBERG,
    }

    dither = dither.lower()

    if dither not in dither_modes:
        raise ValueError(
            "Dither must be 'none' or 'floyd'."
        )

    has_alpha = image.mode == "RGBA"

    if has_alpha:
        alpha = image.getchannel("A")
        rgb = image.convert("RGB")
    else:
        alpha = None
        rgb = image.convert("RGB")

    quantized = rgb.quantize(
        colors=colors,
        method=Image.Quantize.MEDIANCUT,
        dither=dither_modes[dither]
    ).convert("RGB")

    if alpha is not None:
        quantized.putalpha(alpha)

    return quantized


# ============================================================
# Pixel Enlargement
# ============================================================

def enlarge_pixels(
    image: Image.Image,
    pixel_size: int = 4
) -> Image.Image:

    _validate_int("pixel_size", pixel_size, 1, 64)

    width, height = image.size

    return image.resize(
        (width * pixel_size, height * pixel_size),
        Image.Resampling.NEAREST
    )


# ============================================================
# Pixel Grid Overlay
# ============================================================

def add_pixel_grid(
    image: Image.Image,
    pixel_size: int,
    grid_opacity: int = 0
) -> Image.Image:

    _validate_int("pixel_size", pixel_size, 1, 64)
    _validate_int("grid_opacity", grid_opacity, 0, 120)

    if grid_opacity == 0 or pixel_size <= 1:
        return image

    has_alpha = image.mode == "RGBA"
    base = image.convert("RGBA")

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    grid_color = (0, 0, 0, grid_opacity)

    width, height = base.size

    for x in range(0, width, pixel_size):
        draw.line(
            [(x, 0), (x, height)],
            fill=grid_color
        )

    for y in range(0, height, pixel_size):
        draw.line(
            [(0, y), (width, y)],
            fill=grid_color
        )

    result = Image.alpha_composite(base, overlay)

    return result if has_alpha else result.convert("RGB")


# ============================================================
# Main Conversion Function
# ============================================================

def convert(
    input_path: str | Path,
    output_path: str | Path,
    *,
    columns: int = 160,
    pixel_size: int = 4,
    colors: int = 64,
    dither: str = "none",
    sampling: str = "lanczos",
    brightness: float = 1.0,
    contrast: float = 1.08,
    saturation: float = 1.08,
    sharpness: float = 1.15,
    grid_opacity: int = 0,
    max_side: int = 12000,
    progress_callback: Optional[Callable] = None,
    cancel_callback: Optional[Callable] = None
) -> tuple[int, int]:

    """
    Convert an image into pixel art.

    progress_callback:
        Function receiving (percentage, message).

    cancel_callback:
        Function returning True when conversion should stop.

    Returns:
        (output_width, output_height)
    """

    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(input_path)

    if input_path.resolve() == output_path.resolve():
        raise ValueError(
            "Input and output paths cannot be the same."
        )

    _validate_int("columns", columns, 8, 2048)
    _validate_int("pixel_size", pixel_size, 1, 64)
    _validate_int("colors", colors, 2, 256)
    _validate_int("grid_opacity", grid_opacity, 0, 120)

    _check_cancel(cancel_callback)
    _report(progress_callback, 5, "Loading image...")

    image = load_image(input_path, max_side)

    _check_cancel(cancel_callback)
    _report(progress_callback, 20, "Enhancing image...")

    image = enhance_image(
        image,
        brightness=brightness,
        contrast=contrast,
        saturation=saturation,
        sharpness=sharpness
    )

    _check_cancel(cancel_callback)
    _report(progress_callback, 40, "Creating pixel grid...")

    image = make_pixel_grid(
        image,
        columns=columns,
        sampling=sampling
    )

    _check_cancel(cancel_callback)
    _report(progress_callback, 60, "Reducing color palette...")

    image = reduce_palette(
        image,
        colors=colors,
        dither=dither
    )

    _check_cancel(cancel_callback)
    _report(progress_callback, 75, "Enlarging pixels...")

    image = enlarge_pixels(
        image,
        pixel_size=pixel_size
    )

    _check_cancel(cancel_callback)
    _report(progress_callback, 88, "Applying pixel grid...")

    image = add_pixel_grid(
        image,
        pixel_size=pixel_size,
        grid_opacity=grid_opacity
    )

    _check_cancel(cancel_callback)
    _report(progress_callback, 95, "Saving image...")

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    extension = output_path.suffix.lower()

    try:
        if extension in (".jpg", ".jpeg"):
            if image.mode == "RGBA":
                background = Image.new(
                    "RGB",
                    image.size,
                    (255, 255, 255)
                )
                background.paste(
                    image,
                    mask=image.getchannel("A")
                )
                image = background

            image.save(
                output_path,
                format="JPEG",
                quality=95,
                subsampling=0,
                optimize=True
            )

        elif extension == ".png":
            image.save(
                output_path,
                format="PNG",
                optimize=True
            )

        else:
            raise ValueError(
                "Output format must be PNG or JPEG."
            )

    except Exception as error:
        raise PixelForgeError(
            f"Could not save output image: {error}"
        ) from error

    _report(progress_callback, 100, "Conversion complete!")

    return image.size


# ============================================================
# Command Line Interface
# ============================================================

def main():

    import argparse

    parser = argparse.ArgumentParser(
        description="PixelForge 2.0 - Image to Pixel Art Converter"
    )

    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", help="Output image path")

    parser.add_argument("--columns", type=int, default=160)
    parser.add_argument("--pixel-size", type=int, default=4)
    parser.add_argument("--colors", type=int, default=64)

    parser.add_argument(
        "--dither",
        choices=["none", "floyd"],
        default="none"
    )

    parser.add_argument(
        "--sampling",
        choices=["box", "bilinear", "bicubic", "lanczos", "nearest"],
        default="lanczos"
    )

    parser.add_argument("--brightness", type=float, default=1.0)
    parser.add_argument("--contrast", type=float, default=1.08)
    parser.add_argument("--saturation", type=float, default=1.08)
    parser.add_argument("--sharpness", type=float, default=1.15)
    parser.add_argument("--grid", type=int, default=0)

    args = parser.parse_args()

    try:
        dimensions = convert(
            args.input,
            args.output,
            columns=args.columns,
            pixel_size=args.pixel_size,
            colors=args.colors,
            dither=args.dither,
            sampling=args.sampling,
            brightness=args.brightness,
            contrast=args.contrast,
            saturation=args.saturation,
            sharpness=args.sharpness,
            grid_opacity=args.grid
        )

        print("Conversion successful!")
        print(f"Output dimensions: {dimensions[0]} x {dimensions[1]}")
        print(f"Saved to: {args.output}")

    except Exception as error:
        print(f"Error: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()