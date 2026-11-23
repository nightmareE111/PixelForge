import argparse
import sys
from pathlib import Path
from typing import Optional

from PIL import Image, ImageEnhance, ImageOps


def positive_int(value: str) -> int:
        """Parse a positive integer for command-line options."""
        try:
                parsed = int(value)
        except ValueError as error:
                raise argparse.ArgumentTypeError("must be an integer") from error
        if parsed <= 0:
                raise argparse.ArgumentTypeError("must be greater than zero")
        return parsed


def bounded_float(minimum: float, maximum: float):
        """Build a command-line parser for a float within the given bounds."""
        def parse(value: str) -> float:
                try:
                        parsed = float(value)
                except ValueError as error:
                        raise argparse.ArgumentTypeError("must be a number") from error
                if not minimum <= parsed <= maximum:
                        raise argparse.ArgumentTypeError(
                                f"must be between {minimum} and {maximum}"
                        )
                return parsed

        return parse


def load_image(input_path: Path, max_side: int) -> Image.Image:
        """Open an image, normalize its orientation and enforce the size limit."""
        with Image.open(input_path) as opened:
                image = ImageOps.exif_transpose(opened).convert("RGB")
        if max(image.size) > max_side:
                raise ValueError(f"source image exceeds the maximum side length of {max_side}")
        return image


def enhance_image(
        image: Image.Image,
        brightness: float,
        contrast: float,
        saturation: float,
        sharpness: float,
) -> Image.Image:
        """Apply the requested image enhancements before pixelation."""
        image = ImageEnhance.Brightness(image).enhance(brightness)
        image = ImageEnhance.Contrast(image).enhance(contrast)
        image = ImageEnhance.Color(image).enhance(saturation)
        return ImageEnhance.Sharpness(image).enhance(sharpness)


def make_pixel_grid(image: Image.Image, columns: int, sampling: str) -> Image.Image:
        """Shrink the image to the logical pixel grid while preserving aspect ratio."""
        if columns <= 0:
                raise ValueError("columns must be greater than zero")
        rows = max(1, round(image.height * columns / image.width))
        filters = {
                "box": Image.Resampling.BOX,
                "bilinear": Image.Resampling.BILINEAR,
                "bicubic": Image.Resampling.BICUBIC,
                "lanczos": Image.Resampling.LANCZOS,
        }
        if sampling not in filters:
                raise ValueError("sampling must be box, bilinear, bicubic, or lanczos")
        return image.resize((columns, rows), filters[sampling])


def reduce_palette(image: Image.Image, colors: int, dither: str) -> Image.Image:
        """Reduce the image to a limited adaptive palette."""
        if not 2 <= colors <= 256:
                raise ValueError("colors must be between 2 and 256")
        dither_modes = {
                "none": Image.Dither.NONE,
                "floyd": Image.Dither.FLOYDSTEINBERG,
        }
        if dither not in dither_modes:
                raise ValueError("dither must be none or floyd")
        quantized = image.quantize(colors=colors, method=Image.Quantize.MEDIANCUT,
                                                           dither=dither_modes[dither])
        return quantized.convert("RGB")


def enlarge_pixels(image: Image.Image, pixel_size: int) -> Image.Image:
        """Enlarge logical pixels without smoothing their edges."""
        if pixel_size <= 0:
                raise ValueError("pixel_size must be greater than zero")
        return image.resize(
                (image.width * pixel_size, image.height * pixel_size),
                Image.Resampling.NEAREST,
        )


