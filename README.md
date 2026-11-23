# PixelForge 🎨

**A customizable Python Pixel Art Converter**

PixelForge is an image-processing application built with Python and Pillow. It transforms regular images into pixel art through color quantization, image resizing, and nearest-neighbor interpolation.

## Features

- Custom pixel resolution
- Adjustable pixel block size
- Adaptive color palette
- Floyd–Steinberg dithering
- Multiple resampling filters
- Brightness and contrast adjustment
- Saturation and sharpness controls
- Optional pixel grid overlay
- PNG and JPEG export
- Desktop GUI (Tkinter)

## Technologies

- Python 3
- Pillow
- Tkinter

## Installation

Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd PixelForge
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the command-line version:

```bash
python pixelforge.py original_reference.jpg
```

Run the graphical interface:

```bash
python pixelforge_gui.py
```

## Project Structure

```text
PixelForge/
├── pixelforge.py
├── pixelforge_gui.py
├── README.md
├── requirements.txt
├── LICENSE
├── .gitignore
└── assets/
```

## How It Works

1. Load an input image.
2. Resize it into a smaller pixel grid.
3. Reduce the number of colors using adaptive quantization.
4. Optionally apply dithering.
5. Enlarge the grid using nearest-neighbor interpolation.
6. Export the final pixel art.


## Credits

- **Original Artwork:** [@mangoscribble](https://www.instagram.com/mangoscribble/)

Special thanks to the original artist for the artwork used as a reference for this project.

All rights to the original artwork belong to its creator.

## License

MIT License.