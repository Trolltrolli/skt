import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import tomllib
import tomli_w

# -------------------------------------------------
# CONFIG SEARCH (±2 LEVELS)
# -------------------------------------------------

CONFIG_NAMES = {
    "xenia-canary-mousehook.config.toml",
    "xenia-canary.config.toml",
    "xenia.config.toml",
}

CONFIG_PRIORITY = [
    "xenia-canary-mousehook.config.toml",
    "xenia-canary.config.toml",
    "xenia.config.toml",
]

AA_VALUES = ["none", "fxaa", "fxaa_extreme"]

SCALING_VALUES = ["bilinear", "cas", "fsr"]


def select_nearest_config(paths):
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    scored = []
    for p in paths:
        rel = os.path.relpath(p, exe_dir)
        depth = rel.count(os.sep)
        name = os.path.basename(p)
        try:
            name_prio = CONFIG_PRIORITY.index(name)
        except ValueError:
            name_prio = 99
        scored.append((depth, name_prio, p))
    scored.sort()
    return scored[0][2]

def find_config_files():
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    found = set()

    roots = {
        exe_dir,
        os.path.abspath(os.path.join(exe_dir, "..")),
        os.path.abspath(os.path.join(exe_dir, "../..")),
    }

    for root in roots:
        for cur, dirs, files in os.walk(root):
            depth = os.path.relpath(cur, root).count(os.sep)
            if depth > 2:
                dirs[:] = []
                continue
            for f in files:
                if f in CONFIG_NAMES:
                    found.add(os.path.join(cur, f))

    return sorted(found)

def load_toml(path):
    with open(path, "rb") as f:
        return tomllib.load(f)

def save_toml(path, data):
    with open(path, "wb") as f:
        tomli_w.dump(data, f)

# -------------------------------------------------
# RES ENUM
# -------------------------------------------------

RES_ENUM = {
    0:  "640x480",
    1:  "640x576",
    2:  "720x480",
    3:  "720x576",
    4:  "800x600",
    5:  "848x480",
    6:  "1024x768",
    7:  "1152x864",
    8:  "1280x720",
    9:  "1280x768",
    10: "1280x960",
    11: "1280x1024",
    12: "1360x768",
    13: "1440x900",
    14: "1680x1050",
    15: "1920x540",
    16: "1920x1080",
    17: "Custom",
}
RES_ENUM_INV = {v: k for k, v in RES_ENUM.items()}

# -------------------------------------------------
# DEFAULTS (RESET TARGET)
# -------------------------------------------------

DEFAULTS = {
    "res_id": 8,
    "width": 1280,
    "height": 720,
    "fullscreen": True,
    "vsync": True,
    "scale": 1,
    "aa": "none",
    "scaling_method": "bilinear",
    "sharpen": 0.0,
    "fsr_sharpen": 0.0,  
    "patches": True,
    "license": True,
    "dithering": False,
}

# -------------------------------------------------
# UI
# -------------------------------------------------