def add_pixel_grid(image: Image.Image, pixel_size: int, grid_opacity: int) -> Image.Image:
        """Overlay subtle grid lines between enlarged logical pixels."""
        if not 0 <= grid_opacity <= 120:
                raise ValueError("grid_opacity must be between 0 and 120")
        if grid_opacity == 0:
                return image
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        pixels = overlay.load()
        for x in range(pixel_size, image.width, pixel_size):
                for y in range(image.height):
                        pixels[x, y] = (0, 0, 0, grid_opacity)
        for y in range(pixel_size, image.height, pixel_size):
                for x in range(image.width):
                        pixels[x, y] = (0, 0, 0, grid_opacity)
        return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def convert(
        input_path: Path,
        output_path: Path,
        *,
        columns: int = 320,
        pixel_size: int = 6,
        colors: int = 64,
        dither: str = "none",
        sampling: str = "lanczos",
        brightness: float = 1.0,
        contrast: float = 1.08,
        saturation: float = 1.08,
        sharpness: float = 1.15,
        grid_opacity: int = 0,
        max_side: int = 12000,
) -> tuple[int, int]:
        """Convert an image to pixel art and return the output dimensions."""
        if not 2 <= colors <= 256:
                raise ValueError("colors must be between 2 and 256")
        if not 0 <= grid_opacity <= 120:
                raise ValueError("grid_opacity must be between 0 and 120")

        source = load_image(input_path, max_side)
        source = enhance_image(source, brightness, contrast, saturation, sharpness)
        pixel_grid = make_pixel_grid(source, columns, sampling)
        pixel_grid = reduce_palette(pixel_grid, colors, dither)
        result = enlarge_pixels(pixel_grid, pixel_size)
        result = add_pixel_grid(result, pixel_size, grid_opacity)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        suffix = output_path.suffix.lower()
        save_options = {}
        if suffix in {".jpg", ".jpeg"}:
                save_options = {"quality": 95, "subsampling": 0, "optimize": True}
        elif suffix == ".png":
                save_options = {"optimize": True}
        result.save(output_path, **save_options)
        return result.size


def build_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
                description="Turn a regular image into clean, customizable pixel art.",
                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument("input", type=Path, help="path to the source image")
        parser.add_argument(
                "-o", "--output", type=Path, default=Path("pixel_art.png"),
                help="output image path",
        )
        parser.add_argument(
                "--columns", type=positive_int, default=320,
                help="number of logical pixels across the image",
        )
        parser.add_argument(
                "--pixel-size", type=positive_int, default=6,
                help="size in output pixels of each logical pixel",
        )
        parser.add_argument(
                "--colors", type=positive_int, default=64,
                help="maximum number of colors in the final palette (2-256)",
        )
        parser.add_argument(
                "--dither", choices=("none", "floyd"), default="none",
                help="color dithering mode; Floyd-Steinberg adds texture",
        )
        parser.add_argument(
                "--sampling", choices=("box", "bilinear", "bicubic", "lanczos"),
                default="lanczos", help="filter used when shrinking the source",
        )
        parser.add_argument(
                "--brightness", type=bounded_float(0.1, 3.0), default=1.0,
                help="brightness multiplier",
        )
        parser.add_argument(
                "--contrast", type=bounded_float(0.1, 3.0), default=1.08,
                help="contrast multiplier",
        )
        parser.add_argument(
                "--saturation", type=bounded_float(0.0, 3.0), default=1.08,
                help="color saturation multiplier",
        )
        parser.add_argument(
                "--sharpness", type=bounded_float(0.0, 4.0), default=1.15,
                help="sharpness multiplier applied before pixelation",
        )
        parser.add_argument(
                "--grid", type=int, choices=range(0, 121), default=0, metavar="0-120",
                help="optional dark pixel-grid opacity; 0 disables it",
        )
        parser.add_argument(
                "--max-side", type=positive_int, default=12000,
                help="safety limit for the longest source-image side",
        )
        return parser


def main(argv: Optional[list[str]] = None) -> int:
        parser = build_parser()
        args = parser.parse_args(argv)
        try:
                width, height = convert(
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
                        grid_opacity=args.grid,
                        max_side=args.max_side,
                )
        except (OSError, ValueError) as error:
                print(f"Error: {error}", file=sys.stderr)
                return 1

        print(f"Done! Saved: {args.output}")
        print(f"Output size: {width} x {height}")
        print(f"Logical pixel grid: {args.columns} columns")
        return 0


if __name__ == "__main__":
        raise SystemExit(main())