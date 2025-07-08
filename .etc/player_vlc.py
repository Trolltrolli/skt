import tkinter as tk
from tkinter import ttk, filedialog
import vlc
import platform

# --- RangeSlider: jedna lišta s dvěma markery (start/end) ---
class RangeSlider(tk.Canvas):
    def __init__(self, master, length=900, height=40, min_val=0, max_val=1000, start_val=0, end_val=1000, **kwargs):
        super().__init__(master, width=length, height=height, bg="#2d2d2d", highlightthickness=0, **kwargs)
        self.length = length
        self.height = height
        self.min_val = min_val
        self.max_val = max_val
        self.start_val = start_val
        self.end_val = end_val
        self.dragging = None
        self.marker_radius = 8
        self.line_y = height // 2
        self.bind("<Button-1>", self.click)
        self.bind("<B1-Motion>", self.drag)
        self.bind("<ButtonRelease-1>", self.release)
        self.draw()

    def val_to_pos(self, val):
        return (val - self.min_val) / (self.max_val - self.min_val) * self.length

    def pos_to_val(self, pos):
        val = self.min_val + (pos / self.length) * (self.max_val - self.min_val)
        return max(self.min_val, min(self.max_val, val))

    def draw(self):
        self.delete("all")
        # Hlavní lišta
        self.create_line(self.marker_radius, self.line_y, self.length - self.marker_radius, self.line_y, fill="#666", width=4)
        # Vybraná oblast
        start_x = self.val_to_pos(self.start_val)
        end_x = self.val_to_pos(self.end_val)
        self.create_rectangle(start_x, self.line_y - 6, end_x, self.line_y + 6, fill="#0055ff", outline="")
        # Markery
        self.create_oval(start_x - self.marker_radius, self.line_y - self.marker_radius, start_x + self.marker_radius, self.line_y + self.marker_radius, fill="green", outline="white", width=2, tags="start_marker")
        self.create_oval(end_x - self.marker_radius, self.line_y - self.marker_radius, end_x + self.marker_radius, self.line_y + self.marker_radius, fill="red", outline="white", width=2, tags="end_marker")

    def click(self, event):
        x = event.x
        start_x = self.val_to_pos(self.start_val)
        end_x = self.val_to_pos(self.end_val)
        if abs(x - start_x) < self.marker_radius * 2:
            self.dragging = "start"
        elif abs(x - end_x) < self.marker_radius * 2:
            self.dragging = "end"
        else:
            self.dragging = None

    def drag(self, event):
        if self.dragging is None:
            return
        x = max(self.marker_radius, min(event.x, self.length - self.marker_radius))
        val = self.pos_to_val(x)
        if self.dragging == "start":
            if val > self.end_val:
                val = self.end_val
            self.start_val = val
        elif self.dragging == "end":
            if val < self.start_val:
                val = self.start_val
            self.end_val = val
        self.draw()
        if self.dragging == "start":
            self.event_generate("<<StartChanged>>")
        elif self.dragging == "end":
            self.event_generate("<<EndChanged>>")

    def release(self, event):
        self.dragging = None

# --- TimeScale: časová osa s ticky a popisky ---
class TimeScale(tk.Canvas):
    def __init__(self, master, length=900, height=20, max_time=1000, **kwargs):
        super().__init__(master, width=length, height=height, bg="#2d2d2d", highlightthickness=0, **kwargs)
        self.length = length
        self.height = height
        self.max_time = max_time
        self.tick_height = 10
        self.font = ("Arial", 9)
        self.draw_ticks()

    def draw_ticks(self):
        self.delete("all")
        num_ticks = 11  # 0%, 10%, ..., 100%
        for i in range(num_ticks):
            x = i * (self.length / (num_ticks - 1))
            self.create_line(x, self.height, x, self.height - self.tick_height, fill="#888")
            time_sec = (i / (num_ticks - 1)) * self.max_time
            label = self.format_time(time_sec)
            self.create_text(x, self.height - self.tick_height - 10, text=label, fill="white", font=self.font)

    def update_max_time(self, max_time):
        self.max_time = max_time
        self.draw_ticks()

    def format_time(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m:02d}:{s:02d}"

