import tkinter as tk
from tkinter import filedialog
import vlc
import time

class VLCPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 VLC Přehrávač (Tkinter) - opravený")
        self.root.geometry("600x180")

        # VLC instance s HW akcelerací vypnutou
        self.instance = vlc.Instance("--no-video-title-show", "--avcodec-hw=none")
        self.player = self.instance.media_player_new()

        # Ovládací tlačítka
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)

        self.open_btn = tk.Button(control_frame, text="🗂️ Otevřít", command=self.open_file)
        self.open_btn.pack(side=tk.LEFT, padx=5)

        self.play_btn = tk.Button(control_frame, text="▶️ Play", command=self.play_pause, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(control_frame, text="⏹️ Stop", command=self.stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Label aktuálního času nad sliderem
        self.current_time_label = tk.Label(self.root, text="00:00")
        self.current_time_label.pack()

        # Slider pozice
        self.slider = tk.Scale(self.root, from_=0, to=1000, orient=tk.HORIZONTAL, length=550, command=self.slider_seek)
        self.slider.pack(pady=5)
        self.slider.bind("<Button-1>", self.slider_click)
        self.slider.bind("<ButtonRelease-1>", self.slider_release)
        self.slider_enabled = False
        self.seeking = False

        # Label celkového času
        self.total_time_label = tk.Label(self.root, text="--:--")
        self.total_time_label.pack()

        # Timer aktualizace UI
        self.update_timer()

    def open_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Videa", "*.*")])
        if filepath:
            media = self.instance.media_new(filepath)
            self.player.set_media(media)
            self.player.play()
            time.sleep(0.1)  # nechat nabootovat
            self.play_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.NORMAL)
            self.slider_enabled = True
            self.play_btn.config(text="⏸️ Pauza")

    def play_pause(self):
        if self.player.is_playing():
            self.player.pause()
            self.play_btn.config(text="▶️ Pokračovat")
        else:
            self.player.play()
            self.play_btn.config(text="⏸️ Pauza")

    def stop(self):
        self.player.stop()
        self.slider.set(0)
        self.current_time_label.config(text="00:00")
        self.total_time_label.config(text="--:--")
        self.play_btn.config(text="▶️ Play")

    def slider_seek(self, val):
        if self.seeking and self.slider_enabled:
            pos = float(val) / 1000.0
            self.player.set_position(pos)

    def slider_click(self, event):
        self.seeking = True

    def slider_release(self, event):
        self.seeking = False
        pos = self.slider.get() / 1000.0
        self.player.set_position(pos)

    def update_timer(self):
        if self.slider_enabled and not self.seeking:
            length = self.player.get_length()
            current = self.player.get_time()

            if length > 0 and current >= 0:
                pos = current / length
                if pos < 0: pos = 0
                if pos > 1: pos = 1
                self.slider.set(int(pos * 1000))

                # Aktualizace času
                self.current_time_label.config(text=self.format_time(current // 1000))
                self.total_time_label.config(text=self.format_time(length // 1000))
            else:
                self.current_time_label.config(text="00:00")
                self.total_time_label.config(text="--:--")

        self.root.after(300, self.update_timer)

    def format_time(self, sec):
        m, s = divmod(sec, 60)
        return f"{int(m):02}:{int(s):02}"


if __name__ == "__main__":
    root = tk.Tk()
    player = VLCPlayer(root)
    root.mainloop()
