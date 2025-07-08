import tkinter as tk
from tkinter import filedialog, ttk
import vlc
import sys

class VideoPlayer:
    def __init__(self, root):
        self.root = root
        root.title("Čistý VLC přehrávač")
        root.geometry("800x600")

        # VLC instance
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # Panel pro video
        self.video_panel = tk.Frame(root, bg="black")
        self.video_panel.pack(fill=tk.BOTH, expand=1)

        # Posuvník pro přehrávání (ttk.Scale)
        self.progress = ttk.Scale(root, from_=0, to=1000, orient=tk.HORIZONTAL, length=600)
        self.progress.pack(pady=5)
        self.progress.bind("<ButtonPress-1>", self.on_drag_start)
        self.progress.bind("<ButtonRelease-1>", self.on_drag_end)
        self.slider_dragging = False

        # Label pro čas videa
        self.time_label = ttk.Label(root, text="00:00 / 00:00")
        self.time_label.pack()

        # Kontrolní tlačítka
        ctrl = tk.Frame(root)
        ctrl.pack(pady=10)
        tk.Button(ctrl, text="Open", command=self.open_file).pack(side="left", padx=5)
        tk.Button(ctrl, text="Play", command=self.play_video).pack(side="left", padx=5)
        tk.Button(ctrl, text="Pause", command=self.pause_video).pack(side="left", padx=5)
        tk.Button(ctrl, text="Stop", command=self.stop_video).pack(side="left", padx=5)

        self.update()

    def open_file(self):
        file = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mkv *.mov")])
        if file:
            media = self.instance.media_new(file)
            self.player.set_media(media)
            self.root.update()  # Zajistí, že panel má winfo_id
            if sys.platform.startswith("linux"):
                self.player.set_xwindow(self.video_panel.winfo_id())
            elif sys.platform == "win32":
                self.player.set_hwnd(self.video_panel.winfo_id())
            elif sys.platform == "darwin":
                self.player.set_nsobject(self.video_panel.winfo_id())
            self.player.stop()
            self.progress.set(0)
            self.time_label.config(text="00:00 / 00:00")
            self.player.play()

    def play_video(self):
        self.player.play()

    def pause_video(self):
        self.player.pause()

    def stop_video(self):
        self.player.stop()
        self.progress.set(0)
        self.time_label.config(text="00:00 / 00:00")

    def on_drag_start(self, event):
        self.slider_dragging = True

    def on_drag_end(self, event):
        self.slider_dragging = False
        length = self.player.get_length()
        pos = self.progress.get()
        # Ošetření, aby se slider nedostal mimo délku videa
        if length > 0:
            pos = min(max(0, pos), length)
            self.player.set_time(int(pos))

    def update(self):
        if not self.slider_dragging:
            time_ms = self.player.get_time()
            length = self.player.get_length()
            if length > 0:
                self.progress.config(to=length)
                # Ošetření, aby slider nikdy "nepřeskočil" mimo rozsah
                if 0 <= time_ms <= length:
                    self.progress.set(time_ms)
                self.time_label.config(text=f"{self.format_time(time_ms)} / {self.format_time(length)}")
            else:
                self.progress.set(0)
                self.time_label.config(text="00:00 / 00:00")
        self.root.after(100, self.update)  # Aktualizace každých 100 ms pro plynulost

    def format_time(self, ms):
        seconds = int(ms / 1000)
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

if __name__ == "__main__":
    root = tk.Tk()
    VideoPlayer(root)
    root.mainloop()