class XeniaConfigTool(tk.Tk):
    def __init__(self, paths):
        super().__init__()

        self.title("Xenia Simple Config Tool")
        self.geometry("650x830")
        self.resizable(False, False)
        self.eval("tk::PlaceWindow . center")
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.paths = paths
        self.data = load_toml(paths[0])
        self.fullscreen_var = tk.BooleanVar()
        self.vsync_var = tk.BooleanVar()
        self.setup_style()
        self.build_ui()
        self.load_values()

    # ---------------- STYLE ----------------

    def setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        bg = "#151C22"
        fg = "#e6e6e6"
        accent = "#3a3f45"
        hover = "#454b52"

        self.configure(bg=bg)

        style.configure(".", background=bg, foreground=fg)
        style.configure("TFrame", background=bg)
        style.configure("TLabelframe", background=bg, foreground=fg)
        style.configure("TLabelframe.Label", background=bg, foreground=fg)

        style.configure(
            "TLabel",
            background=bg,
            foreground=fg,
            padding=(4, 6)
        )

        style.configure(
            "TButton",
            background=accent,
            foreground=fg,
            padding=(12, 6),
            borderwidth=0
        )
        style.map(
            "TButton",
            background=[("active", hover)]
        )

        style.configure(
            "TCheckbutton",
            background=bg,
            foreground=fg,
            padding=6
        )

        style.map(
            "TCheckbutton",
            background=[
                ("active", hover),
                ("selected", bg)
            ],
            foreground=[
                ("disabled", "#888888")
            ]
        )

        style.configure(
            "TCombobox",
            fieldbackground=accent,
            background=accent,
            foreground=fg,
            arrowcolor=fg,
            padding=6
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", accent)],
            background=[("active", hover)],
            selectbackground=[("readonly", accent)],
            selectforeground=[("readonly", fg)]
        )

        style.configure(
            "TEntry",
            fieldbackground=accent,
            background=accent,
            foreground=fg,
            insertcolor=fg,
            borderwidth=0,
            padding=6
        )

        style.map(
            "TEntry",
            fieldbackground=[
                ("focus", hover),
                ("active", hover)
            ],
            foreground=[
                ("disabled", "#888888")
            ]
        )

        style.configure(
            "Horizontal.TScale",
            background=bg,
            troughcolor="#3a3f45",
            sliderlength=16
        )

        style.map(
            "Horizontal.TScale",
            background=[
                ("active", hover)
            ],
            troughcolor=[
                ("active", "#4b5158")
            ]
        )
        
        # ---- Combobox dropdown list (gray, not white) ----
        self.option_add("*TCombobox*Listbox.background", "#3a3f45")
        self.option_add("*TCombobox*Listbox.foreground", "#e6e6e6")
        self.option_add("*TCombobox*Listbox.selectBackground", "#454b52")
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        self.option_add("*TCombobox*Listbox.borderWidth", 0)


    # ---------------- UI ----------------

    def build_ui(self):
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, padx=24, pady=2)
        root.columnconfigure(0, weight=1)

        pad = {"padx": 14, "pady": 14}
        row_pad = {"padx": 6, "pady": 6}

        # ---------- VIDEO ----------
        video = ttk.LabelFrame(root, text="Video", padding=(14, 10))
        video.pack(fill="x", **pad)
        video.columnconfigure(1, weight=1)

        ttk.Label(video, text="Resolution  (internal render resolution)")\
            .grid(row=0, column=0, sticky="w", **row_pad)

        self.res_var = tk.StringVar()
        self.res_combo = ttk.Combobox(
            video,
            textvariable=self.res_var,
            values=list(RES_ENUM.values()),
            state="readonly",
            width=25
        )
        self.res_combo.grid(row=0, column=1, sticky="w", **row_pad)
        self.res_combo.bind("<<ComboboxSelected>>", self.on_res_change)

        ttk.Label(video, text="Width / Height  (custom resolution)")\
            .grid(row=1, column=0, sticky="w", **row_pad)

        self.w_var = tk.StringVar()
        self.h_var = tk.StringVar()
        ttk.Entry(video, textvariable=self.w_var, width=12)\
            .grid(row=1, column=1, sticky="w", **row_pad)
        ttk.Entry(video, textvariable=self.h_var, width=12)\
            .grid(row=1, column=1, padx=(124, 0), pady=6, sticky="w")

        # row 2 – fullscreen
        ttk.Checkbutton(
            video,
            text="Fullscreen  (exclusive fullscreen mode)",
            variable=self.fullscreen_var
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=6, pady=(6, 2))

        # row 3 – vsync
        ttk.Checkbutton(
            video,
            text="VSync  (synchronize frame output)",
            variable=self.vsync_var
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=6, pady=(6, 6))

        # ---------- SCALING ----------
        scaling = ttk.LabelFrame(root, text="Scaling", padding=(14, 10))
        scaling.pack(fill="x", **pad)
        scaling.columnconfigure(1, weight=1)

        ttk.Label(scaling, text="Render Scale  (internal upscaling)")\
            .grid(row=0, column=0, sticky="w", **row_pad)

        self.scale_var = tk.StringVar()
        ttk.Combobox(
            scaling,
            textvariable=self.scale_var,
            values=["720p (1x)", "2K (2x)", "4K (3x)"],
            state="readonly",
            width=25
        ).grid(row=0, column=1, sticky="w", **row_pad)

        ttk.Label(scaling, text="Anti-Aliasing  (edge smoothing)")\
            .grid(row=1, column=0, sticky="w", **row_pad)

        self.aa_type = tk.StringVar()
        ttk.Combobox(
            scaling,
            textvariable=self.aa_type,
            values=["none", "fxaa", "fxaa_extreme"],
            state="readonly",
            width=25
        ).grid(row=1, column=1, sticky="w", **row_pad)

        ttk.Label(scaling, text="Scaling Method  (post-process filter)")\
            .grid(row=2, column=0, sticky="w", **row_pad)

        self.scaling_method = tk.StringVar()
        ttk.Combobox(
            scaling,
            textvariable=self.scaling_method,
            values=["bilinear", "cas", "fsr"],
            state="readonly",
            width=25
        ).grid(row=2, column=1, sticky="w", **row_pad)


        # --- CAS SHARPEN ---
        ttk.Label(scaling, text="Sharpen Strength  (CAS amount)")\
            .grid(row=3, column=0, sticky="w", **row_pad)

        self.sharp_var = tk.DoubleVar()
        self.sharp_scale = ttk.Scale(
            scaling,
            from_=0.0,
            to=1.0,
            length=230,
            variable=self.sharp_var,
            orient="horizontal"
        )
        self.sharp_scale.grid(row=3, column=1, sticky="w", padx=6, pady=(10, 6))
        self.sharp_scale_grid = dict(row=3, column=1, sticky="w", padx=6, pady=(10, 6))
        self.sharp_scale.bind("<Button-1>", self.scale_click_to_position)
        self.sharp_scale.bind("<B1-Motion>", self.scale_click_to_position)


        # --- FSR SHARPNESS REDUCTION ---
        ttk.Label(scaling, text="FSR Sharpness Reduction  (lower = sharper)")\
            .grid(row=4, column=0, sticky="w", **row_pad)

        self.fsr_var = tk.DoubleVar()
        self.fsr_var.trace_add("write", self.on_fsr_changed)
        self.fsr_scale = ttk.Scale(
            scaling,
            from_=0.0,
            to=2.0,
            length=230,
            variable=self.fsr_var,
            orient="horizontal"
        )
        self.fsr_scale.grid(row=4, column=1, sticky="w", padx=6, pady=(10, 6))
        self.fsr_scale_grid = dict(row=4, column=1, sticky="w", padx=6, pady=(10, 6))
        self.fsr_scale.bind("<Button-1>", self.scale_click_to_position)
        self.fsr_scale.bind("<B1-Motion>", self.scale_click_to_position)


        self.sharp_scale.bind("<Button-1>", self.scale_click_to_position)
        self.sharp_scale.bind("<B1-Motion>", self.scale_click_to_position)
               
        # ---------- GENERAL ----------
        general = ttk.LabelFrame(root, text="General", padding=(14, 10))
        general.pack(fill="x", **pad)

        self.patch_var = tk.BooleanVar()
        self.license_var = tk.BooleanVar()
        self.dither_var = tk.BooleanVar() 

        ttk.Checkbutton(
            general,
            text="Apply patches  (game compatibility fixes)",
            variable=self.patch_var
        ).pack(anchor="w", padx=6, pady=6)

        ttk.Checkbutton(
            general,
            text="Enable XBLA full license  (unlock content)",
            variable=self.license_var
        ).pack(anchor="w", padx=6, pady=6)

        ttk.Checkbutton(
            general,
            text="Enable dithering  (reduce color banding)",
            variable=self.dither_var
        ).pack(anchor="w", padx=6, pady=6)

        # ---------- BUTTONS ----------
        btns = ttk.Frame(root)
        btns.pack(fill="x", pady=(5, 0))

        ttk.Button(btns, text="Save", command=self.save)\
            .pack(side="right", padx=16)
        ttk.Button(btns, text="Reset to Defaults", command=self.reset_defaults)\
            .pack(side="right", padx=10)

        self.scaling_method.trace_add("write", self.update_fsr_state)
        self.update_fsr_state()

    # ---------------- LOGIC ----------------
    def load_values(self):
        v = self.data.get("Video", {})
        g = self.data.get("GPU", {})
        d = self.data.get("Display", {})
        gen = self.data.get("General", {})
        cont = self.data.get("Content", {})

        self.res_var.set(
            RES_ENUM.get(v.get("internal_display_resolution", DEFAULTS["res_id"]))
        )
        self.w_var.set(str(v.get("internal_display_resolution_x", DEFAULTS["width"])))
        self.h_var.set(str(v.get("internal_display_resolution_y", DEFAULTS["height"])))

        # ✅ FULLSCREEN JE DISPLAY
        self.fullscreen_var.set(
            d.get("fullscreen", DEFAULTS["fullscreen"])
        )

        # ✅ VSYNC JE GPU
        self.vsync_var.set(
            g.get("vsync", DEFAULTS["vsync"])
        )

        self.scale_var.set(
            ["720p (1x)", "2K (2x)", "4K (3x)"][
                g.get("draw_resolution_scale_x", 1) - 1
            ]
        )

        method = d.get(
            "postprocess_scaling_and_sharpening",
            DEFAULTS["scaling_method"]
        )
        if method not in SCALING_VALUES:
            method = "bilinear"
        self.scaling_method.set(method)

        aa = d.get("postprocess_antialiasing", DEFAULTS["aa"])
        if aa not in AA_VALUES:
            aa = "none"
        self.aa_type.set(aa)

        self.fsr_var.set(
            float(
                d.get(
                    "postprocess_ffx_fsr_sharpness_reduction",
                    DEFAULTS["fsr_sharpen"]
                )
            )
        )

        self.sharp_var.set(
            d.get(
                "postprocess_ffx_cas_additional_sharpness",
                DEFAULTS["sharpen"]
            )
        )

        self.patch_var.set(gen.get("apply_patches", DEFAULTS["patches"]))
        self.license_var.set(cont.get("license_mask", 1) == 1)
        self.dither_var.set(d.get("postprocess_dithering", DEFAULTS["dithering"]))



    def reset_defaults(self):
        self.res_var.set(RES_ENUM[DEFAULTS["res_id"]])
        self.w_var.set(str(DEFAULTS["width"]))
        self.h_var.set(str(DEFAULTS["height"]))
        self.fullscreen_var.set(DEFAULTS["fullscreen"])
        self.vsync_var.set(DEFAULTS["vsync"])
        self.scale_var.set("720p (1x)")
        self.scaling_method.set(DEFAULTS["scaling_method"])
        self.aa_type.set(DEFAULTS["aa"])
        self.fsr_var.set(DEFAULTS["fsr_sharpen"])
        self.sharp_var.set(DEFAULTS["sharpen"])
        self.patch_var.set(DEFAULTS["patches"])
        self.license_var.set(DEFAULTS["license"])
        self.dither_var.set(DEFAULTS["dithering"])

    def save(self):
        try:
            w = int(self.w_var.get())
            h = int(self.h_var.get())
        except ValueError:
            messagebox.showerror("Error", "Width and Height must be numeric values.")
            return

        scale = {
            "720p (1x)": 1,
            "2K (2x)": 2,
            "4K (3x)": 3
        }[self.scale_var.get()]

        res_id = RES_ENUM_INV[self.res_var.get()]

        for path in self.paths:
            d = load_toml(path)
            d.setdefault("Video", {})
            d.setdefault("GPU", {})
            d.setdefault("Display", {})
            d.setdefault("General", {})
            d.setdefault("Content", {})

            d["Video"].update({
                "internal_display_resolution": res_id,
                "internal_display_resolution_x": w,
                "internal_display_resolution_y": h
            })

            # ✅ GPU = VSYNC + SCALE
            d["GPU"].update({
                "vsync": self.vsync_var.get(),
                "draw_resolution_scale_x": scale,
                "draw_resolution_scale_y": scale
            })

            # ✅ DISPLAY = FULLSCREEN + POSTPROCESS
            d["Display"].update({
                "fullscreen": self.fullscreen_var.get(),
                "postprocess_scaling_and_sharpening": self.scaling_method.get(),
                "postprocess_antialiasing": self.aa_type.get(),
                "postprocess_ffx_fsr_sharpness_reduction": self.fsr_var.get(),
                "postprocess_ffx_cas_additional_sharpness": self.sharp_var.get(),
                "postprocess_dithering": self.dither_var.get(),
            })

            d["General"]["apply_patches"] = self.patch_var.get()
            d["Content"]["license_mask"] = 1 if self.license_var.get() else 0

            save_toml(path, d)

        messagebox.showinfo("Saved", "Configuration saved successfully.")



    def on_res_change(self, _):
        if self.res_var.get() != "Custom":
            w, h = self.res_var.get().split("x")
            self.w_var.set(w)
            self.h_var.set(h)

    def scale_click_to_position(self, event):
        scale = event.widget

        x = event.x
        length = scale.winfo_width()

        min_val = float(scale.cget("from"))
        max_val = float(scale.cget("to"))

        ratio = max(0.0, min(1.0, x / length))
        value = min_val + (max_val - min_val) * ratio

        step = 0.01
        value = round(value / step) * step

        scale.set(value)
        return "break" 


    def scale_drag(self, event):
        scale = event.widget
        value = scale.get()

        step = 0.01
        value = round(value / step) * step

        scale.set(value)

    def on_fsr_changed(self, *_):
        value = round(self.fsr_var.get(), 3)
        print("FSR:", value)

    def update_fsr_state(self, *_):
        method = self.scaling_method.get()
        if method == "fsr":
            self.show_scale(self.fsr_scale, self.fsr_scale_grid)
            self.hide_scale(self.sharp_scale)

        elif method == "cas":
            self.show_scale(self.sharp_scale, self.sharp_scale_grid)
            self.hide_scale(self.fsr_scale)

        else:
            self.hide_scale(self.fsr_scale)
            self.hide_scale(self.sharp_scale)

    def hide_scale(self, scale):
        scale.grid_remove()

    def show_scale(self, scale, grid_info):
        scale.grid(**grid_info)


configs = find_config_files()
if not configs:
    messagebox.showerror(
        "Configuration not found",
        "No Xenia Canary configuration file was found.\n\n"
        "Make sure this tool is placed inside or near the Xenia Canary folder."
    )
    sys.exit(1)

active_config = select_nearest_config(configs)
XeniaConfigTool([active_config]).mainloop()
