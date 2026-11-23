
"""
PixelForge Studio 2.0
Professional Tkinter GUI

Requirements:
    pip install Pillow

Keep this file in the same folder as pixelforge.py.
"""

from __future__ import annotations

import os
import sys
import threading
import queue
import tkinter as tk

from pathlib import Path
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ImageTk, ImageOps

import pixelforge


# ============================================================
# THEME
# ============================================================

BG = "#101016"
PANEL = "#191923"
PANEL_LIGHT = "#222231"
BORDER = "#303044"
PURPLE = "#9270FF"
PURPLE_HOVER = "#A78BFA"
TEXT = "#F3F0FF"
MUTED = "#A09DB3"
SUCCESS = "#65D6A0"
DANGER = "#FF6B81"


# ============================================================
# MAIN APPLICATION
# ============================================================

class PixelForgeGUI:

    def __init__(self, root):

        self.root = root
        self.root.title("PixelForge Studio 2.0")
        self.root.geometry("1250x800")
        self.root.minsize(950, 650)
        self.root.configure(bg=BG)

        self.input_path = None
        self.output_path = None

        self.original_image = None
        self.result_image = None

        self.original_photo = None
        self.result_photo = None

        self.worker = None
        self.cancel_event = threading.Event()
        self.messages = queue.Queue()

        self.preview_mode = "before"
        self.zoom = 1.0

        self.closing = False

        self._create_variables()
        self._setup_styles()
        self._build_interface()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.root.after(100, self._process_messages)

    # ========================================================
    # VARIABLES
    # ========================================================

    def _create_variables(self):

        self.columns = tk.IntVar(value=160)
        self.pixel_size = tk.IntVar(value=4)
        self.colors = tk.IntVar(value=64)

        self.brightness = tk.DoubleVar(value=1.0)
        self.contrast = tk.DoubleVar(value=1.08)
        self.saturation = tk.DoubleVar(value=1.08)
        self.sharpness = tk.DoubleVar(value=1.15)

        self.grid_opacity = tk.IntVar(value=0)

        self.dither = tk.StringVar(value="floyd")
        self.sampling = tk.StringVar(value="lanczos")

        self.output_format = tk.StringVar(value="PNG")

        self.status = tk.StringVar(
            value="Ready — Choose an image to begin."
        )

        self.progress = tk.DoubleVar(value=0)

        self.zoom_label = tk.StringVar(value="100%")

    # ========================================================
    # STYLES
    # ========================================================

    def _setup_styles(self):

        style = ttk.Style()

        style.theme_use("clam")

        style.configure(
            "Pixel.Horizontal.TProgressbar",
            troughcolor=PANEL_LIGHT,
            background=PURPLE,
            bordercolor=PANEL_LIGHT,
            lightcolor=PURPLE,
            darkcolor=PURPLE,
            thickness=8
        )

        style.configure(
            "Pixel.TCombobox",
            fieldbackground=PANEL_LIGHT,
            background=PANEL_LIGHT,
            foreground=TEXT,
            arrowcolor=TEXT,
            bordercolor=BORDER,
            padding=8
        )

        style.map(
            "Pixel.TCombobox",
            fieldbackground=[("readonly", PANEL_LIGHT)],
            foreground=[("readonly", TEXT)]
        )

        style.configure(
            "Pixel.TScale",
            background=PANEL,
            troughcolor=PANEL_LIGHT
        )

    # ========================================================
    # UI HELPERS
    # ========================================================

    def _label(
        self,
        parent,
        text,
        size=10,
        color=TEXT,
        weight="normal"
    ):

        return tk.Label(
            parent,
            text=text,
            bg=parent.cget("bg"),
            fg=color,
            font=("Segoe UI", size, weight),
            anchor="w"
        )

    def _button(
        self,
        parent,
        text,
        command,
        primary=False,
        danger=False,
        width=None
    ):

        background = PANEL_LIGHT
        foreground = TEXT

        if primary:
            background = PURPLE

        if danger:
            background = "#512733"

        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=background,
            fg=foreground,
            activebackground=PURPLE_HOVER,
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=10,
            width=width
        )

        return button

    def _section(self, parent, title):

        frame = tk.Frame(
            parent,
            bg=PANEL,
            padx=16,
            pady=12
        )

        self._label(
            frame,
            title.upper(),
            size=9,
            color=PURPLE,
            weight="bold"
        ).pack(anchor="w", pady=(0, 12))

        return frame

    # ========================================================
    # MAIN LAYOUT
    # ========================================================

    def _build_interface(self):

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_main_area()
        self._build_status_bar()

    # ========================================================
    # HEADER
    # ========================================================

    def _build_header(self):

        header = tk.Frame(
            self.root,
            bg=BG,
            padx=24,
            pady=17
        )

        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        logo = tk.Frame(header, bg=BG)
        logo.grid(row=0, column=0, sticky="w")

        self._label(
            logo,
            "PIXEL",
            size=20,
            color=TEXT,
            weight="bold"
        ).pack(side="left")

        self._label(
            logo,
            "FORGE",
            size=20,
            color=PURPLE,
            weight="bold"
        ).pack(side="left")

        self._label(
            logo,
            "STUDIO 2.0",
            size=9,
            color=MUTED
        ).pack(side="left", padx=(10, 0), pady=(8, 0))

        actions = tk.Frame(header, bg=BG)
        actions.grid(row=0, column=2, sticky="e")

        self._button(
            actions,
            "＋  Open Image",
            self.choose_image,
            primary=True
        ).pack(side="left", padx=5)

        self._button(
            actions,
            "Reset",
            self.reset_settings
        ).pack(side="left", padx=5)

    # ========================================================
    # MAIN AREA
    # ========================================================

    def _build_main_area(self):

        main = tk.Frame(
            self.root,
            bg=BG,
            padx=18,
            pady=5
        )

        main.grid(row=1, column=0, sticky="nsew")

        main.grid_columnconfigure(0, weight=0)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        self._build_settings_panel(main)
        self._build_workspace(main)

    # ========================================================
    # SCROLLABLE SETTINGS
    # ========================================================

    def _build_settings_panel(self, parent):

        container = tk.Frame(
            parent,
            bg=PANEL,
            width=310
        )

        container.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 12)
        )

        container.grid_propagate(False)
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self._label(
            container,
            "SETTINGS",
            size=14,
            weight="bold"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=17,
            pady=15
        )

        canvas_frame = tk.Frame(container, bg=PANEL)
        canvas_frame.grid(row=1, column=0, sticky="nsew")

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        self.settings_canvas = tk.Canvas(
            canvas_frame,
            bg=PANEL,
            highlightthickness=0
        )

        scrollbar = ttk.Scrollbar(
            canvas_frame,
            orient="vertical",
            command=self.settings_canvas.yview
        )

        self.settings_canvas.configure(
            yscrollcommand=scrollbar.set
        )

        scrollbar.grid(row=0, column=1, sticky="ns")

        self.settings_canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.settings_content = tk.Frame(
            self.settings_canvas,
            bg=PANEL
        )

        self.canvas_window = self.settings_canvas.create_window(
            (0, 0),
            window=self.settings_content,
            anchor="nw"
        )

        self.settings_content.bind(
            "<Configure>",
            self._update_scroll_region
        )

        self.settings_canvas.bind(
            "<Configure>",
            self._resize_settings_content
        )

        self.settings_canvas.bind(
            "<Enter>",
            self._bind_mousewheel
        )

        self.settings_canvas.bind(
            "<Leave>",
            self._unbind_mousewheel
        )

        self._build_settings_content()

    def _update_scroll_region(self, event=None):

        self.settings_canvas.configure(
            scrollregion=self.settings_canvas.bbox("all")
        )

    def _resize_settings_content(self, event):

        self.settings_canvas.itemconfigure(
            self.canvas_window,
            width=event.width
        )

    def _bind_mousewheel(self, event=None):

        self.root.bind_all(
            "<MouseWheel>",
            self._on_mousewheel
        )

    def _unbind_mousewheel(self, event=None):

        self.root.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):

        if self.settings_canvas.winfo_exists():
            self.settings_canvas.yview_scroll(
                int(-event.delta / 120),
                "units"
            )

    # ========================================================
    # SETTINGS CONTENT
    # ========================================================

    def _build_settings_content(self):

        self._build_resolution_settings()
        self._build_color_settings()
        self._build_enhancement_settings()
        self._build_render_settings()
        self._build_export_settings()

    def _add_slider(
        self,
        parent,
        title,
        variable,
        minimum,
        maximum,
        resolution=1
    ):

        frame = tk.Frame(parent, bg=PANEL)
        frame.pack(fill="x", padx=16, pady=8)

        top = tk.Frame(frame, bg=PANEL)
        top.pack(fill="x")

        self._label(
            top,
            title,
            size=10
        ).pack(side="left")

        value_label = self._label(
            top,
            str(variable.get()),
            size=9,
            color=PURPLE
        )

        value_label.pack(side="right")

        def update(value):

            number = float(value)

            if resolution >= 1:
                value_label.config(text=str(int(number)))
            else:
                value_label.config(text=f"{number:.2f}")

        scale = tk.Scale(
            frame,
            variable=variable,
            from_=minimum,
            to=maximum,
            resolution=resolution,
            orient="horizontal",
            showvalue=False,
            bg=PANEL,
            fg=TEXT,
            troughcolor=PANEL_LIGHT,
            activebackground=PURPLE,
            highlightthickness=0,
            bd=0,
            command=update,
            length=230
        )

        scale.pack(fill="x")

        update(variable.get())

    def _build_resolution_settings(self):

        section = self._section(
            self.settings_content,
            "Pixel Resolution"
        )

        section.pack(fill="x", pady=(0, 2))

        self._add_slider(
            section,
            "Columns",
            self.columns,
            32,
            512
        )

        self._add_slider(
            section,
            "Pixel Size",
            self.pixel_size,
            1,
            16
        )

        self._add_slider(
            section,
            "Maximum Colors",
            self.colors,
            2,
            256
        )

    def _build_color_settings(self):

        section = self._section(
            self.settings_content,
            "Color Processing"
        )

        section.pack(fill="x", pady=2)

        self._label(
            section,
            "Dithering",
            size=10
        ).pack(anchor="w")

        ttk.Combobox(
            section,
            textvariable=self.dither,
            values=["none", "floyd"],
            state="readonly",
            style="Pixel.TCombobox"
        ).pack(fill="x", pady=(6, 12))

        self._label(
            section,
            "Sampling Filter",
            size=10
        ).pack(anchor="w")

        ttk.Combobox(
            section,
            textvariable=self.sampling,
            values=[
                "box",
                "bilinear",
                "bicubic",
                "lanczos",
                "nearest"
            ],
            state="readonly",
            style="Pixel.TCombobox"
        ).pack(fill="x", pady=(6, 4))

    def _build_enhancement_settings(self):

        section = self._section(
            self.settings_content,
            "Image Enhancement"
        )

        section.pack(fill="x", pady=2)

        self._add_slider(
            section,
            "Brightness",
            self.brightness,
            0.1,
            2.0,
            0.05
        )

        self._add_slider(
            section,
            "Contrast",
            self.contrast,
            0.1,
            2.0,
            0.05
        )

        self._add_slider(
            section,
            "Saturation",
            self.saturation,
            0.0,
            2.0,
            0.05
        )

        self._add_slider(
            section,
            "Sharpness",
            self.sharpness,
            0.0,
            2.0,
            0.05
        )

    def _build_render_settings(self):

        section = self._section(
            self.settings_content,
            "Pixel Grid"
        )

        section.pack(fill="x", pady=2)

        self._add_slider(
            section,
            "Grid Opacity",
            self.grid_opacity,
            0,
            120
        )

    def _build_export_settings(self):

        section = self._section(
            self.settings_content,
            "Export"
        )

        section.pack(fill="x", pady=2)

        self._label(
            section,
            "Output Format",
            size=10
        ).pack(anchor="w")

        ttk.Combobox(
            section,
            textvariable=self.output_format,
            values=["PNG", "JPEG"],
            state="readonly",
            style="Pixel.TCombobox"
        ).pack(fill="x", pady=(6, 4))

    # ========================================================
    # WORKSPACE
    # ========================================================

    def _build_workspace(self, parent):

        workspace = tk.Frame(
            parent,
            bg=BG
        )

        workspace.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        workspace.grid_columnconfigure(0, weight=1)
        workspace.grid_rowconfigure(1, weight=1)

        self._build_preview_toolbar(workspace)
        self._build_preview_area(workspace)
        self._build_action_bar(workspace)

    # ========================================================
    # PREVIEW TOOLBAR
    # ========================================================

    def _build_preview_toolbar(self, parent):

        toolbar = tk.Frame(
            parent,
            bg=PANEL,
            padx=12,
            pady=10
        )

        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.grid_columnconfigure(0, weight=1)

        self.preview_title = self._label(
            toolbar,
            "PREVIEW",
            size=10,
            color=TEXT,
            weight="bold"
        )

        self.preview_title.grid(row=0, column=0, sticky="w")

        controls = tk.Frame(toolbar, bg=PANEL)
        controls.grid(row=0, column=1, sticky="e")

        self._button(
            controls,
            "Before",
            lambda: self.set_preview_mode("before")
        ).pack(side="left", padx=2)

        self._button(
            controls,
            "After",
            lambda: self.set_preview_mode("after")
        ).pack(side="left", padx=2)

        self._button(
            controls,
            "−",
            lambda: self.change_zoom(-0.1)
        ).pack(side="left", padx=2)

        self._label(
            controls,
            "100%",
            size=9,
            color=PURPLE
        ).pack(side="left", padx=5)

        self._button(
            controls,
            "+",
            lambda: self.change_zoom(0.1)
        ).pack(side="left", padx=2)

        self._button(
            controls,
            "Fit",
            self.fit_preview
        ).pack(side="left", padx=2)

    # ========================================================
    # PREVIEW AREA
    # ========================================================

    def _build_preview_area(self, parent):

        self.preview_container = tk.Frame(
            parent,
            bg="#0C0C12",
            highlightbackground=BORDER,
            highlightthickness=1
        )

        self.preview_container.grid(
            row=1,
            column=0,
            sticky="nsew",
            pady=12
        )

        self.preview_container.grid_rowconfigure(0, weight=1)
        self.preview_container.grid_columnconfigure(0, weight=1)

        self.preview_label = tk.Label(
            self.preview_container,
            text="",
            bg="#0C0C12",
            fg=MUTED
        )

        self.preview_label.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=15,
            pady=15
        )

        self.empty_state = tk.Frame(
            self.preview_container,
            bg="#0C0C12"
        )

        self.empty_state.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        self._label(
            self.empty_state,
            "PIXELFORGE STUDIO",
            size=22,
            color=PURPLE,
            weight="bold"
        ).pack(pady=8)

        self._label(
            self.empty_state,
            "Choose an image to start creating pixel art.",
            size=10,
            color=MUTED
        ).pack()

        self.preview_container.bind(
            "<Configure>",
            lambda event: self._refresh_preview()
        )

    # ========================================================
    # ACTION BAR
    # ========================================================

    def _build_action_bar(self, parent):

        bar = tk.Frame(
            parent,
            bg=PANEL,
            padx=12,
            pady=12
        )

        bar.grid(row=2, column=0, sticky="ew")
        bar.grid_columnconfigure(0, weight=1)

        self._button(
            bar,
            "Generate Pixel Art",
            self.generate,
            primary=True
        ).grid(row=0, column=0, sticky="w")

        self.cancel_button = self._button(
            bar,
            "Cancel",
            self.cancel_conversion,
            danger=True
        )

        self.cancel_button.grid(
            row=0,
            column=1,
            padx=5
        )

        self.cancel_button.config(state="disabled")

        self.export_button = self._button(
            bar,
            "Export",
            self.export_result
        )

        self.export_button.grid(
            row=0,
            column=2,
            padx=5
        )

        self.export_button.config(state="disabled")

        self.progress_bar = ttk.Progressbar(
            bar,
            variable=self.progress,
            maximum=100,
            style="Pixel.Horizontal.TProgressbar"
        )

        self.progress_bar.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(15, 0)
        )

    # ========================================================
    # STATUS BAR
    # ========================================================

    def _build_status_bar(self):

        status_bar = tk.Frame(
            self.root,
            bg=PANEL,
            padx=18,
            pady=9
        )

        status_bar.grid(row=2, column=0, sticky="ew")
        status_bar.grid_columnconfigure(0, weight=1)

        self.status_label = self._label(
            status_bar,
            "",
            size=9,
            color=MUTED
        )

        self.status_label.config(
            textvariable=self.status
        )

        self.status_label.grid(
            row=0,
            column=0,
            sticky="w"
        )

        self._label(
            status_bar,
            "PIXELFORGE 2.0",
            size=9,
            color=PURPLE
        ).grid(row=0, column=1, sticky="e")

    # ========================================================
    # IMAGE SELECTION
    # ========================================================

    def choose_image(self):

        if self.worker and self.worker.is_alive():
            messagebox.showwarning(
                "Busy",
                "Please wait for the current conversion."
            )
            return

        path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff"),
                ("All Files", "*.*")
            ]
        )

        if not path:
            return

        try:

            image = pixelforge.load_image(path)

            self.input_path = Path(path)
            self.original_image = image
            self.result_image = None
            self.output_path = None

            self.export_button.config(state="disabled")

            self.status.set(
                f"Loaded: {self.input_path.name}  |  "
                f"{image.width} × {image.height}"
            )

            self.preview_mode = "before"

            self.empty_state.place_forget()

            self._refresh_preview()

        except Exception as error:

            messagebox.showerror(
                "Image Error",
                str(error)
            )

    # ========================================================
    # PREVIEW MODE
    # ========================================================

    def set_preview_mode(self, mode):

        self.preview_mode = mode
        self._refresh_preview()

    def change_zoom(self, amount):

        self.zoom = max(
            0.1,
            min(3.0, self.zoom + amount)
        )

        self._refresh_preview()

    def fit_preview(self):

        self.zoom = 1.0
        self._refresh_preview()

    def _refresh_preview(self):

        if not hasattr(self, "preview_label"):
            return

        if self.original_image is None:
            return

        if self.preview_mode == "after" and self.result_image:
            image = self.result_image
        else:
            image = self.original_image

        self._display_image(image)

    def _display_image(self, image):

        try:

            width = max(
                100,
                self.preview_container.winfo_width() - 40
            )

            height = max(
                100,
                self.preview_container.winfo_height() - 40
            )

            preview = image.copy()

            preview.thumbnail(
                (width, height),
                Image.Resampling.LANCZOS
            )

            if self.zoom != 1.0:

                new_width = max(
                    1,
                    int(preview.width * self.zoom)
                )

                new_height = max(
                    1,
                    int(preview.height * self.zoom)
                )

                preview = preview.resize(
                    (new_width, new_height),
                    Image.Resampling.LANCZOS
                )

            if preview.mode == "RGBA":

                background = Image.new(
                    "RGBA",
                    preview.size,
                    "#252535"
                )

                background.alpha_composite(preview)
                preview = background.convert("RGB")

            self.preview_photo = ImageTk.PhotoImage(preview)

            self.preview_label.config(
                image=self.preview_photo,
                text=""
            )

        except Exception:
            pass

    # ========================================================
    # COLLECT SETTINGS ON MAIN THREAD
    # ========================================================

    def _get_settings(self):

        return {
            "columns": self.columns.get(),
            "pixel_size": self.pixel_size.get(),
            "colors": self.colors.get(),

            "brightness": self.brightness.get(),
            "contrast": self.contrast.get(),
            "saturation": self.saturation.get(),
            "sharpness": self.sharpness.get(),

            "grid_opacity": self.grid_opacity.get(),

            "dither": self.dither.get(),
            "sampling": self.sampling.get(),
        }

    # ========================================================
    # GENERATE
    # ========================================================

    def generate(self):

        if self.input_path is None:
            messagebox.showwarning(
                "No Image",
                "Please choose an image first."
            )
            return

        if self.worker and self.worker.is_alive():
            return

        extension = (
            ".png"
            if self.output_format.get() == "PNG"
            else ".jpg"
        )

        default_name = (
            f"{self.input_path.stem}_pixelforge{extension}"
        )

        output = filedialog.asksaveasfilename(
            title="Save Pixel Art",
            initialfile=default_name,
            defaultextension=extension,
            filetypes=[
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg *.jpeg")
            ]
        )

        if not output:
            return

        self.output_path = Path(output)

        settings = self._get_settings()
        input_path = self.input_path
        output_path = self.output_path

        self.cancel_event.clear()
        self.progress.set(0)

        self.status.set("Starting conversion...")

        self.cancel_button.config(state="normal")

        self.export_button.config(state="disabled")

        self.worker = threading.Thread(
            target=self._worker_conversion,
            args=(input_path, output_path, settings),
            daemon=True
        )

        self.worker.start()

    # ========================================================
    # BACKGROUND WORKER
    # ========================================================

    def _worker_conversion(
        self,
        input_path,
        output_path,
        settings
    ):

        def progress_callback(value, message):

            self.messages.put(
                ("progress", value, message)
            )

        def cancel_callback():

            return self.cancel_event.is_set()

        try:

            dimensions = pixelforge.convert(
                input_path,
                output_path,
                progress_callback=progress_callback,
                cancel_callback=cancel_callback,
                **settings
            )

            if self.cancel_event.is_set():

                self.messages.put(
                    ("cancelled",)
                )

            else:

                self.messages.put(
                    ("success", str(output_path), dimensions)
                )

        except pixelforge.ConversionCancelled:

            self.messages.put(
                ("cancelled",)
            )

        except Exception as error:

            self.messages.put(
                ("error", str(error))
            )

    # ========================================================
    # MESSAGE QUEUE
    # ========================================================

    def _process_messages(self):

        if self.closing:
            return

        try:

            while True:

                message = self.messages.get_nowait()

                kind = message[0]

                if kind == "progress":

                    _, value, text = message

                    self.progress.set(value)
                    self.status.set(text)

                elif kind == "success":

                    _, path, dimensions = message

                    self._finish_success(
                        Path(path),
                        dimensions
                    )

                elif kind == "error":

                    self._finish_error(message[1])

                elif kind == "cancelled":

                    self._finish_cancelled()

        except queue.Empty:
            pass

        self.root.after(
            100,
            self._process_messages
        )

    # ========================================================
    # COMPLETION HANDLERS
    # ========================================================

    def _finish_success(self, path, dimensions):

        try:

            with Image.open(path) as image:
                self.result_image = image.copy()

            self.output_path = path

            self.preview_mode = "after"
            self.zoom = 1.0

            self._refresh_preview()

            self.progress.set(100)

            self.status.set(
                f"Completed: {path.name}  |  "
                f"{dimensions[0]} × {dimensions[1]}"
            )

            self.export_button.config(state="normal")

            self.cancel_button.config(state="disabled")

            messagebox.showinfo(
                "Success",
                f"Pixel art created successfully!\n\n{path}"
            )

        except Exception as error:

            self._finish_error(str(error))

    def _finish_error(self, error):

        self.cancel_button.config(state="disabled")

        self.status.set("Conversion failed.")

        messagebox.showerror(
            "Conversion Error",
            error
        )

    def _finish_cancelled(self):

        self.cancel_button.config(state="disabled")

        self.progress.set(0)

        self.status.set("Conversion cancelled.")

    # ========================================================
    # CANCEL
    # ========================================================

    def cancel_conversion(self):

        if self.worker and self.worker.is_alive():

            self.cancel_event.set()

            self.status.set(
                "Cancelling conversion..."
            )

            self.cancel_button.config(
                state="disabled"
            )

    # ========================================================
    # EXPORT
    # ========================================================

    def export_result(self):

        if self.result_image is None:
            messagebox.showwarning(
                "No Result",
                "Generate an image before exporting."
            )
            return

        extension = (
            ".png"
            if self.output_format.get() == "PNG"
            else ".jpg"
        )

        output = filedialog.asksaveasfilename(
            title="Export Pixel Art",
            defaultextension=extension,
            filetypes=[
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg *.jpeg")
            ]
        )

        if not output:
            return

        try:

            image = self.result_image.copy()

            if Path(output).suffix.lower() in (".jpg", ".jpeg"):

                if image.mode == "RGBA":

                    background = Image.new(
                        "RGB",
                        image.size,
                        "white"
                    )

                    background.paste(
                        image,
                        mask=image.getchannel("A")
                    )

                    image = background

                image.save(
                    output,
                    format="JPEG",
                    quality=95
                )

            else:

                image.save(
                    output,
                    format="PNG",
                    optimize=True
                )

            self.status.set(
                f"Exported: {Path(output).name}"
            )

            messagebox.showinfo(
                "Export Complete",
                f"Saved successfully:\n{output}"
            )

        except Exception as error:

            messagebox.showerror(
                "Export Error",
                str(error)
            )

    # ========================================================
    # RESET
    # ========================================================

    def reset_settings(self):

        if self.worker and self.worker.is_alive():
            return

        self.columns.set(160)
        self.pixel_size.set(4)
        self.colors.set(64)

        self.brightness.set(1.0)
        self.contrast.set(1.08)
        self.saturation.set(1.08)
        self.sharpness.set(1.15)

        self.grid_opacity.set(0)

        self.dither.set("floyd")
        self.sampling.set("lanczos")

        self.output_format.set("PNG")

        self.zoom = 1.0

        self.status.set("Settings restored to defaults.")

        self._refresh_preview()

    # ========================================================
    # SAFE CLOSE
    # ========================================================

    def on_close(self):

        if self.worker and self.worker.is_alive():

            self.cancel_event.set()

            self.status.set(
                "Waiting for conversion to stop..."
            )

            self.closing = True

            self.root.after(
                100,
                self._wait_for_worker
            )

            return

        self.root.destroy()

    def _wait_for_worker(self):

        if self.worker and self.worker.is_alive():

            self.root.after(
                100,
                self._wait_for_worker
            )

        else:

            self.root.destroy()


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

def main():

    root = tk.Tk()

    app = PixelForgeGUI(root)

    root.mainloop()


if __name__ == "__main__":
    main()