# --- Hlavní okno ---
class VideoPlayer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DeOldify Video Colorizer - Demo")
        self.geometry("1050x650")
        self.configure(bg="#2d2d2d")

        # Styl pro tmavé prvky a decentní hover
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TButton', background='#444', foreground='white', borderwidth=1)
        style.map('TButton', background=[('active', '#555')])
        style.configure('TScale', troughcolor='#333', background='#666')
        style.map('TScale', background=[('active', '#444'), ('!active', '#666')])
        style.map('TScale', troughcolor=[('active', '#222'), ('!active', '#333')])
        style.configure('TRadiobutton', background='#2d2d2d', foreground='white')
        style.configure('TCheckbutton', background='#2d2d2d', foreground='white')
        style.configure('TLabel', background='#2d2d2d', foreground='white')

        # VLC player instance
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # Zmenšený video panel
        self.video_panel = tk.Frame(self, bg="black", width=600, height=300)
        self.video_panel.pack(pady=10)

        # Časová osa
        self.time_scale = TimeScale(self, length=900, height=20)
        self.time_scale.pack(padx=40, pady=(0, 0))

        # Exportní lišta s dvěma posuvníky (start/end) na jedné liště
        self.range_slider = RangeSlider(self, length=900, height=40)
        self.range_slider.pack(padx=40, pady=(0, 10))
        self.range_slider.bind("<<StartChanged>>", self.range_start_changed)
        self.range_slider.bind("<<EndChanged>>", self.range_end_changed)

        # Ovládací panel pod videem
        controls_frame = tk.Frame(self, bg="#2d2d2d")
        controls_frame.pack(fill=tk.X, padx=40, pady=0)

        self.play_button = ttk.Button(controls_frame, text="Play", command=self.play_pause)
        self.play_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(controls_frame, text="Stop", command=self.stop)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.position_slider = ttk.Scale(controls_frame, from_=0, to=1000, orient=tk.HORIZONTAL,
                                         command=self.set_position, length=900)
        self.position_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.position_slider.bind("<ButtonPress-1>", self.on_slider_press)
        self.position_slider.bind("<ButtonRelease-1>", self.on_slider_release)
        self.slider_dragging = False

        self.time_label = ttk.Label(controls_frame, text="00:00 / 00:00")
        self.time_label.pack(side=tk.LEFT, padx=5)

        # Extra ovládací panel
        extra_controls = tk.Frame(self, bg="#2d2d2d")
        extra_controls.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(extra_controls, text="Render Factor:", fg="white", bg="#2d2d2d", font=("Arial", 12), padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        self.render_slider = ttk.Scale(extra_controls, from_=1, to=30, orient=tk.HORIZONTAL)
        self.render_slider.set(16)
        self.render_slider.pack(side=tk.LEFT, padx=5)

        tk.Label(extra_controls, text="Saturation:", fg="white", bg="#2d2d2d", font=("Arial", 12), padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        self.saturation_slider = ttk.Scale(extra_controls, from_=10, to=30, orient=tk.HORIZONTAL)
        self.saturation_slider.set(15)
        self.saturation_slider.pack(side=tk.LEFT, padx=5)

        self.model_var = tk.StringVar(value="Video")
        for model in ["Artistic", "Stable", "Video"]:
            b = ttk.Radiobutton(extra_controls, text=model, variable=self.model_var, value=model)
            b.pack(side=tk.LEFT, padx=5)

        self.watermark_var = tk.BooleanVar()
        self.watermark_check = ttk.Checkbutton(extra_controls, text="Add Watermark", variable=self.watermark_var)
        self.watermark_check.pack(side=tk.LEFT, padx=5)

        # Export range label
        export_frame = tk.Frame(self, bg="#2d2d2d")
        export_frame.pack(fill=tk.X, padx=10, pady=10)
        self.export_label = ttk.Label(export_frame, text="Export Range: 00:00 - 00:00")
        self.export_label.pack(side=tk.LEFT, padx=10)

        # Akční tlačítka
        action_frame = tk.Frame(self, bg="#2d2d2d")
        action_frame.pack(fill=tk.X, padx=10, pady=10)

        self.load_button = ttk.Button(action_frame, text="Load Video", command=self.load_video)
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.colorize_button = ttk.Button(action_frame, text="Colorize", command=self.colorize_video, state=tk.DISABLED)
        self.colorize_button.pack(side=tk.LEFT, padx=5)

        # Srovnávací panel (originál vs. kolorované video)
        comparison_frame = tk.Frame(self, bg="#2d2d2d")
        comparison_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.original_panel = tk.Frame(comparison_frame, bg="black", width=320, height=180)
        self.original_panel.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)

        self.colorized_panel = tk.Frame(comparison_frame, bg="black", width=320, height=180)
        self.colorized_panel.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)

        # Timer update
        self.after_id = None

        # Nastavení výstupu VLC do panelu
        self._set_video_panel()

        # Exportní rozsahy v sekundách
        self.export_start_sec = 0
        self.export_end_sec = 0
        self.video_length = 0

    def _set_video_panel(self):
        self.update()
        if platform.system() == "Windows":
            self.player.set_hwnd(self.video_panel.winfo_id())
        elif platform.system() == "Linux":
            self.player.set_xwindow(self.video_panel.winfo_id())
        elif platform.system() == "Darwin":
            self.player.set_nsobject(self.video_panel.winfo_id())

    def play_pause(self):
        if self.player.is_playing():
            self.player.pause()
            self.play_button.config(text="Play")
        else:
            self.player.play()
            self.play_button.config(text="Pause")
            self.update_position()

    def stop(self):
        self.player.stop()
        self.play_button.config(text="Play")
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        self.position_slider.set(0)
        self.time_label.config(text="00:00 / 00:00")

    def set_position(self, val):
        if self.slider_dragging:
            return
        pos = float(val) / 1000.0
        self.player.set_position(pos)

    def on_slider_press(self, event):
        self.slider_dragging = True

    def on_slider_release(self, event):
        self.slider_dragging = False
        val = self.position_slider.get()
        pos = float(val) / 1000.0
        self.player.set_position(pos)

    def update_position(self):
        pos = self.player.get_position()
        self.video_length = self.player.get_length() / 1000
        if self.video_length > 0:
            if not self.slider_dragging:
                self.position_slider.set(pos * 1000)
            current_time = self._format_time(pos * self.video_length)
            total_time = self._format_time(self.video_length)
            self.time_label.config(text=f"{current_time} / {total_time}")

            # Aktualizace časové osy
            self.time_scale.update_max_time(self.video_length)

            # Synchronizace exportních posuvníků s délkou videa
            self.range_slider.min_val = 0
            self.range_slider.max_val = 1000
            if self.export_end_sec == 0 or self.export_end_sec > self.video_length:
                self.export_end_sec = self.video_length
                self.range_slider.end_val = 1000
            if self.export_start_sec < 0 or self.export_start_sec > self.export_end_sec:
                self.export_start_sec = 0
                self.range_slider.start_val = 0
            self.range_slider.draw()
            self._update_export_label()

        self.after_id = self.after(200, self.update_position)

    def _format_time(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m:02d}:{s:02d}"

    def load_video(self):
        filename = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mkv *.mov")])
        if filename:
            media = self.instance.media_new(filename)
            self.player.set_media(media)
            self.colorize_button.config(state=tk.NORMAL)
            self.export_start_sec = 0
            self.export_end_sec = 0
            self.range_slider.start_val = 0
            self.range_slider.end_val = 1000
            self.range_slider.draw()
            self.export_label.config(text="Export Range: 00:00 - 00:00")

    def colorize_video(self):
        print("Colorize clicked")
        # Tady napojíš vlastní funkci pro kolorování

    def range_start_changed(self, event=None):
        val = self.range_slider.start_val
        self.export_start_sec = (val / 1000) * self.video_length
        if self.export_start_sec > self.export_end_sec:
            self.export_start_sec = self.export_end_sec
            self.range_slider.start_val = (self.export_end_sec / self.video_length) * 1000
            self.range_slider.draw()
        self._update_export_label()

    def range_end_changed(self, event=None):
        val = self.range_slider.end_val
        self.export_end_sec = (val / 1000) * self.video_length
        if self.export_end_sec < self.export_start_sec:
            self.export_end_sec = self.export_start_sec
            self.range_slider.end_val = (self.export_start_sec / self.video_length) * 1000
            self.range_slider.draw()
        self._update_export_label()

    def _update_export_label(self):
        start = self._format_time(self.export_start_sec)
        end = self._format_time(self.export_end_sec)
        self.export_label.config(text=f"Export Range: {start} - {end}")

if __name__ == '__main__':
    app = VideoPlayer()
    app.mainloop()
