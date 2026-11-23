
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from pathlib import Path
import threading
import os
import sys

# Import the PixelForge engine
try:
    import pixelforge
except ImportError:
    pixelforge = None


class PixelForgeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PixelForge Studio")
        self.root.geometry("1000x720")
        self.root.minsize(850, 600)
        self.root.configure(bg="#101014")

        self.input_path = None
        self.output_path = None
        self.preview_image = None

        self.bg = "#101014"
        self.panel = "#191920"
        self.accent = "#9B72FF"
        self.text = "#F4F1FF"
        self.muted = "#A5A0B5"

        self.setup_style()
        self.build_ui()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TCombobox",
            fieldbackground=self.panel,
            background=self.panel,
            foreground=self.text
        )

        style.configure(
            "Horizontal.TScale",
            background=self.panel,
            troughcolor="#33303D"
        )

    def build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=self.bg)
        header.pack(fill="x", padx=30, pady=(22, 15))

        tk.Label(
            header,
            text="PIXELFORGE",
            font=("Segoe UI", 25, "bold"),
            fg=self.accent,
            bg=self.bg
        ).pack(side="left")

        tk.Label(
            header,
            text="STUDIO  /  IMAGE TO PIXEL ART",
            font=("Segoe UI", 9),
            fg=self.muted,
            bg=self.bg
        ).pack(side="left", padx=15, pady=12)

        # Main layout
        main = tk.Frame(self.root, bg=self.bg)
        main.pack(fill="both", expand=True, padx=25, pady=10)

        # Left settings panel
        settings = tk.Frame(main, bg=self.panel, width=310)
        settings.pack(side="left", fill="y", padx=(0, 15))
        settings.pack_propagate(False)

        tk.Label(
            settings,
            text="SETTINGS",
            font=("Segoe UI", 13, "bold"),
            fg=self.text,
            bg=self.panel
        ).pack(anchor="w", padx=20, pady=(20, 15))

        self.add_button(
            settings,
            "Choose Image",
            self.choose_image
        )

        self.file_label = tk.Label(
            settings,
            text="No image selected",
            fg=self.muted,
            bg=self.panel,
            wraplength=260,
            font=("Segoe UI", 9)
        )
        self.file_label.pack(anchor="w", padx=20, pady=10)

        self.add_separator(settings)

        self.columns = self.add_slider(
            settings, "Pixel Resolution", 32, 512, 160
        )

        self.pixel_size = self.add_slider(
            settings, "Pixel Block Size", 1, 12, 4
        )

        self.colors = self.add_slider(
            settings, "Color Palette", 2, 256, 64
        )

        self.brightness = self.add_slider(
            settings, "Brightness", 0.2, 2.0, 1.0
        )

        self.contrast = self.add_slider(
            settings, "Contrast", 0.2, 2.0, 1.0
        )

        self.saturation = self.add_slider(
            settings, "Saturation", 0.0, 2.0, 1.0
        )

        self.add_separator(settings)

        self.dither_var = tk.BooleanVar(value=True)

        tk.Checkbutton(
            settings,
            text="Enable Dithering",
            variable=self.dither_var,
            bg=self.panel,
            fg=self.text,
            selectcolor="#30283F",
            activebackground=self.panel,
            activeforeground=self.text
        ).pack(anchor="w", padx=20, pady=8)

        self.filter_var = tk.StringVar(value="box")

        tk.Label(
            settings,
            text="Sampling Filter",
            fg=self.text,
            bg=self.panel
        ).pack(anchor="w", padx=20, pady=(8, 4))

        ttk.Combobox(
            settings,
            textvariable=self.filter_var,
            values=["box", "bilinear", "bicubic", "lanczos"],
            state="readonly"
        ).pack(fill="x", padx=20)

        self.add_button(
            settings,
            "GENERATE PIXEL ART",
            self.generate,
            accent=True
        )

        # Right preview panel
        preview = tk.Frame(main, bg=self.panel)
        preview.pack(side="right", fill="both", expand=True)

        tk.Label(
            preview,
            text="LIVE PREVIEW",
            font=("Segoe UI", 13, "bold"),
            fg=self.text,
            bg=self.panel
        ).pack(anchor="w", padx=20, pady=20)

        self.preview_area = tk.Label(
            preview,
            text="Select an image to get started",
            bg="#111116",
            fg=self.muted,
            font=("Segoe UI", 12)
        )
        self.preview_area.pack(
            fill="both", expand=True, padx=20, pady=(0, 15)
        )

        self.status = tk.Label(
            self.root,
            text="Ready",
            bg=self.bg,
            fg=self.muted,
            anchor="w",
            font=("Segoe UI", 9)
        )
        self.status.pack(fill="x", padx=30, pady=10)

    def add_button(self, parent, text, command, accent=False):
        color = self.accent if accent else "#292632"
        fg = "#FFFFFF"

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=fg,
            activebackground="#8057E8",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            pady=11
        )
        btn.pack(fill="x", padx=20, pady=8)
        return btn

    def add_separator(self, parent):
        tk.Frame(
            parent,
            height=1,
            bg="#34313E"
        ).pack(fill="x", padx=20, pady=12)

    def add_slider(self, parent, label, minimum, maximum, default):
        container = tk.Frame(parent, bg=self.panel)
        container.pack(fill="x", padx=20, pady=5)

        value = tk.DoubleVar(value=default)

        top = tk.Frame(container, bg=self.panel)
        top.pack(fill="x")

        tk.Label(
            top,
            text=label,
            fg=self.text,
            bg=self.panel,
            font=("Segoe UI", 9)
        ).pack(side="left")

        value_label = tk.Label(
            top,
            text=str(default),
            fg=self.accent,
            bg=self.panel
        )
        value_label.pack(side="right")

        def update_label(v):
            value_label.config(text=f"{float(v):.1f}")

        tk.Scale(
            container,
            from_=minimum,
            to=maximum,
            variable=value,
            orient="horizontal",
            command=update_label,
            resolution=1 if isinstance(default, int) else 0.1,
            bg=self.panel,
            fg=self.text,
            highlightthickness=0,
            troughcolor="#383342",
            activebackground=self.accent,
            bd=0
        ).pack(fill="x")

        return value

    def choose_image(self):
        path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        self.input_path = path
        self.file_label.config(text=Path(path).name)

        try:
            image = Image.open(path)
            self.show_preview(image)
            self.status.config(text="Image loaded successfully")
        except Exception as error:
            messagebox.showerror("Image Error", str(error))

    def show_preview(self, image):
        image = image.convert("RGB")
        image.thumbnail((650, 500))

        self.preview_image = ImageTk.PhotoImage(image)
        self.preview_area.config(
            image=self.preview_image,
            text=""
        )

    def generate(self):
        if not self.input_path:
            messagebox.showwarning(
                "No Image",
                "Please choose an image first."
            )
            return

        if pixelforge is None:
            messagebox.showerror(
                "Missing Engine",
                "pixelforge.py must be in the same folder."
            )
            return

        output = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg")
            ],
            initialfile="pixel_art.png"
        )

        if not output:
            return

        self.output_path = output
        self.status.config(text="Generating pixel art...")

        thread = threading.Thread(
            target=self.process_image,
            args=(output,),
            daemon=True
        )
        thread.start()

    def process_image(self, output):
        try:
            pixelforge.convert(
                input_path=self.input_path,
                output_path=output,
                columns=int(self.columns.get()),
                pixel_size=int(self.pixel_size.get()),
                colors=int(self.colors.get()),
                dither=self.dither_var.get(),
                sampling=self.filter_var.get(),
                brightness=float(self.brightness.get()),
                contrast=float(self.contrast.get()),
                saturation=float(self.saturation.get())
            )

            self.root.after(
                0, lambda: self.finish_success(output)
            )

        except Exception as error:
            self.root.after(
                0, lambda: self.finish_error(str(error))
            )

    def finish_success(self, output):
        self.status.config(text="Pixel art generated successfully!")

        image = Image.open(output)
        self.show_preview(image)

        messagebox.showinfo(
            "Success",
            f"Your pixel art has been saved to:\n{output}"
        )

    def finish_error(self, error):
        self.status.config(text="Generation failed")
        messagebox.showerror("Generation Error", error)


if __name__ == "__main__":
    root = tk.Tk()
    app = PixelForgeGUI(root)
    root.mainloop()
