# -*- coding: utf-8 -*-
# cspell: disable
import datetime, multiprocessing, sys, os, random, re, json, subprocess, time, base64, tempfile, time, requests, threading, queue, zipfile, io, time, urllib.request, configparser, winreg, shutil
from pathlib import Path
from PyQt6.QtGui import QFont, QFontMetrics, QColor, QPainter, QShortcut, QKeySequence, QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QRect, QPoint, QObject, QEvent
from PyQt6.QtWidgets import (QToolButton, QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit, QComboBox, QLabel, QMessageBox, QFileDialog, QProgressBar, QGroupBox, QGridLayout, QFrame, QScrollArea, QSpacerItem, QSizePolicy, QStylePainter, QStyleOptionProgressBar, QCheckBox, QSplashScreen)
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from PyQt6.QtWidgets import QStackedWidget
_SESSION_MANAGER = None

# ---------------------------------------------------------
# opravy:
# 1. zelené tlačítko pro spuštění stahování zrušit...
# 2. oprava - nastavení kvality videa
# 3. oprava - výběr prohlížeče pro cookies - asi ok
# 4. oprava - výběr výstupní složky - pro video ok, pro mp3 to bude složka music
# psaní + enter!!!
# při zdědění není url checknuté!!!
# jen vybrané se exportují
# multi vložení nezatrhne se poslední odkaz ??? jen někdy, nebo při větším počtu
# kill yt-dlp procesů při zavření aplikace
# 8. oprava - výběr kvality videa - defaultně 1080p
# 9. kontrola mrtvých částí kódu
# 11. zjistit, jestli funguje správný výběr prohlížeče pro cookies - asi ok
# 12. zjistit, jestli nechat ostatní formu stahování, jinou, než auto defaultní prohlížeč s cookies - asi ok
# 13. stop procesů - animace, apod

# -------------------------------
#   FIXED CONFIG & CONSTANTS
# -------------------------------

INI_TEMPLATE = """; ================================
;  ULTIMATE VIDEO DOWNLOADER - CONFIG
;  All settings explained below.
;  Lines starting with ';' are comments.
; ================================
;  APPLICATION SETTINGS
; ================================
[settings]

; Number of worker threads for parallel download/extraction tasks.
; Default: 4
max_threads = 4

; Browser override for cookie loading.
; Options: default / firefox / chrome / edge
browser = default

; If true, cookies will be harvested from the selected browser.
; Set to false to disable cookie loading for testing (faster startup).
harvest_cookies = true

; Enable or disable proxy usage.
; Must be true for proxy_url to apply.
use_proxy = false

; Proxy server URL (HTTP/HTTPS/SOCKS).
; Example: http://127.0.0.1:8080
proxy_url =

; Encoding method for output processing.
; Options:
;   auto - automatic behavior (recommended)
;   cpu  - force CPU encoding
;   gpu  - force GPU encoding
encoding_by = auto


; ================================
;  YT-DLP SETTINGS
; ================================
[yt-dlp]
; Automatically update yt-dlp executable on startup.
; Options: true / false
yt_dlp_update = true


; ================================
;  LOGGING SETTINGS
; ================================
[logging]
; Enable or disable application logging.
; Options: true / false
enabled = false

"""


SPINNER_FRAMES = ["▂▄▆▇▅","▃▄▆▇▆","▄▅▇█▆","▅▆█▇▅","▆▇▇█▄","▇█▇▆▄","█▇▆▅▄",
                  "▇▆▅▄▃","▆▅▄▃▂","▅▄▃▂▁","▄▃▂▁▂","▃▂▁▂▃","▂▁▂▃▄","▁▂▃▄▅",
                  "▂▃▄▅▆","▃▄▅▆▇","▄▅▆▇█","▅▆▇█▇","▆▇█▇▆","▇█▇▆▅","█▇▆▅▄",
                  "▇▆▅▄▃","▆▅▄▃▂","▅▄▃▂▁"]
SPINNER_INTERVAL = 150
def spinner_frame(i):return SPINNER_FRAMES[i % len(SPINNER_FRAMES)]

MAX_THREADS = 16
preferred_browsers = ["chrome", "edge", "firefox", "brave"]
BROWSERS = ["chrome", "firefox", "edge", "brave"]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
]
PROXY_LIST = [
    "http://103.187.168.109:80",
    "http://103.153.154.209:80",
    "http://190.61.88.147:8080",
]

YOUTUBE_CLIENTS = [
    "web",
    "android",
    "android_app",
    "ios",
    "tv",
    "mweb",
    "web;player_skip=config"
]

def get_app_real_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

APP_DIR = get_app_real_path()

def get_bin_dir():
    primary = os.path.join(APP_DIR, "bin")
    # Žádný fallback, žádné AppData
    try:
        os.makedirs(primary, exist_ok=True)
        testfile = os.path.join(primary, "_write_test.tmp")
        with open(testfile, "w") as f:
            f.write("ok")
        os.remove(testfile)
        return primary
    except:
        return primary

_SHOWN_COOKIES_OK = False
APP_DIR = get_app_real_path()
BIN_DIR = get_bin_dir()

def get_local_temp_dir():
    temp_dir = os.path.join(BIN_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

TEMP_DIR = get_local_temp_dir()
os.environ["TEMP"] = TEMP_DIR
os.environ["TMP"] = TEMP_DIR
LOG_FILE_PATH = os.path.join(APP_DIR, "log.txt")
YTDLP_PATH   = os.path.join(BIN_DIR, "yt-dlp.exe" if sys.platform == "win32" else "yt-dlp")
FFMPEG_PATH  = os.path.join(BIN_DIR, "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
FFPROBE_PATH = os.path.join(BIN_DIR, "ffprobe.exe" if sys.platform == "win32" else "ffprobe")

LAST_STRATEGY_PATH = os.path.join(BIN_DIR, "last_strategy.txt")
COOKIE_REFRESH_AGE_SECONDS = 60 * 60 * 24 * 7

def save_last_strategy(strategy_label: str):
    try:
        os.makedirs(os.path.dirname(LAST_STRATEGY_PATH), exist_ok=True)
        with open(LAST_STRATEGY_PATH, "w", encoding="utf-8") as f:
            f.write(strategy_label)
    except:
        pass

def load_last_strategy():
    try:
        if os.path.exists(LAST_STRATEGY_PATH):
            with open(LAST_STRATEGY_PATH, "r", encoding="utf-8") as f:
                return f.read().strip()
    except:
        pass
    return None

def choose_proxy():
    if not PROXY_LIST:
        return None
    return random.choice(PROXY_LIST)


def choose_user_agent():
    return random.choice(USER_AGENTS) if USER_AGENTS else "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

def netscape_has_auth_tokens(netscape_path: str) -> bool:
    if not os.path.exists(netscape_path):
        return False
    try:
        with open(netscape_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().lower()
            for token in ("sapisid", "__secure-1psid", "__secure-3psid", "sid", "hsid", "apisaid", "ssid"):
                if token in content:
                    return True
    except:
        return False
    return False

def detect_default_browser():
    import sys
    if sys.platform != "win32":
        return None

    import winreg

    reg_paths = [
        r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice",
        r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice",
    ]

    browser_map = {
        "chrome": "chrome",
        "firefox": "firefox",
        "edge": "edge",
        "microsoft": "edge",
        "brave": "brave",
        "opera": "opera",
        "vivaldi": "vivaldi"
    }

    for reg_path in reg_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                progid, _ = winreg.QueryValueEx(key, "ProgId")
                progid = progid.lower()
                for keyword, browser in browser_map.items():
                    if keyword in progid:
                        return browser
        except:
            continue

    return None

def export_default_browser_cookies(browser):
    print(f"[CookieExport] Export from browser: {browser}")

    json_path = _SESSION_MANAGER.cookie_json_path("default")
    txt_path  = _SESSION_MANAGER.cookie_netscape_path("default")

    # startupinfo + hide window
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    # smažeme staré cookies
    try:
        if os.path.exists(json_path):
            os.remove(json_path)
        if os.path.exists(txt_path):
            os.remove(txt_path)
    except:
        pass

    cmd = [
        YTDLP_PATH,
        "--cookies-from-browser", browser,
        "--cookies", txt_path,
        "--dump-json",
        "--simulate",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    ]

    print("[CookieExport] Running export...")

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=creationflags,   # 🔥 skryje okno
            startupinfo=startupinfo,       # 🔥 skryje okno
            cwd=BIN_DIR                    # 🔥 žádné AppData
        )

        if os.path.exists(txt_path) and netscape_has_auth_tokens(txt_path):
            print(f"[CookieExport] OK -> {txt_path}")
            return True

        print("[CookieExport] Failed to create valid cookie file")
        return False

    except Exception as e:
        print(f"[CookieExport] Error: {e}")
        return False

def get_optimal_browser_for_cookies():
    default = detect_default_browser()
    if default:
        print(f"[BrowserDetect] Default browser: {default}")
        return default

    fallback_list = ["chrome", "edge", "firefox", "brave", "opera", "opera-gx"]

    for br in fallback_list:
        try:
            test = subprocess.run(
                [
                    YTDLP_PATH,
                    "--cookies-from-browser", br,
                    "--dump-json",
                    "--simulate",
                    "https://youtube.com/watch?v=dQw4w9WgXcQ"
                ],
                capture_output=True,
                text=True,
                timeout=6,
                cwd=BIN_DIR   # 🔥 DŮLEŽITÉ: ať si to nesahá do AppData
            )
            if test.returncode == 0 and "error" not in test.stderr.lower():
                print(f"[BrowserDetect] Fallback OK: {br}")
                return br
        except:
            continue

    print("[BrowserDetect] No usable browser found -> using firefox")
    return "firefox"

def try_cookies_from_browsers(url, browsers=None, timeout=10):
    if browsers is None:
        browsers = ["chrome", "edge", "firefox", "brave", "opera", "opera-gx"]

    startinfo = subprocess.STARTUPINFO()
    startinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    last_error = None

    for browser in browsers:
        cmd = [
            YTDLP_PATH,                # ← používáme tvůj YTDLP z BIN, ne systémový
            "--cookies-from-browser", browser,
            "--dump-json", url
        ]
        try:
            r = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=creationflags,
                startupinfo=startinfo,
                cwd=BIN_DIR                # ← aby si yt-dlp nehledal bordel v PATH
            )

            stderr = (r.stderr or "").lower()

            if r.returncode == 0 and "error" not in stderr and "confirm you're not a bot" not in stderr:
                print(f"✓ Cookies loaded from {browser}")
                save_last_strategy(f"browser:{browser}")
                return ["--cookies-from-browser", browser]

            last_error = stderr

        except Exception as e:
            last_error = str(e)

    print(f"⚠ No browser cookies worked (last: {str(last_error)[:200]})")
    return None

def build_cookie_strategy(url):
    strategies = []

    last = load_last_strategy()
    if last:
        if last.startswith("browser:"):
            br = last.split(":", 1)[1]
            strategies.append(["--cookies-from-browser", br])
        elif last.startswith("file:"):
            fname = last.split(":", 1)[1]
            strategies.append(["--cookies", fname])
        elif last.startswith("client:"):
            client = last.split(":", 1)[1]
            strategies.append(["--extractor-args", f"youtube:player_client={client}"])

    browser = get_optimal_browser_for_cookies()
    if browser:
        bstr = try_cookies_from_browsers(url, browsers=[browser])
        if bstr:
            strategies.append(bstr)

    bstr_all = try_cookies_from_browsers(url)
    if bstr_all and bstr_all not in strategies:
        strategies.append(bstr_all)

    netscape_txt = _SESSION_MANAGER.cookie_netscape_path("default")
    if os.path.exists(netscape_txt):
        age = time.time() - os.path.getmtime(netscape_txt)
        if age < COOKIE_REFRESH_AGE_SECONDS and netscape_has_auth_tokens(netscape_txt):
            strategies.append(["--cookies", netscape_txt])
            save_last_strategy(f"file:{netscape_txt}")
    for client in YOUTUBE_CLIENTS:
        strategies.append(["--extractor-args", f"youtube:player_client={client}"])

    strategies.append(["--no-cookies"])
    return strategies

def build_safe_cmd(base_cmd, url, *, use_proxy=False, cookie_session=None, timeout=20):
    ua = choose_user_agent()
    cmd_base = list(base_cmd)

    if use_proxy:
        proxy = choose_proxy()
        if proxy:
            cmd_base += ['--proxy', proxy]

    cmd_base += ['--user-agent', ua, '--no-check-certificate']

    if cookie_session:
        netscape_path = _SESSION_MANAGER.cookie_netscape_path(cookie_session)
        if os.path.exists(netscape_path) and netscape_has_auth_tokens(netscape_path):
            print(f"[SafeCmd] Using session cookies: {netscape_path}")
            save_last_strategy(f"file:{netscape_path}")
            return cmd_base + ['--cookies', netscape_path, url]

    strategies = build_cookie_strategy(url)
    last_exception = None
    for strat in strategies:
        test_cmd = cmd_base + strat + [url]
        try:
            r = subprocess.run(test_cmd, capture_output=True, text=True, timeout=timeout)
            stderr = (r.stderr or "").lower()
            if r.returncode == 0 and "confirm you're not a bot" not in stderr and "error" not in stderr:
                if strat[0] == "--cookies-from-browser":
                    save_last_strategy(f"browser:{strat[1]}")
                elif strat[0] == "--cookies":
                    save_last_strategy(f"file:{strat[1]}")
                elif strat[0] == "--extractor-args":
                    save_last_strategy(f"client:{strat[1].split('=',1)[1]}")
                print(f"✓ Strategy OK -> {strat}")
                return test_cmd
            last_exception = stderr
        except Exception as e:
            last_exception = str(e)

    print("[SafeCmd] All strategies failed -> trying browser export")
    default_browser = detect_default_browser() or "firefox"
    if export_default_browser_cookies(default_browser):
        netscape_txt = _SESSION_MANAGER.cookie_netscape_path("default")
        if os.path.exists(netscape_txt) and netscape_has_auth_tokens(netscape_txt):
            save_last_strategy(f"file:{netscape_txt}")
            return cmd_base + ['--cookies', netscape_txt, url]
    try:
        print("[SafeCmd] Starting login window...")
        _SESSION_MANAGER.create_session_for_youtube()
        netscape_txt = _SESSION_MANAGER.cookie_netscape_path("default")
        if os.path.exists(netscape_txt) and netscape_has_auth_tokens(netscape_txt):
            save_last_strategy(f"file:{netscape_txt}")
            return cmd_base + ['--cookies', netscape_txt, url]
    except Exception as e:
        print(f"[SafeCmd] Login error: {e}")

    print("[SafeCmd] Final fallback (no cookies)")
    return cmd_base + ['--no-cookies', url]

def build_yt_dlp_cmd(base_cmd_list, url, cookie_session='default', use_proxy=False):
    return build_safe_cmd(base_cmd_list, url, use_proxy=use_proxy, cookie_session=cookie_session)

def check_dependencies():
    bin_dir = BIN_DIR
    os.makedirs(bin_dir, exist_ok=True)

    yt_dlp_path = YTDLP_PATH
    ffmpeg_path = FFMPEG_PATH
    ffprobe_path = FFPROBE_PATH

    # --- startupinfo pro potlačení oken ---
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    except Exception:
        creation_flags = 0

    # --- zjistit, zda je update povolen ---
    try:
        allow_update = CONFIG.get_yt_dlp_update()
    except Exception:
        allow_update = True

    # -------------------------------
    # yt-dlp — exists?
    # -------------------------------
    if not os.path.exists(yt_dlp_path):
        print("[AutoFix] yt-dlp not found — downloading nightly build.")
        try:
            url = (
                "https://github.com/yt-dlp/yt-dlp-nightly-builds/releases/latest/download/yt-dlp.exe"
                if sys.platform == "win32"
                else "https://github.com/yt-dlp/yt-dlp-nightly-builds/releases/latest/download/yt-dlp"
            )

            tmp_path = os.path.join(TEMP_DIR, "yt-dlp.exe")

            urllib.request.urlretrieve(url, tmp_path)
            os.chmod(tmp_path, 0o755)
            shutil.move(tmp_path, yt_dlp_path)

            print("[AutoFix] yt-dlp downloaded successfully.")

        except Exception as e:
            print(f"[AutoFix] Failed to download yt-dlp: {e}")
            return "yt-dlp"

    # -------------------------------
    # test yt-dlp (POUZE pokud update povolen)
    # -------------------------------
    if allow_update:
        try:
            subprocess.run(
                [yt_dlp_path, "--version"],
                check=True,
                capture_output=True,
                creationflags=creation_flags,
                startupinfo=startupinfo,
                cwd=bin_dir
            )
        except Exception:
            print("[AutoFix] yt-dlp failed to execute.")
            return "yt-dlp"

    # -------------------------------
    # test ffprobe
    # -------------------------------
    try:
        subprocess.run(
            [ffprobe_path, "-version"],
            check=True,
            capture_output=True,
            creationflags=creation_flags,
            startupinfo=startupinfo,
            cwd=bin_dir
        )
    except Exception:
        print("[AutoFix] FFprobe failed to execute.")
        return "ffprobe"

    return None

def check_gpu_support():
    bindir = BIN_DIR
    ffmpeg_path = FFMPEG_PATH

    # --- startupinfo pro potlačení oken ---
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    except AttributeError:
        creationflags = 0

    gpu_candidates = [
        ("nvenc", ("h264_nvenc", "hevc_nvenc"), "NVIDIA"),
        ("amf", ("h264_amf", "hevc_amf"), "AMD"),
        ("qsv", ("h264_qsv", "hevc_qsv"), "Intel QuickSync"),
        ("vaapi", ("h264_vaapi", "hevc_vaapi"), "Linux VAAPI"),
        ("videotoolbox", ("h264_videotoolbox", "hevc_videotoolbox"), "macOS VideoToolbox"),
    ]

    # --- zjistit seznam enkodérů ---
    try:
        res = subprocess.run(
            [ffmpeg_path, "-hide_banner", "-encoders"],
            capture_output=True, text=True, check=True,
            creationflags=creationflags,
            startupinfo=startupinfo,
            cwd=bindir
        )
        encoders_out = res.stdout.lower()
    except Exception as e:
        print(f"[GPU] Unable to run ffmpeg -encoders ({e}) → CPU mode.")
        return "cpu", "libx264"

    print("[GPU] Detecting available encoders...")

    # --- test jednotlivých GPU kodérů ---
    for mode, names, friendly_name in gpu_candidates:
        for name in names:
            if name in encoders_out:
                print(f"[GPU] Encoder {name} found ({friendly_name}), testing...")
                test_cmd = [
                    ffmpeg_path, "-hide_banner", "-loglevel", "error",
                    "-f", "lavfi", "-i", "testsrc=size=192x108:rate=1",
                    "-t", "1", "-c:v", name, "-f", "null", "-"
                ]
                try:
                    test_proc = subprocess.run(
                        test_cmd,
                        capture_output=True, text=True,
                        creationflags=creationflags,
                        startupinfo=startupinfo,
                        cwd=bindir,
                        timeout=8
                    )
                    if test_proc.returncode == 0:
                        print(f"[GPU] OK → {friendly_name} ({name}) is working...")
                        return mode, name
                    else:
                        print(f"[GPU] {friendly_name} ({name}) failed during test...")
                except subprocess.TimeoutExpired:
                    print(f"[GPU] {friendly_name} ({name}) test timed out.")
                except Exception as e:
                    print(f"[GPU] {friendly_name} ({name}) test error: {e}")

    print("[GPU] No working GPU encoder found → CPU (libx264).")
    return "cpu", "libx264"

def get_unique_filepath(filepath):
    if not os.path.exists(filepath):
        return filepath
    path_obj = Path(filepath)
    directory = path_obj.parent
    filename = path_obj.stem
    extension = path_obj.suffix
    counter = 1
    while True:
        new_filename = f"{filename} ({counter}){extension}"
        new_filepath = directory / new_filename
        if not os.path.exists(new_filepath):
            return str(new_filepath)
        counter += 1

def get_original_bitrate(video_path):
    ffprobe_path = FFPROBE_PATH
    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

        cmd = [
            ffprobe_path, '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=bit_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',
            errors='replace',
            creationflags=creation_flags
        )

        bitrate_bps = int(result.stdout.strip())
        return round(bitrate_bps / 1_000_000, 1)

    except Exception:
        return 5.0

def get_video_dimensions(video_path):
    ffprobe_path = FFPROBE_PATH
    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

        cmd = [
            ffprobe_path, '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0:s=x',
            video_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',
            errors='replace',
            creationflags=creation_flags
        )

        w, h = result.stdout.strip().split('x')
        return int(w), int(h)
    except Exception:
        return 640, 360

def calculate_quality_params(compression_preset, original_audio_bitrate, encoder='libx264'):
    is_gpu = any(x in encoder for x in ['nvenc', 'qsv', 'amf'])
    compression_map = {
        "Very High Quality low compression": {"crf": 10, "audio_target_kbps": 192},
        "High Quality Compressed":           {"crf": 21, "audio_target_kbps": 160},
        "Medium Quality":                    {"crf": 24, "audio_target_kbps": 128},
        "Low Quality":                       {"crf": 28, "audio_target_kbps": 96},
        "Very Low Quality":                  {"crf": 32, "audio_target_kbps": 64},
    }
    preset_settings = compression_map.get(compression_preset, compression_map["Medium Quality"])  
    video_crf = preset_settings['crf']
    audio_target = preset_settings['audio_target_kbps']
    audio_bitrate_kbps = min(original_audio_bitrate, audio_target)
    if is_gpu:
        video_crf = max(15, video_crf - 2)
    return video_crf, audio_bitrate_kbps

def calculate_quality(compression_preset, original_audio_bitrate, encoder="libx264"):
    gpu = any(x in encoder for x in ["nvenc", "qsv", "amf"])
    
    compression_map = {
        "Very High Quality": {"crf": 18, "audio_target": 320},
        "High Quality (Compressed)": {"crf": 21, "audio_target": 256},
        "Medium Quality": {"crf": 24, "audio_target": 128},
        "Low Quality": {"crf": 28, "audio_target": 96},
        "Very Low Quality": {"crf": 32, "audio_target": 64},
    }
    preset_conf = compression_map.get(compression_preset, compression_map["Medium Quality"])
    crf = preset_conf["crf"]
    audio_target = preset_conf["audio_target"]
    if original_audio_bitrate < audio_target:
        audio_bitrate = original_audio_bitrate
    else:
        audio_bitrate = audio_target
    if gpu:
        crf = max(15, crf - 2)
    return crf, audio_bitrate

def get_audio_bitrate(video_path):
    ffprobe_path = FFPROBE_PATH
    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

        cmd = [
            ffprobe_path, '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=bit_rate',
            '-of', 'default=nw=1:nk=1',
            video_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',
            errors='replace',
            creationflags=creation_flags
        )

        br = result.stdout.strip()
        return int(int(br) / 1000) if br.isdigit() else 128

    except Exception:
        return 128

def canonicalize_youtube_url(url: str) -> str:
    if not url:
        return url
    url = url.strip()
    m = re.search(r'(?:v=|\/youtu\.be\/|\/embed\/)([A-Za-z0-9_-]{11})', url)
    if m:
        return f"https://www.youtube.com/watch?v={m.group(1)}"
    q = re.search(r'[?&]v=([A-Za-z0-9_-]{11})', url)
    if q:
        return f"https://www.youtube.com/watch?v={q.group(1)}"
    return url

def is_supported_url(url: str) -> bool:
    if not url:
        return False
    u = url.strip().lower()
    valid_prefixes = (
        "https://www.youtube.com/", "http://www.youtube.com/",
        "https://youtube.com/", "http://youtube.com/",
        "https://youtu.be/", "http://youtu.be/",
        "https://www.facebook.com/", "http://www.facebook.com/",
        "https://facebook.com/", "http://facebook.com/",
        "https://fb.watch/", "http://fb.watch/"
    )
    return any(u.startswith(p) for p in valid_prefixes)

def is_youtube_url(url: str) -> bool:
    if not url:
        return False
    u = url.strip().lower()
    return (
        u.startswith("https://www.youtube.com/") or
        u.startswith("http://www.youtube.com/")  or
        u.startswith("https://youtube.com/")     or
        u.startswith("http://youtube.com/")      or
        u.startswith("https://youtu.be/")        or
        u.startswith("http://youtu.be/")
    )

def normalize_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    return canonicalize_youtube_url(url) if is_youtube_url(url) else url

def normalize_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    return canonicalize_youtube_url(url) if is_youtube_url(url) else url

def dbg(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[YTDBG {ts}] {msg}"
    print(line, flush=True)

def get_unique_filepath(path: str) -> str:
    base, ext = os.path.splitext(path)
    if ext == ".mp4.webm":
        ext = ".mp4"
    path = base + ext
    if not os.path.exists(path):
        return path
    i = 1
    while True:
        candidate = f"{base}({i}){ext}"
        if not os.path.exists(candidate):
            return candidate
        i += 1

def choose_default_quality(available, target="1080p"):
    try:
        target_val = int(target[:-1])
    except:
        target_val = 1080
    nums = sorted(
        [int(r[:-1]) for r in available if r.endswith("p") and r[:-1].isdigit()],
        reverse=True
    )
    if target_val in nums:
        return f"{target_val}p"
    lower = [n for n in nums if n < target_val]
    if lower:
        return f"{max(lower)}p"
    return f"{min(nums)}p" if nums else target

def show_download_error_message(parent, original_error=""):
    title = "Action Failed"
    message = (
        "Oops! Something went wrong.\n\n"
        "Here are a few things you can try to fix it:\n\n"
        "1.  **Enable yt-dlp Update:** Open the configuration file `conf.ini` and set `yt_dlp_update = true` under the [yt-dlp] section, then restart the application.\n\n"
        "2.  **Browser Login:** Log in to your YouTube/Google account in your default web browser. This can help with age-restricted or private videos.\n\n"
        "3.  **Check the URL:** Double-check that the video URL is correct and the video is publicly available.\n\n"
        "4.  **Reset Config:** As a last resort, you can delete the `conf.ini` file (while the app is closed) to reset all settings to their defaults.\n\n"
        "Also, ensure your internet connection is stable."
    )
    QMessageBox.warning(parent, title, message)

# =====================
#  log_system  
# =====================
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
LOG_FILE_PATH = os.path.join(BASE_DIR, "log.txt")
MAX_LOG_SIZE = 5_000_000  

def rotate_log_if_needed():
    """Pokud je log.txt větší než MAX_LOG_SIZE → přesune se do log.old.txt"""
    try:
        if os.path.exists(LOG_FILE_PATH):
            size = os.path.getsize(LOG_FILE_PATH)
            if size >= MAX_LOG_SIZE:
                old_path = LOG_FILE_PATH + ".old"
                if os.path.exists(old_path):
                    os.remove(old_path)
                os.rename(LOG_FILE_PATH, old_path)
    except:
        pass

def safe_log(text: str):
    """Zapisuje text do log.txt + provádí rotaci, pokud je log velký."""
    try:
        rotate_log_if_needed()
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except:
        pass
_original_print = print

def print(*args, **kwargs):
    """Přepis print() → zapisuje do log.txt a volá originální print."""
    try:
        msg = " ".join(str(a) for a in args)
    except:
        msg = "<print_error>"

    safe_log(msg)

    try:
        _original_print(*args, **kwargs)
    except:
        pass

def log(message: str):
    """Log funkce s timestampem."""
    ts = time.strftime("%H:%M:%S")
    line = f"[LOG {ts}] {message}"
    safe_log(line)
    try:
        _original_print(line)
    except:
        pass

def enable_logging():
    if getattr(enable_logging, "_already", False):
        return
    enable_logging._already = True
    log("--- LOG STARTED ---")

def disable_logging():
    log("--- LOG STOPPED ---")

class ConfigManager:
    def __init__(self, filepath='conf.ini'):
        self.filepath = filepath
        self.config = configparser.ConfigParser()
        self._load_or_create()

    def _load_or_create(self):
        if os.path.exists(self.filepath):
            self.config.read(self.filepath, encoding='utf-8')
        else:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(INI_TEMPLATE.strip() + "\n")
            return
        if 'yt-dlp' not in self.config:
            self.config['yt-dlp'] = {'yt_dlp_update': 'true'}
        elif 'yt_dlp_update' not in self.config['yt-dlp']:
            self.config['yt-dlp']['yt_dlp_update'] = 'true'
        if 'logging' not in self.config:
            self.config['logging'] = {'enabled': 'false'}
        elif 'enabled' not in self.config['logging']:
            self.config['logging']['enabled'] = 'false'
        else:
            val = self.config['logging']['enabled'].strip().lower()
            if val not in ('true', 'false'):
                self.config['logging']['enabled'] = 'false'
        if 'settings' not in self.config:
            self.config['settings'] = {}
        defaults = {
            'max_threads': '4',
            'browser': 'default',
            'harvest_cookies': 'false',
            'use_proxy': 'false',
            'proxy_url': '',
            'encoding_by': 'auto'
        }
        for key, val in defaults.items():
            if key not in self.config['settings']:
                self.config['settings'][key] = val
            else:
                current = self.config['settings'][key].strip().lower()

                if key in ('harvest_cookies', 'use_proxy'):
                    if current not in ('true', 'false'):
                        self.config['settings'][key] = 'false'

                elif key == 'encoding_by':
                    if current not in ('auto', 'cpu', 'gpu'):
                        self.config['settings'][key] = 'auto'

    def get_yt_dlp_update(self):
        return self.config.getboolean('yt-dlp', 'yt_dlp_update', fallback=True)

    def set_yt_dlp_update(self, value: bool):
        if 'yt-dlp' not in self.config:
            self.config['yt-dlp'] = {}
        self.config['yt-dlp']['yt_dlp_update'] = 'true' if value else 'false'

    def get_logging_enabled(self) -> bool:
        try:
            self.config.read(self.filepath, encoding='utf-8')
            return self.config.getboolean('logging', 'enabled', fallback=False)
        except Exception:
            return False

    def set_logging_enabled(self, value: bool):
        new_value = 'true' if value else 'false'
        with open(self.filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        new_lines = []
        in_logging_section = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                in_logging_section = (stripped.lower() == "[logging]")
                new_lines.append(line)
                continue
            if in_logging_section and stripped.lower().startswith("enabled"):
                new_lines.append(f"enabled = {new_value}\n")
            else:
                new_lines.append(line)
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        self.config.read(self.filepath, encoding='utf-8')

class SplashWidget(QWidget):
    def __init__(self, text="YouTube Downloader starting..."):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        label = QLabel(text, self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setStyleSheet("""QWidget { background: rgba(0,0,0,.5); border: 1px solid grey; border-radius: 10px; color: #e8f0ff; font-size: 18px; font-weight: 600; padding: 15px;}""")
        self.resize(320, 80)
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.center() - self.rect().center())

class DownloadManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=MAX_THREADS)
        self.ytdlppath = YTDLP_PATH
        self.active_downloads = {}

    def download(self, urls, params):
        futures = [self.executor.submit(self._download_single, url, params) for url in urls]
        for future in futures:
            future.add_done_callback(self._handle_download_done)

    def _download_single(self, url, params):
        try:
            quality = params.get('video_quality', '1080p') 
            m = re.search(r'(\d+)', quality or '')
            h = m.group(1) if m else '1080'
            format_selector = (
                f"bv*[height<={h}][vcodec^=av01]+ba/"
                f"bv*[height<={h}][vcodec^=vp9]+ba/"
                f"bv*[height<={h}][ext=mp4]+ba/"
                f"bv*[height<={h}]+ba/"
                f"best"
            )
            output_path = get_unique_filepath(params['output_path'])
            session_name = params.get('cookie_session', 'default')
            cmd = build_safe_cmd(
                [self.ytdlppath, '-f', format_selector, '-o', output_path], 
                url, 
                cookie_session=session_name
            )
            if params.get('playlist', False):
                cmd += ['--yes-playlist']
            subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            return True
        except Exception as e:
            raise RuntimeError(f"Download failed for {url}: {str(e)}")

    def _handle_download_done(self, future):
        try:
            result = future.result()
            print(f"Download complete: {result}")
        except Exception as e:
            print(f"Download error: {e}")

    def cancel(self):
        if not self._is_cancelled:
            self._is_cancelled = True
            try:
                if self.process and self.process.poll() is None:
                    self.process.terminate()
            finally:
                QTimer.singleShot(50, lambda: self.error.emit("Cancelled"))

def _extract_yt_initial_data_from_html(html):
    import re
    m = re.search(r"var ytInitialData = (\{.*?\});", html, re.DOTALL)
    if not m:
        m = re.search(r"window\[['\"]ytInitialData['\"]\]\s*=\s*(\{.*?\});", html, re.DOTALL)
    if not m:
        m = re.search(r"ytInitialData\s*=\s*(\{.*?\});", html, re.DOTALL)
    if not m:
        return None
    txt = m.group(1)
    try:
        return json.loads(txt)
    except Exception:
        try:
            txt2 = txt.replace("undefined", "null")
            return json.loads(txt2)
        except Exception:
            return None

def _find_playlist_panel_videos(initial):
    videos = []
    def walk(node):
        if isinstance(node, dict):
            if node.get('videoId'):
                videos.append({'id': node.get('videoId'), 'title': node.get('title', {}).get('simpleText') if node.get('title') else None})
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for i in node:
                walk(i)
    walk(initial)
    seen = set()
    out = []
    for v in videos:
        if v['id'] and v['id'] not in seen:
            seen.add(v['id'])
            out.append(v)
    return out

def _find_playlist_panel_title(initial):
    def walk_for_title(node):
        if isinstance(node, dict):
            if 'title' in node and isinstance(node['title'], dict) and 'simpleText' in node['title']:
                return node['title']['simpleText']
            for v in node.values():
                t = walk_for_title(v)
                if t:
                    return t
        elif isinstance(node, list):
            for i in node:
                t = walk_for_title(i)
                if t:
                    return t
        return None
    return walk_for_title(initial)

def _scrape_radio_playlist(url, *, timeout=12):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
    except Exception:
        resp = None
    initial = None
    if resp and resp.status_code == 200:
        initial = _extract_yt_initial_data_from_html(resp.text)
    if not initial:
        session_name = "radio"
        try:
            _SESSION_MANAGER.create_session_for_youtube(
                name=session_name,
                headless=False,
                interactive=True
            )
        except Exception:
            pass
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                page.goto(url, wait_until='networkidle', timeout=15000)
                page.wait_for_timeout(1500)
                html = page.content()
                browser.close()
                initial = _extract_yt_initial_data_from_html(html)
        except Exception:
            initial = None
    if not initial:
        try:
            cmd = build_safe_cmd(
                ['yt-dlp', '--flat-playlist', '--dump-json'],
                url,
                cookie_session='radio'
            )
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            lines = [l for l in proc.stdout.splitlines() if l.strip()]
            vids = []

            for ln in lines:
                try:
                    j = json.loads(ln)
                    if 'id' in j:
                        vids.append({'id': j['id'], 'title': j.get('title')})
                except Exception:
                    continue
            urls = [f"https://www.youtube.com/watch?v={v['id']}" for v in vids]
            title = f"Radio/Mix ({len(urls)} items)"
            return {'title': title, 'urls': urls, 'entries': vids}

        except Exception:
            raise RuntimeError("ytInitialData not found and fallbacks failed")
    videos = _find_playlist_panel_videos(initial)
    title = _find_playlist_panel_title(initial) or f"Radio/Mix ({len(videos)} items)"
    if title:
        low = title.lower()
        if any(x in low for x in (
            "like this video", "líbí se vám", "magst du dieses",
            "vous aimez cette", "te gusta este", "ti piace questo",
            "gosta deste vídeo"
        )):
            title = f"Radio/Mix ({len(videos)} items)"
    urls = [f"https://www.youtube.com/watch?v={v['id']}" for v in videos]
    entries = [{'id': v['id'], 'title': v.get('title')} for v in videos]
    return {'title': title, 'urls': urls, 'entries': entries}

class SessionManager:
    
    def __init__(self, base_dir=None):
        if base_dir:
            self.base_dir = base_dir
        else:
            self.base_dir = BIN_DIR
        try:
            os.makedirs(self.base_dir, exist_ok=True)
        except Exception:
            pass
        try:
            default_json = self.cookie_json_path("default")
            default_txt = self.cookie_netscape_path("default")
            if not os.path.exists(default_json):
                fd, tmp = tempfile.mkstemp(
                    prefix="cookies_", suffix=".json",
                    dir=os.path.dirname(default_json)
                )
                os.close(fd)
                try:
                    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
                        json.dump([], f, ensure_ascii=False, indent=2)
                    os.replace(tmp, default_json)
                finally:
                    if os.path.exists(tmp):
                        try:
                            os.remove(tmp)
                        except Exception:
                            pass
            if not os.path.exists(default_txt):
                try:
                    with open(default_txt, "w", encoding="utf-8") as f:
                        f.write("# Netscape HTTP Cookie File\n")
                except Exception:
                    pass
        except Exception:
            pass

    def cookie_json_path(self, name="default"):
        return os.path.join(self.base_dir, f"cookies_{name}.json")

    def cookie_netscape_path(self, name="default"):
        return os.path.join(self.base_dir, f"cookies_{name}.txt")

    def has_cookie(self, name="default"):
        return os.path.exists(self.cookie_json_path(name))

    def save_cookies_json(self, cookies, name="default"):
        safe_list = []
        for c in (cookies or []):
            raw_val = c.get("value") or ""
            value_b64 = base64.b64encode(raw_val.encode("utf-8")).decode("ascii")
            safe_list.append({
                "name": c.get("name") or "",
                "value_b64": value_b64,
                "domain": c.get("domain") or "",
                "path": c.get("path", "/"),
                "expires": int(c.get("expires", 0)) if c.get("expires") else 0,
                "secure": bool(c.get("secure", False)),
                "httpOnly": bool(c.get("httpOnly", False)),
            })
        json_path = self.cookie_json_path(name)
        txt_path = self.cookie_netscape_path(name)
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(safe_list, f, ensure_ascii=False, indent=2)
        self._write_netscape(cookies, txt_path)
        return json_path

    def _write_netscape(self, cookies, netscape_path):
        os.makedirs(os.path.dirname(netscape_path), exist_ok=True)
        with open(netscape_path, "w", encoding="utf-8") as f:
            f.write("# Netscape HTTP Cookie File\n")
            for c in (cookies or []):
                domain = c.get("domain", "")
                flag = "TRUE" if domain.startswith(".") else "FALSE"
                path = c.get("path", "/")
                secure = "TRUE" if c.get("secure", False) else "FALSE"
                expires = str(int(c.get("expires", 0))) if c.get("expires") else "0"
                name = c.get("name", "")
                value = c.get("value", "")
                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")

    def create_session_for_youtube(self, name="default", headless=False, interactive=True): # CO TO JE?
        try:
            from playwright.sync_api import sync_playwright
            from playwright_stealth import stealth_sync
        except Exception:
            print("[SessionManager] Playwright není dostupný.")
            return self.save_cookies_json([], name)

        profile_dir = os.path.join(self.base_dir, f"profile_{name}")
        os.makedirs(profile_dir, exist_ok=True)
        cookies_collected = []
        with sync_playwright() as p:
            chromium = p.chromium
            context = chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                headless=False,
                ignore_default_args=["--enable-automation"],
                viewport={"width": 1400, "height": 900},
            )
            page = context.new_page()
            stealth_sync(page)
            print("[SessionManager] Otevírám YouTube...")
            try:
                page.goto("https://www.youtube.com/", wait_until="domcontentloaded", timeout=20000)
            except Exception:
                print("[SessionManager] YouTube se nepodařilo načíst.")
                context.close()
                return self.save_cookies_json([], name)

            print("\n[LOGIN] Přihlaš se do YouTube/Google v otevřeném okně.")
            print("[LOGIN] Až budeš přihlášen, stiskni Enter v konzoli...")
            input(">>> ")
            try:
                cookies = context.cookies()
                cookies_collected = [
                    c for c in cookies
                    if "youtube.com" in c["domain"] or "google.com" in c["domain"]
                ]
            except Exception:
                cookies_collected = []

            print(f"[LOGIN] Načteno {len(cookies_collected)} cookies.")
            context.close()
        return self.save_cookies_json(cookies_collected, name)

# ----------------------
class MetadataManager(QThread):
    resolutions_fetched = pyqtSignal(str, object)
    error = pyqtSignal(str, str)
    status_update = pyqtSignal(str, str) 

    def __init__(self):
        super().__init__()
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self.cache = {}
        self._current_url = None
        self._current_process = None
        self._cancelled = set()
        self._processes = {} 
        self._queue_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=MAX_THREADS)
        self._queued = set()
        self.yt_dlp_path = YTDLP_PATH
        try:
            self.creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        except Exception:
            self.creation_flags = 0
        self.start()
        self.cookie_path = _SESSION_MANAGER.cookie_netscape_path("default")
        global _SHOWN_COOKIES_OK
        if os.path.exists(self.cookie_path):
            if not _SHOWN_COOKIES_OK:
                print("[AutoFix] Using existing cookies file ✅")
                _SHOWN_COOKIES_OK = True
        else:
            print("[AutoFix] Cookie file missing (will rely on fallback strategies)")

    def run(self):
        while not self._stop_event.is_set():
            try:
                item = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if item is None:
                break
            if item in self._cancelled:
                self._cancelled.discard(item)
                self._queued.discard(item)
                continue
            url = item
            if url in self.cache:
                try:
                    self.resolutions_fetched.emit(url, self.cache[url])
                finally:
                    self._queued.discard(url)
                continue
            self._current_url = url
            future = self.executor.submit(self._fetch_metadata, url)
            future.add_done_callback(lambda f, u=url: self._handle_fetch_done(f, u))

    def request(self, urls):
        if isinstance(urls, str):
            urls = [urls]

        for url in urls:
            if not url:
                continue
            if not is_supported_url(url):
                try:
                    self.error.emit(url, "Unsupported URL.")
                except Exception:
                    pass
                continue

            if is_youtube_url(url) and ("list=RD" in url or "start_radio=1" in url):
                base = canonicalize_youtube_url(url)
                m = re.search(r"v=([A-Za-z0-9_-]{11})", base)
                if m:
                    vid = m.group(1)
                    norm = f"https://www.youtube.com/watch?v={vid}&list=RD{vid}"
                else:
                    sep = '&' if '?' in base else '?'
                    norm = f"{base}{sep}list=RD"
            else:
                norm = normalize_url(url)

            if norm in self._cancelled:
                self._cancelled.discard(norm)

            if norm in self.cache:
                try:
                    self.resolutions_fetched.emit(norm, self.cache[norm])
                except Exception:
                    pass
                continue

            if norm == self._current_url or norm in self._queued:
                continue
            with self._queue_lock:
                self._queue.put(norm)
                self._queued.add(norm)

    def _fetch_metadata(self, url):
        cookie_file = getattr(self, "cookie_path", "")
        has_cookie_file = os.path.exists(cookie_file)

        if "list=RD" in url or "start_radio=1" in url:
            print(f"[MetadataManager] Forcing radio-only fetch for {url}")
            self.status_update.emit(url, "Loading radio mix info...")
            try:
                try:
                    scraped = _scrape_radio_playlist(url)
                except Exception as scrap_e:
                    scraped = None
                    print(f"[RadioScrape] Failed: {scrap_e}")

                if scraped and scraped.get("urls"):
                    data = {
                        "is_playlist": True,
                        "is_radio_playlist": True,
                        "entries": scraped.get("entries", []),
                        "urls": scraped.get("urls", []),
                        "title": scraped.get(
                            "title",
                            f"Radio/Mix playlist ({len(scraped.get('urls', []))} items)"
                        )
                    }
                    if not data["urls"] or len(data["urls"]) <= 1:
                        print("[META] Ignoring fake RD placeholder (no valid URLs)")
                        raise RuntimeError("Fake RD placeholder ignored")
                    self.cache[url] = data
                    return data

                cmd = [
                    self.yt_dlp_path, "--flat-playlist", "--dump-json",
                    "--force-ipv4", "--geo-bypass", url
                ]
                print(f"[MetadataManager] Running (radio flat): {' '.join(cmd)}")

                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, encoding="utf-8", errors="replace",
                    creationflags=self.creation_flags
                )
                stdout, stderr = process.communicate(timeout=60)
                if not stdout.strip():
                    raise RuntimeError(f"No playlist data (stderr: {stderr})")

                items = [
                    json.loads(line)
                    for line in stdout.splitlines() if line.strip()
                ]
                video_urls = [
                    f"https://www.youtube.com/watch?v={it['id']}"
                    for it in items if "id" in it
                ]

                if len(video_urls) <= 1:
                    raise RuntimeError("Invalid RD playlist placeholder")

                data = {
                    "is_playlist": True,
                    "is_radio_playlist": True,
                    "entries": items,
                    "urls": video_urls,
                    "title": f"Radio/Mix playlist ({len(video_urls)} items)"
                }
                self.cache[url] = data
                return data

            except Exception as e:
                raise RuntimeError(f"Radio playlist fetch failed: {str(e)}")

        self.status_update.emit(url, "Loading video info...")
        strategies = [
            ("default", True, "Default (with cookies)"),
            ("web_safari", False, "Safari Client"),
            ("android", False, "Android Client"),
            ("ios", False, "iOS Client"),
            ("tv", False, "TV Client (anti-ban)"),
            ("web_embedded", False, "Embedded Client"),
            ("default", False, "Default (no cookies)"),
        ]

        last_error_message = "Unknown error"
        ban_markers = (
            "sign in", "captcha", "consent.youtube.com",
            "confirm you’re not a bot", "confirm you're not a bot",
            "too many requests", "http error 429"
        )

        for client, use_browser_cookies, log_name in strategies:
            time.sleep(random.uniform(0.4, 1.0))

            try:
                cmd = [
                    self.yt_dlp_path, "--dump-json", "--no-playlist",
                    "--user-agent", random.choice(USER_AGENTS),
                    "--force-ipv4", "--geo-bypass"
                ]
                cmd.extend(["--extractor-args", "youtube:player_client=default"])

                if client != "default":
                    cmd.extend(["--extractor-args", f"youtube:player_client={client}"])

                if has_cookie_file:
                    cmd.extend(["--cookies", cookie_file])
                elif use_browser_cookies:
                    for browser in BROWSERS:
                        cmd.extend(["--cookies-from-browser", browser])
                else:
                    cmd.append("--no-cookies")

                cmd.append(url)
                print(f"[MetadataManager] Running: {' '.join(cmd)}")

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )

                self._current_process = process
                stdout, stderr = process.communicate(timeout=70)


                if process.returncode != 0 or not stdout.strip():
                    raise RuntimeError(stderr or "yt-dlp returned no data.")

                lower = (stdout + stderr).lower()
                if any(x in lower for x in ban_markers):
                    print(f"[AntiBan] Block detected for '{log_name}', trying next...")
                    last_error_message = "Temporary consent or rate-limit block"
                    continue

                if "private video" in lower:
                    raise RuntimeError("Private video (requires account access).")

                video_info = json.loads(stdout)
                formats = video_info.get("formats", [])

                resolutions = sorted(
                    list({
                        f"{f['height']}p"
                        for f in formats
                        if f.get("vcodec") != "none" and f.get("height")
                    }),
                    key=lambda r: int(r[:-1]) if r[:-1].isdigit() else 0,
                    reverse=True
                )

                if not resolutions:
                    raise RuntimeError(
                        "No valid video formats found (only audio or thumbnails)."
                    )

                data = {
                    "resolutions": resolutions,
                    "duration": video_info.get("duration", 0),
                    "title": video_info.get("title", "Unknown Title")
                }
                self.cache[url] = data
                return data

            except Exception as e:
                last_error_message = str(e)
                print(f"[MetadataManager] Attempt with '{log_name}' failed: {str(e)[:250]}")
                low_err = last_error_message.lower()
                if any(x in low_err for x in ban_markers):
                    continue
                continue

        raise RuntimeError(
            f"Metadata fetch failed after all strategies.\n\nLast error:\n{last_error_message}"
        )


    def _handle_fetch_done(self, future, url):
        try:
            data = future.result()
            self.status_update.emit(url, "Ready to download...")
            self.resolutions_fetched.emit(url, data)
        except Exception as e:
            self.error.emit(url, str(e))
        finally:
            self._current_url = None
            self._current_process = None
            self._queued.discard(url)

    def cancel(self, url):
        if not url:
            return

        norm = canonicalize_youtube_url(url)
        self._cancelled.add(norm)

        if self._current_url == norm and self._current_process:
            try:
                print("[META CANCEL] HARD KILL", norm)
                self._kill_process_tree(self._current_process)
            except Exception:
                pass
            finally:
                self._current_process = None
                self._current_url = None

        # vyhození z fronty
        try:
            with self._queue_lock:
                new_q = queue.Queue()
                while True:
                    try:
                        item = self._queue.get_nowait()
                        if item != norm:
                            new_q.put(item)
                    except queue.Empty:
                        break
                self._queue = new_q
        except Exception:
            pass

        self._queued.discard(norm)

    def _kill_process_tree(self, process):
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass
    def cancel_one(self, url):
        url_norm = canonicalize_youtube_url(url)

        proc = self._processes.pop(url_norm, None)
        if proc:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

    def cancel_all(self):
        for proc in list(self._processes.values()):
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception:
                pass

        self._processes.clear()

# ----------------------
class InfoFetchThread(threading.Thread):
    def __init__(self, url, yt_dlp_path='yt-dlp', status_update=None, resolutions_fetched=None, error=None):
        super().__init__()
        self.url = url
        self.yt_dlp_path = yt_dlp_path
        self.status_update = status_update or (lambda *a, **k: None)
        self.resolutions_fetched = resolutions_fetched or (lambda *a, **k: None)
        self.error = error or (lambda *a, **k: None)

    def run(self):
        try:
            self.status_update("Loading video info...")
            session_name = 'default'
            if not _SESSION_MANAGER.has_cookie(session_name):
                try:
                    _SESSION_MANAGER.create_session_for_youtube(
                        name=session_name,
                        headless=False,
                        interactive=True
                    )
                except Exception:
                    pass
            cmd = build_safe_cmd(
                [self.yt_dlp_path, '--dump-json'],
                self.url,
                cookie_session=session_name
            )
            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate(timeout=30)
            try:
                out_text = stdout.decode('utf-8')
            except Exception:
                try:
                    out_text = stdout.decode('cp1250', errors='replace')
                except Exception:
                    out_text = stdout.decode('utf-8', errors='replace')
            if not out_text.strip():
                try:
                    err_text = stderr.decode('utf-8', errors='replace')
                except Exception:
                    err_text = str(stderr)
                raise RuntimeError(f"yt-dlp returned no output. stderr: {err_text}")
            video_info = json.loads(out_text)
            formats = video_info.get('formats', [])
            resolutions = sorted(
                list({
                    f.get('height')
                    for f in formats
                    if f.get('vcodec') != 'none' and f.get('height')
                }),
                reverse=True
            )
            resolutions_str = [f"{r}p" for r in resolutions if isinstance(r, int)]
            if resolutions_str:
                self.status_update("Ready to download...")
                self.resolutions_fetched({
                    "resolutions": resolutions_str,
                    "duration": video_info.get('duration', 0),
                    "title": video_info.get('title', 'Unknown Title')
                })
            else:
                self.error("No video streams found.")

        except subprocess.TimeoutExpired:
            self.error("yt-dlp timed out while fetching metadata.")
        except Exception as e:
            self.error(f"Failed to get video info: {str(e)}")

# ----------------------
# DownloadThread (reused)
# ----------------------
class DownloadThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(self, **kwargs):
        super().__init__()
        self.params = kwargs
        self._is_cancelled = False
        self.process = None
        self.yt_dlp_path = YTDLP_PATH
        self.ffmpeg_path = FFMPEG_PATH
        self.gpu_mode, self.gpu_encoder = ("cpu", "libx264")
        self._gpu_checked = False
        self._last_percent = -1
        self._current_download_url = None

    def cancel(self):
        self._is_cancelled = True
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                pass
            finally:
                self.process = None
        try:
            self.progress.emit(0, "Cancelled")
        except Exception:
            pass
        try:
            PROGRESS_AGGREGATOR.update(self._current_download_url, 0, "Cancelled")
        except Exception:
            pass
        return

    def run(self):
        if not self._gpu_checked:
            try:
                self.gpu_mode, self.gpu_encoder = check_gpu_support()
            except Exception:
                self.gpu_mode, self.gpu_encoder = ("cpu", "libx264")
            self._gpu_checked = True

        try:
            urls = self.params.get('urls', [])
            total_urls = len(urls)
            titles = self.params.get('titles', [])
            try:
                PROGRESS_AGGREGATOR.register_urls(urls)
            except Exception:
                pass

            for idx, url in enumerate(urls):
                if self._is_cancelled:
                    raise InterruptedError("Cancelled before start")

                if idx < len(titles):
                    title = titles[idx]
                else:
                    title = self.params.get('title') or f"video_{idx+1}"

                title = re.sub(r'[\\/*?:\"<>|]', "", title).strip() or f"video_{idx+1}"

                self._current_download_url = url
                try:
                    PROGRESS_AGGREGATOR.update(url, 0, f"Starting {idx+1}/{total_urls}")
                except Exception:
                    pass

                if self.params.get('format_opt', '').startswith('MP3'):
                    self._download_mp3(url, title)
                else:
                    self._download_video_with_optional_compress(url, title)

                try:
                    PROGRESS_AGGREGATOR.set_done(url)
                except Exception:
                    pass

                if self._is_cancelled:
                    raise InterruptedError("Cancelled during download")

            try:
                self.progress.emit(100, "All done")
            except Exception:
                pass
            self.finished.emit(True)

        except InterruptedError:
            try:
                self.progress.emit(0, "Cancelled")
            except Exception:
                pass
            try:
                self.error.emit("Download cancelled by user.")
            except Exception:
                pass
            self.finished.emit(False)

        except Exception as e:
            try:
                self.error.emit(f"Error: {str(e)}")
            except Exception:
                pass
            self.finished.emit(False)

        finally:
            try:
                QTimer.singleShot(1200, lambda: PROGRESS_AGGREGATOR.reset())
            except Exception:
                pass

    def _format_selector(self, height_str):
        m = re.search(r"(\d+)", height_str or "")
        h = m.group(1) if m else "1080"
        return (
            f"bv*[height={h}][vcodec^=av01]+bestaudio/"
            f"bv*[height={h}][vcodec^=vp9]+bestaudio/"
            f"bv*[height={h}][ext=mp4]+bestaudio/"
            f"bv*[height={h}]+bestaudio/"
            f"bestvideo+bestaudio/best"
        )

    def _download_video(self, url, title):
        save_dir = self.params["save_path"]
        requested_quality = self.params.get("video_quality", "1080p")
        available = self.params.get("available_resolutions", [])
        quality = choose_default_quality(available, requested_quality)
        out_path = get_unique_filepath(os.path.join(save_dir, f"{title}.mp4"))
        fmt = self._format_selector(quality)
        cmd = [
            self.yt_dlp_path,
            '--progress', '--no-playlist', '--no-recode-video',
            '--ffmpeg-location', self.ffmpeg_path,
            '-o', out_path,
            '-f', fmt,
            url
        ]
        dbg(f"DIRECT DL => {url} | -f {fmt} | -> {out_path}")
        self._run_proc(cmd, 0, 100, file_url=url, label="Downloading")

    def _download_video_with_optional_compress(self, url, title):
        save_dir = self.params["save_path"]
        requested_quality = self.params.get("video_quality", "1080p")
        available = self.params.get("available_resolutions", [])
        quality = choose_default_quality(available, requested_quality)
        print(">>> Requested:", requested_quality, "Available:", available, "Chosen:", quality)
        preset = self.params.get("compression_mode", "Original (No Re-encoding)")
        tmp_path = get_unique_filepath(os.path.join(save_dir, f"{title}__SOURCE__.mp4"))
        m = re.search(r"(\d+)", quality or "")
        h = m.group(1) if m else "1080"
        fmt = (
            f"bv*[height={h}][vcodec^=av01]+bestaudio/"
            f"bv*[height={h}][vcodec^=vp9]+bestaudio/"
            f"bv*[height={h}][ext=mp4]+bestaudio/"
            f"bv*[height={h}]+bestaudio/"
            f"bestvideo+bestaudio/best"
        )
        base_cmd = [
            self.yt_dlp_path,
            '--progress',
            '--no-playlist',
            '--merge-output-format', 'mp4',
            '--ffmpeg-location', self.ffmpeg_path,
            '-o', tmp_path,
            '-f', fmt,
            url
        ]
        try:
            self._run_proc(base_cmd, phase_start=0, phase_end=90, label="Downloading", file_url=url)
        except InterruptedError:
            raise
        if self._is_cancelled:
            self.progress.emit(0, "Cancelled")
            raise InterruptedError("User cancelled")
        if not os.path.exists(tmp_path):
            raise RuntimeError("Download failed: no file produced.")
        if preset.startswith("Original"):
            final = get_unique_filepath(os.path.join(save_dir, f"{title}.mp4"))
            os.replace(tmp_path, final)
            self.progress.emit(100, "Done")
            return
        final = get_unique_filepath(os.path.join(save_dir, f"{title}.mp4"))
        video_width, video_height = get_video_dimensions(tmp_path)
        v_encoder = self.gpu_encoder if getattr(self, "gpu_mode", "cpu") != "cpu" else "libx264"
        if video_width < 320 or video_height < 240:
            v_encoder = "libx264"
        orig_audio_br = get_audio_bitrate(tmp_path)

        def quality_from_preset(compression_preset, original_audio_kbps, encoder="libx264"):
            table = {
                "Very High Quality low compression": {"level": 18, "a_kbps": 192},
                "High Quality (Compressed)":         {"level": 21, "a_kbps": 160},
                "Medium Quality":                    {"level": 24, "a_kbps": 128},
                "Low Quality":                       {"level": 28, "a_kbps": 128},
                "Very Low Quality":                  {"level": 32, "a_kbps": 96},
            }
            conf = table.get(compression_preset, table["Medium Quality"])
            level = conf["level"]
            a_target = conf["a_kbps"]
            a_kbps = min(int(original_audio_kbps or a_target), a_target)
            enc = (encoder or "libx264").lower()
            if enc == "libx264":
                v_args = ["-c:v", "libx264", "-crf", str(level), "-preset", "slow", "-pix_fmt", "yuv420p"]
            elif enc.endswith("_nvenc"):
                cq = max(15, level - 2)
                v_args = ["-c:v", enc, "-rc", "vbr_hq", "-cq", str(cq), "-b:v", "0", "-preset", "p5"]
            elif enc.endswith("_qsv") or enc.endswith("_amf"):
                v_args = ["-c:v", enc, "-global_quality", str(level), "-preset", "medium"]
            else:
                v_args = ["-c:v", "libx264", "-crf", str(level), "-preset", "slow", "-pix_fmt", "yuv420p"]
            a_args = ["-c:a", "aac", "-b:a", f"{a_kbps}k"]
            return v_args, a_args

        v_args, a_args = quality_from_preset(preset, orig_audio_br, v_encoder)

        ff = [
            self.ffmpeg_path, '-y', '-hide_banner',
            '-i', tmp_path,
            *v_args,
            *a_args,
            '-movflags', '+faststart',
            final
        ]
        try:
            start_time = time.time()
            est_total = 10
            last_emit = 90
            self._run_proc(ff, phase_start=90, phase_end=100, label="Compressing", file_url=url)
            while last_emit < 100 and not self._is_cancelled:
                elapsed = time.time() - start_time
                pct = min(100, 90 + (elapsed / est_total) * 10)
                if pct > last_emit:
                    last_emit = pct
                    self.progress.emit(int(pct), f"Finalizing {int(pct)}%")
                    PROGRESS_AGGREGATOR.update(url, int(pct), f"Finalizing {int(pct)}%")
                if pct >= 100:
                    break
                time.sleep(0.3)
        except InterruptedError:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _download_mp3(self, url, title):
        outp = get_unique_filepath(os.path.join(self.params['save_path'], f"{title}.mp3"))
        cmd = [
            self.yt_dlp_path, '--progress', '--no-playlist',
            '--extract-audio', '--audio-format', 'mp3',
            '--audio-quality', f"{self.params.get('mp3_bitrate', 320)}K",
            '--ffmpeg-location', self.ffmpeg_path,
            '-o', outp, url
        ]
        self._run_proc(cmd, phase_start=0, phase_end=100, label="Downloading MP3", file_url=url)

    def _with_client_fallbacks(self, base_cmd, phase_start=0, phase_end=100, label="Downloading", file_url=None):
        strategies = [
            ("web_safari", False),
            ("default", True),
            ("tv", False),
            ("default", False),
        ]
        last_err = "unknown"
        for client, use_cookies in strategies:
            try:
                cmd = list(base_cmd)
                if client != "default":
                    cmd += ["--extractor-args", f"youtube:player_client={client}"]
                if use_cookies:
                    for br in BROWSERS:
                        cmd += ["--cookies-from-browser", br]
                else:
                    cmd += ["--no-cookies"]
                return self._run_proc(cmd, phase_start=phase_start, phase_end=phase_end, label=label, file_url=file_url)
            except Exception as e:
                last_err = str(e)
                continue
        raise RuntimeError(f"Download interrupted!{last_err}")

    def _run_proc(self, cmd, phase_start=0, phase_end=100, label="Processing", file_url=None):
        try:
            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        except Exception:
            creation_flags = 0
        duration_s = None
        try:
            duration_s = float(self.params.get("duration_s")) if self.params and self.params.get("duration_s") else None
        except Exception:
            duration_s = None
        self.process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
            bufsize=1, creationflags=creation_flags
        )
        stderr_buf = []
        stdout_q = queue.Queue()

        def _read_stderr():
            try:
                for line in self.process.stderr:
                    stderr_buf.append(line)
                    try:
                        stdout_q.put(line)
                    except Exception:
                        pass
            except Exception:
                pass

        def _read_stdout():
            try:
                for line in self.process.stdout:
                    try:
                        stdout_q.put(line)
                    except Exception:
                        pass
            except Exception:
                pass
            finally:
                try:
                    stdout_q.put(None)
                except Exception:
                    pass
        t_err = threading.Thread(target=_read_stderr, daemon=True)
        t_out = threading.Thread(target=_read_stdout, daemon=True)
        t_err.start()
        t_out.start()
        last = None
        last_update = time.time()

    def _run_proc(self, cmd, phase_start=0, phase_end=100, label="Processing", file_url=None):
        try:
            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        except Exception:
            creation_flags = 0
        duration_s = None
        try:
            duration_s = float(self.params.get("duration_s")) if self.params and self.params.get("duration_s") else None
        except Exception:
            duration_s = None
        self.process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
            bufsize=1, creationflags=creation_flags
        )
        stderr_buf = []
        stdout_q = queue.Queue()

        def _read_stderr():
            try:
                for line in self.process.stderr:
                    stderr_buf.append(line)
                    try:
                        stdout_q.put(line)
                    except Exception:
                        pass
            except Exception:
                pass

        def _read_stdout():
            try:
                for line in self.process.stdout:
                    try:
                        stdout_q.put(line)
                    except Exception:
                        pass
            except Exception:
                pass
            finally:
                try:
                    stdout_q.put(None)
                except Exception:
                    pass
        t_err = threading.Thread(target=_read_stderr, daemon=True)
        t_out = threading.Thread(target=_read_stdout, daemon=True)
        t_err.start()
        t_out.start()
        last = None
        last_update = time.time()

        def _parse_ffmpeg_time(s):
            m = re.search(r'time=(\d{1,2}):(\d{2}):([\d\.]+)', s)
            if not m:
                return None
            try:
                h = int(m.group(1))
                mm = int(m.group(2))
                ss = float(m.group(3))
                return h * 3600 + mm * 60 + ss
            except Exception:
                return None
        try:
            while True:
                if self._is_cancelled:
                    final_pct = last if last is not None else phase_start
                    try:
                        self.progress.emit(final_pct, "Cancelled")
                    except Exception:
                        pass
                    try:
                        if self.process and self.process.poll() is None:
                            self.process.terminate()
                            self.process.wait(timeout=5)
                    except Exception:
                        pass
                    finally:
                        self.process = None
                    try:
                        PROGRESS_AGGREGATOR.update(file_url, 0, "Cancelled")
                    except Exception:
                        pass
                    return
                try:
                    ln = stdout_q.get(timeout=0.5)
                except queue.Empty:
                    ln = None
                if ln is None and self.process.poll() is not None:
                    break
                if ln:
                    m = re.search(r'\[download\]\s*([\d\.]+)\%', ln)
                    if m and phase_end > phase_start:
                        try:
                            raw_p = float(m.group(1))
                            p = int(round(phase_start + raw_p * (phase_end - phase_start) / 100.0))
                        except Exception:
                            p = None
                        if p is not None and (last is None or p > last):
                            last = p
                            last_update = time.time()
                            try:
                                self.progress.emit(p, f"{label}. {p}%")
                            except Exception:
                                pass
                            try:
                                PROGRESS_AGGREGATOR.update(file_url, p, f"{label} {p}%")
                            except Exception:
                                pass
                            continue
                    if duration_s and phase_end > phase_start:
                        tsec = _parse_ffmpeg_time(ln)
                        if tsec is not None and duration_s > 0:
                            frac = min(1.0, max(0.0, float(tsec) / float(duration_s)))
                            p = int(round(phase_start + frac * (phase_end - phase_start)))
                            if last is None or p > last:
                                last = p
                                last_update = time.time()
                                try:
                                    self.progress.emit(p, f"{label}. {p}%")
                                except Exception:
                                    pass
                                try:
                                    PROGRESS_AGGREGATOR.update(file_url, p, f"{label} {p}%")
                                except Exception:
                                    pass
                                continue
                if time.time() - last_update > 0.8:
                    if phase_end > phase_start:
                        if last is None:
                            last = phase_start
                        if last < phase_end - 1:
                            last += 1
                            last_update = time.time()
                            try:
                                self.progress.emit(last, f"{label}. {last}%")
                            except Exception:
                                pass
                            try:
                                PROGRESS_AGGREGATOR.update(file_url, last, f"{label} {last}%")
                            except Exception:
                                pass

                time.sleep(0.01)
            t_out.join(timeout=0.1)
            t_err.join(timeout=0.1)
            if self.process.returncode != 0 and not self._is_cancelled:
                errtxt = "".join(stderr_buf).strip() or "process failed"
                raise RuntimeError(errtxt)
            if phase_end > phase_start and not self._is_cancelled:
                if last is None:
                    last = phase_end
                    try:
                        self.progress.emit(phase_end, f"{label}. {phase_end}%")
                    except Exception:
                        pass
                    try:
                        PROGRESS_AGGREGATOR.update(file_url, phase_end, f"{label} {phase_end}%")
                    except Exception:
                        pass
                elif last < phase_end:
                    try:
                        self.progress.emit(phase_end, f"{label}. {phase_end}%")
                    except Exception:
                        pass
                    try:
                        PROGRESS_AGGREGATOR.update(file_url, phase_end, f"{label} {phase_end}%")
                    except Exception:
                        pass
        finally:
            try:
                if self.process:
                    self.process.terminate()
                    self.process = None
            except Exception:
                pass
            
class URLLineWidget(QWidget):
    line_edited = pyqtSignal(object)
    delete_requested = pyqtSignal(object)
    paste_multi = pyqtSignal(object, list)

    def __init__(self, parent_dialog=None, initial_url='', is_first=False):
        super().__init__()
        self.parent_dialog = parent_dialog
        self.is_first = is_first
        self._last_url = None

        QTimer.singleShot(0, lambda: self.setMinimumWidth(self.sizeHint().width() + 20))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # --- HORNÍ ŘÁDEK (GRID) ---
        top = QGridLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(4)

        # ---- LEVÁ STRANA ----
        if self.is_first:
            self.checkbox = None
            left_widget = QWidget()
            left_widget.setFixedWidth(18)
        else:
            self.checkbox = QCheckBox()
            self.checkbox.setChecked(True)
            self.checkbox.setFixedWidth(18)
            self.checkbox.setToolTip("Include in download")

            if self.parent_dialog:
                self.checkbox.stateChanged.connect(
                    lambda: self.parent_dialog.emit_updated_urls()
                )

            left_widget = self.checkbox

        top.addWidget(left_widget, 0, 0)

        # ---- URL INPUT ----
        self.line_edit = QLineEdit(initial_url)
        self.line_edit.setPlaceholderText("Enter URL..." if self.is_first else "")
        self.line_edit.setClearButtonEnabled(True)
        #self.line_edit.textChanged.connect(self._on_line_edit_changed_for_delete)

        w = getattr(self.parent_dialog, 'input_field_width', 400)
        self.line_edit.setFixedWidth(w)

        top.addWidget(self.line_edit, 0, 1)

        # ---- PRAVÁ STRANA ----
        if self.is_first:
            # pouze PASTE
            self.btn_paste = QPushButton("Paste")
            self.btn_paste.setFixedSize(60, 28)
            top.addWidget(self.btn_paste, 0, 2)
            self.btn_remove = None

        else:
            # malé červené "x" pro mazání řádků
            self.btn_paste = None

            self.btn_remove = QToolButton(self)
            self.btn_remove.setText("z")
            self.btn_remove.setFixedSize(24, 24)
            self.btn_remove.setToolTip("Remove this row")
            self.btn_remove.setStyleSheet(
                "QToolButton { background: transparent; color: #ff4444; font-size: 14px; border: none; }"
                "QToolButton:hover { color: #ff6666; }"
            )
            self.btn_remove.clicked.connect(lambda: self.delete_requested.emit(self))
            top.addWidget(self.btn_remove, 0, 2)

        top.setColumnStretch(1, 1)
        main_layout.addLayout(top)

        # ---- META LABEL (jen normální řádek) ----
        self.meta_label = QLabel("")
        self.meta_label.setWordWrap(False)
        self.meta_label.setStyleSheet("color: #666; font-size: 11px;")

        if not self.is_first:
            main_layout.addWidget(self.meta_label)

        # ---- Signály ----
        self.line_edit.textChanged.connect(self.on_text_changed)
        self.line_edit.returnPressed.connect(self.on_return_pressed)
        self.line_edit.keyPressEvent = self._key_press_event_custom

        if self.is_first:
            self.btn_paste.clicked.connect(self._handle_paste)
            self.line_edit.textChanged.connect(self._on_first_line_changed)

        # ---- Styl PASTE ----
        if self.is_first:
            self.btn_paste.setStyleSheet(
                "QPushButton { background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, "
                "stop:0 rgb(122,150,230), stop:0.5 rgb(42,130,218), stop:1 rgb(24,92,158)); "
                "color:white; font-weight:bold; padding:4px 10px; border-radius:6px; border:2px solid #555; }"
                "QPushButton:hover { background:qlineargradient(spread:pad,x1:0,y1:0,x2:0,y2:1, "
                "stop:0 rgb(85,163,235),stop:0.5 rgb(55,140,225),stop:1 rgb(35,102,168)); "
                "border:2px solid #555; }"
                "QPushButton:pressed { background:qlineargradient(spread:pad,x1:0,y1:1,x2:0,y2:0, "
                "stop:0 rgb(20,80,140),stop:0.5 rgb(32,110,185),stop:1 rgb(50,140,210)); "
                "border:2px solid #555; }"
            )

    def _on_line_edit_changed_for_delete(self, text):
        if not text.strip():
            self.setMarkedForDelete(True)
        else:
            self.setMarkedForDelete(False)

    def _on_first_line_changed(self, text):
        if not text and self.parent_dialog and hasattr(self.parent_dialog, 'check_and_remove_empty_line_if_only_first'):
            self.parent_dialog.check_and_remove_empty_line_if_only_first()
    
    def _key_press_event_custom(self, event):
        if event.key() == Qt.Key.Key_Delete and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.line_edit.selectAll()
            self.line_edit.clear()
        else:
            QLineEdit.keyPressEvent(self.line_edit, event)
    
    def _handle_paste(self):
        clip = QApplication.clipboard().text().strip()
        if not clip:
            return

        url_pattern = re.compile(
            r'^https?://(?:www\.)?(?:youtube\.com|youtu\.be|facebook\.com|fb\.watch)/\S+',
            re.IGNORECASE
        )

        # rozdělíme clipboard po řádcích
        parts = [p.strip() for p in re.split(r'[\r\n]+', clip) if p.strip()]
        urls = [p for p in parts if url_pattern.match(p)]

        if not urls:
            QMessageBox.information(
                self,
                "Invalid URL",
                "Clipboard does not contain a valid YouTube/Facebook URL."
            )
            return

        # první URL jde do prvního řádku
        first = urls[0]

        if is_youtube_url(first) and ("list=RD" in first or "start_radio=1" in first):
            first_canon = first
        else:
            first_canon = normalize_url(first)

        self.line_edit.setText(first_canon)

        # ostatní URL → přes paste_multi do dialogu
        if len(urls) > 1:
            remaining = []
            for u in urls[1:]:
                if is_youtube_url(u) and ("list=RD" in u or "start_radio=1" in u):
                    remaining.append(u)
                else:
                    remaining.append(normalize_url(u))

            # 🔥 Nový MULTI EMIT: (sender_widget, urls_list)
            try:
                self.paste_multi.emit(self, remaining)
            except Exception as e:
                print("paste_multi emit error:", e)

    def on_text_changed(self, text):
        # první řádek NIKDY neřeší mazání řádku
        if self.is_first:
            self._last_url = text.strip()
            return

        new_url = text.strip()

        # --- CLEAR BUTTON CLICK: URL → "" a dřív něco bylo ---
        if new_url == "" and self._last_url:
            # 1) zrušit metadata načítání
            if self.parent_dialog and hasattr(self.parent_dialog, "metadata_manager"):
                try:
                    self.parent_dialog.metadata_manager.cancel(self._last_url)
                except Exception:
                    pass

            self._last_url = ""

            # 2) Smazat celý řádek
            try:
                self.delete_requested.emit(self)
            except Exception:
                pass
            return

        # --- běžná logika dál ---
        # uložíme poslední text
        self._last_url = new_url

        # pokud URL není podporovaná
        if new_url and not is_supported_url(new_url):
            if self.parent_dialog and hasattr(self.parent_dialog, 'cancel_meta_fetch_for_widget'):
                self.parent_dialog.cancel_meta_fetch_for_widget(self)

            self.line_edit.setClearButtonEnabled(False)

            if self.meta_label:
                self.meta_label.setText("<span style='color:#e66;'>Unsupported URL.</span>")
                QTimer.singleShot(2000, self.clear_meta)

            # message box (tichý fail pokud chyba)
            try:
                QMessageBox.warning(self, "Invalid URL", "Clipboard does not contain a valid YouTube/Facebook URL.")
            except Exception:
                pass

            self.line_edit.blockSignals(True)
            self.line_edit.clear()
            self.line_edit.blockSignals(False)
            return

        # --- duplicita ---
        parent = self.parent()
        while parent and not hasattr(parent, 'line_widgets'):
            parent = parent.parent()

        if parent and new_url:
            urls_now = [
                w.get_url().strip()
                for w in parent.line_widgets
                if w is not self and w.get_url()
            ]
            if new_url in urls_now:
                self.line_edit.blockSignals(True)
                self.line_edit.clear()
                self.line_edit.blockSignals(False)

                self.line_edit.setClearButtonEnabled(False)
                QTimer.singleShot(50, lambda: self.line_edit.setClearButtonEnabled(True))

                if self.meta_label:
                    self.meta_label.setText("<span style='color:#e66;'>Duplicate URL skipped.</span>")
                    QTimer.singleShot(2000, self.clear_meta)
                return

        # normální událost – notif parent
        try:
            self.line_edited.emit(self)
        except Exception:
            pass


    def on_return_pressed(self):
        self.line_edited.emit()
    
    def get_url(self):
        return self.line_edit.text().strip()
    
    def set_meta(self, text):
        try:
            self.meta_label.setToolTip(text)
            font_metrics = self.meta_label.fontMetrics()
            elided_text = font_metrics.elidedText(text, Qt.TextElideMode.ElideRight, self.line_edit.width())
            self.meta_label.setText(elided_text)
        except RuntimeError:
            pass
    
    def clear_meta(self):
        try:
            self.meta_label.setText("")
            self.meta_label.setToolTip("")
        except RuntimeError:
            pass
    
    def is_empty(self):
        return self.get_url() == ""
    
    def _on_text_changed(self, text):
        text = text.strip()
        if not text:
            return
        if re.match(r'^https?://(?:www\.)?(?:youtube\.com|youtu\.be|facebook\.com|fb\.watch)/\S+', text, re.IGNORECASE):
            if is_youtube_url(text) and ("list=RD" in text or "start_radio=1" in text):
                norm = text
            else:
                norm = normalize_url(text)
            parent = self.parent()
            while parent and not hasattr(parent, 'fetch_meta_for_widget'):
                parent = parent.parent()

            if parent and hasattr(parent, 'fetch_meta_for_widget'):
                self.line_edit.blockSignals(True)
                self.line_edit.setText(norm)
                self.line_edit.blockSignals(False)
                parent.fetch_meta_for_widget(self)

class InputRowWidget(QWidget):
    url_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.edit = QLineEdit(self)
        self.edit.setPlaceholderText("Paste URL here…")
        self.edit.returnPressed.connect(self._submit)

        self.paste_btn = QPushButton("Paste", self)
        self.paste_btn.clicked.connect(self._paste)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.edit, 1)
        layout.addWidget(self.paste_btn)

    def _paste(self):
        text = QApplication.clipboard().text()
        if not text:
            return

        urls = [line.strip() for line in text.splitlines() if line.strip()]
        for url in urls:
            self.url_submitted.emit(url)

        self.edit.clear()

    def _submit(self):
        url = self.edit.text().strip()
        if not url:
            return

        self.url_submitted.emit(url)
        self.edit.clear()

class CombiRowWidget(QWidget):
    delete_requested = pyqtSignal(object)

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self._last_text = url

        self.checkbox = QCheckBox(self)
        self.checkbox.setChecked(True)

        self.edit = QLineEdit(self)
        self.edit.setText(url)
        self.edit.setReadOnly(True)
        self.edit.setClearButtonEnabled(True)

        self.edit.textChanged.connect(self._on_text_changed)
        self.edit.editingFinished.connect(self._on_edit_finished)

        self.title = QLabel("", self)
        self.title.setWordWrap(True)
        self.title.setStyleSheet("padding-left: 22px; color: #aaa;")

        top = QHBoxLayout()
        top.setContentsMargins(0, 6, 0, 0)
        top.setSpacing(6)
        top.addWidget(self.checkbox)
        top.addWidget(self.edit, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addLayout(top)
        layout.addWidget(self.title)

    def _on_text_changed(self, text):
        self._last_text = text

    def _on_edit_finished(self):
        if not self.edit.text().strip():
            self.delete_requested.emit(self)

    def set_title(self, text):
        self.title.setText(text)

    def set_error(self, msg):
        self.checkbox.setChecked(False)
        self.checkbox.setEnabled(False)
        self.title.setText(msg)

class MultiURLDialog(QFrame):
    urls_updated = pyqtSignal(list)
    closed = pyqtSignal(list)

    def __init__(self, parent=None, urls=None):
        super().__init__(parent, Qt.WindowType.Dialog)

        self._owner = parent
        self.rows = []

        self.setWindowTitle("Enter Multiple URLs")
        self.setFixedSize(585, 375)

        # ======================================================
        #   MAIN LAYOUT
        # ======================================================
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(12, 12, 12, 12)

        # ======================================================
        #   INPUT ROW (FIXNÍ, HLUPÁ)
        # ======================================================
        self.input_row = InputRowWidget(self)
        self.input_row.url_submitted.connect(self._add_url)
        self.layout.addWidget(self.input_row)

        # ======================================================
        #   SCROLL AREA – POUZE COMBI ŘÁDKY
        # ======================================================
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setStyleSheet(
            "QScrollArea { padding-right: 0px; }"
            "QScrollBar:vertical { margin-right: 5px; }"
        )

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

        # ======================================================
        #   PŘEDVYPLNĚNÉ URL (pokud jsou)
        # ======================================================
        if urls:
            for item in urls:
                if isinstance(item, dict):
                    url = item.get("url", "")
                    checked = bool(item.get("checked", True))
                else:
                    url = item
                    checked = True

                row = self._create_row(url)
                row.checkbox.setChecked(checked)

        # ======================================================
        #   BUTTONS
        # ======================================================
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")

        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        self.layout.addLayout(btn_layout)

        # ======================================================
        #   INFO TEXT
        # ======================================================
        info = QLabel(
            "Paste multiple URLs (each on a new line) or add them one by one. "
            "Use Ctrl+A to select all, Ctrl+D to deselect all."
        )
        info.setStyleSheet("color:#999; font-size:10px; margin-top:-3px;")
        self.layout.addWidget(info)

        self._center_dialog(parent)

    # ======================================================
    #   INTERNAL HELPERS
    # ======================================================

    def _center_dialog(self, parent):
        parent_geom = (
            parent.geometry()
            if parent else QApplication.primaryScreen().availableGeometry()
        )
        geom = self.frameGeometry()
        geom.moveCenter(parent_geom.center())
        self.move(geom.topLeft())

    def _create_row(self, url):
        row = CombiRowWidget(url, self)
        row.delete_requested.connect(self._remove_row)

        self.scroll_layout.insertWidget(
            self.scroll_layout.count() - 1,
            row
        )
        self.rows.append(row)

        mgr = getattr(self._owner, "metadata_manager", None)
        if mgr:
            mgr.request(url)

        return row

    def _remove_row(self, row):
        # 1) zabít metadata pro TEN řádek
        try:
            mgr = getattr(self._owner, "metadata_manager", None)
            if mgr:
                mgr.cancel_one(row.url)
        except Exception:
            pass

        # 2) odebrat z interního seznamu
        if row in self.rows:
            self.rows.remove(row)

        # 3) fyzicky zničit widget
        row.setParent(None)
        row.deleteLater()

    # ======================================================
    #   INPUT HANDLING
    # ======================================================

    def _add_url(self, url):
        url = normalize_url(url)

        if not is_supported_url(url):
            return

        row = CombiRowWidget(url, self)
        row.delete_requested.connect(self._remove_row)

        self.scroll_layout.insertWidget(
            self.scroll_layout.count() - 1,
            row
        )

        self.rows.append(row)

        mgr = getattr(self._owner, "metadata_manager", None)
        if mgr:
            mgr.request(url)

    def select_all_checkboxes(self):
        for w in self.line_widgets:
            if w.checkbox.isVisible():
                w.checkbox.setChecked(True)

    def deselect_all_checkboxes(self):
        for w in self.line_widgets:
            if w.checkbox.isVisible():
                w.checkbox.setChecked(False)

    def delete_selected_lines(self):
        for w in list(self.line_widgets):
            if w.checkbox.isVisible() and w.checkbox.isChecked():
                if not w.is_empty() or not getattr(w, "is_first", False):
                    self.delete_line(w)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.ShortcutOverride:
            key = event.key()
            mods = event.modifiers()
            if key == Qt.Key.Key_A and (mods & Qt.KeyboardModifier.ControlModifier):
                event.accept()
                self.select_all_checkboxes()
                return True
            if key == Qt.Key.Key_D and (mods & Qt.KeyboardModifier.ControlModifier):
                event.accept()
                self.deselect_all_checkboxes()
                return True
            if key == Qt.Key.Key_Delete:
                event.accept()
                self.delete_selected_lines()
                return True
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            mods = event.modifiers()
            if key == Qt.Key.Key_Delete:
                self.delete_selected_lines()
                return True
            if key == Qt.Key.Key_A and (mods & Qt.KeyboardModifier.ControlModifier):
                self.select_all_checkboxes()
                return True
            if key == Qt.Key.Key_D and (mods & Qt.KeyboardModifier.ControlModifier):
                self.deselect_all_checkboxes()
                return True
        return super().eventFilter(obj, event)

    def update_remove_buttons(self):
        """
        Nastaví viditelnost mazacího tlačítka.
        První řádek (paste) nemá nikdy btn_remove.
        Ostatní řádky mají btn_remove vždy viditelné.
        """
        for w in self.line_widgets:
            if w.is_first:
                # první řádek = bez mazacího 'x'
                if w.btn_remove:
                    w.btn_remove.setVisible(False)
                continue

            # normální řádky mají vždy malé 'x'
            if w.btn_remove:
                w.btn_remove.setVisible(True)

            # right_spacer nemá aktuálně žádnou zvláštní logiku
            if hasattr(w, "right_spacer"):
                w.right_spacer.setVisible(False)

    def is_last_empty_widget(self, widget):
        return (self.line_widgets and
                widget is self.line_widgets[-1] and
                widget.is_empty())

    def add_line(self, url_text=""):
        widget = URLLineWidget(
            parent_dialog=self,
            initial_url=url_text,
            is_first=False
        )

        if hasattr(widget, "checkbox"):
            widget.checkbox.stateChanged.connect(self.emit_updated_urls)

        widget.delete_requested.connect(lambda w=widget: self.delete_specific_line(w))
        widget.line_edited.connect(lambda w=widget: self.on_line_edited(w))
        widget.paste_multi.connect(self.handle_paste_multi)

        try:
            widget.btn_paste.setVisible(False)
        except:
            pass

        try:
            widget.right_spacer.setVisible(True)
        except:
            pass

        self.scroll_layout.insertWidget(
            self.scroll_layout.count() - 1,
            widget
        )

        self.line_widgets.append(widget)

        url = widget.get_url().strip()
        if url:
            self.fetch_meta_for_widget(widget)
        else:
            if hasattr(widget, "checkbox"):
                widget.checkbox.setChecked(True)

        self.update_remove_buttons()
        self.emit_updated_urls()
        return widget

    def handle_paste_multi(self, widget, url_list):
        # Convert list-like argument into a list of strings
        if isinstance(url_list, str):
            url_list = [url_list]
        elif isinstance(url_list, (list, tuple)):
            url_list = [str(x).strip() for x in url_list if str(x).strip()]
        else:
            url_list = []

        if not url_list:
            return

        # Normalize & check duplicates
        existing = {w.get_url().strip() for w in self.line_widgets if w.get_url().strip()}
        duplicates_found = False
        valid_final = []

        for raw in url_list:
            if not is_supported_url(raw):
                continue

            if is_youtube_url(raw) and ("list=RD" in raw or "start_radio=1" in raw):
                norm = raw
            else:
                norm = normalize_url(raw)

            if norm in existing:
                duplicates_found = True
                continue

            existing.add(norm)
            valid_final.append(norm)

        # add each as new scroll line
        for u in valid_final:
            self.add_line(u)

        self.emit_updated_urls()
        self.update_remove_buttons()

        # Show "duplicate" message
        if duplicates_found:
            parent = getattr(self, "_owner", None)
            if parent and hasattr(parent, "progress_bar"):
                try:
                    parent.progress_bar.setFormat("⚠️ Duplicate URLs ignored")
                    QTimer.singleShot(
                        2000,
                        lambda: parent.progress_bar.setFormat("Ready to download...")
                    )
                except Exception:
                    pass


    def delete_specific_line(self, widget):
        # ochrana: první řádek se nikdy nemaže
        if widget is getattr(self, "first_line", None):
            return

        # stop loading meta
        if hasattr(self, "cancel_meta_fetch_for_widget"):
            try:
                self.cancel_meta_fetch_for_widget(widget)
            except Exception:
                pass

        # kill thread
        t = self.info_threads.pop(widget, None) if hasattr(self, "info_threads") else None
        if t and t.isRunning():
            try:
                t.terminate()
            except Exception:
                pass

        # odebrat widget ze seznamu
        try:
            self.line_widgets.remove(widget)
        except:
            pass

        # odstranit widget z UI
        try:
            widget.setParent(None)
            widget.deleteLater()
        except:
            pass

        # refresh
        self.emit_updated_urls()


        def delete_line(self, widget):
            """
            Odstraní pouze skutečné URL řádky (ne první paste řádek).
            Killne meta-loading, odpojí signály, smaže widget a refreshne UI.
            """

            # --- 1) PRVNÍ ŘÁDEK (PASTE) SE NIKDY NEODSTRAŇUJE ---
            if widget is getattr(self, "first_line", None):
                # první řádek místo mazání pouze vyčistíme
                try:
                    widget.line_edit.clear()
                    widget.meta_label.clear()
                except Exception:
                    pass
                return

            # --- 2) Pokud widget není v line_widgets → ignorujeme ---
            if widget not in self.line_widgets:
                return

            # --- 3) ZASTAVENÍ A ODPOJENÍ CALLBACKŮ METADATA ---
            try:
                cb = self._mgr_callbacks.pop(widget, None)
            except Exception:
                cb = None

            if cb:
                try:
                    mgr_for_cb, on_fetched, on_error, on_status, expected_url = cb

                    try: mgr_for_cb.resolutions_fetched.disconnect(on_fetched)
                    except: pass

                    try: mgr_for_cb.error.disconnect(on_error)
                    except: pass

                    try: mgr_for_cb.status_update.disconnect(on_status)
                    except: pass

                    if hasattr(mgr_for_cb, "cancel"):
                        try: mgr_for_cb.cancel(expected_url)
                        except: pass

                except Exception:
                    pass

            # --- 4) ZASTAVENÍ SPINNER / QTimer ---
            if hasattr(self, "_loading_timers") and widget in self._loading_timers:
                try:
                    self._loading_timers[widget].stop()
                except Exception:
                    pass
                self._loading_timers.pop(widget, None)

            # --- 5) KILL THREADU ---
            t = self.info_threads.pop(widget, None) if hasattr(self, "info_threads") else None
            if t and t.isRunning():
                try: t.terminate()
                except Exception: pass

            # --- 6) DISCONNECT SIGNÁLŮ Z WIDGETU ---
            try: widget.line_edited.disconnect()
            except Exception: pass

            try: widget.delete_requested.disconnect()
            except Exception: pass

            try:
                if hasattr(widget, "paste_multi") and widget.paste_multi:
                    widget.paste_multi.disconnect()
            except Exception:
                pass

            # --- 7) SMAZÁNÍ Z LISTU A UI ---
            try:
                self.line_widgets.remove(widget)
                widget.setParent(None)
                widget.deleteLater()
            except Exception:
                pass

            # --- 8) REFRESH UI ---
            self.update_remove_buttons()
            self.emit_updated_urls()

    def emit_updated_urls(self):
        try:
            all_urls = []
            selected_urls = []
            parent = getattr(self, "_owner", None)
            mgr = getattr(parent, "metadata_manager", None)
            payload = []

            for w in self.line_widgets:
                u = ""
                try:
                    u = (w.get_url() or "").strip()
                except Exception:
                    u = ""
                if not u:
                    continue

                u_norm = canonicalize_youtube_url(u)
                all_urls.append(u_norm)

                is_checked = True
                try:
                    if getattr(w, "checkbox", None) and w.checkbox.isVisible():
                        is_checked = bool(w.checkbox.isChecked())
                except Exception:
                    is_checked = True
                is_failed = bool(mgr and u_norm in getattr(mgr, "failed", set()))
                payload.append({
                    "url": u_norm,
                    "checked": (is_checked and not is_failed)
                })

                if is_checked and not is_failed:
                    selected_urls.append(u_norm)

            if parent:
                try:
                    parent.saved_multilist = list(payload)
                except Exception as e:
                    print(f"[MultiURLDialog.emit_updated_urls] Saving multilist failed: {e}")

            self.urls_updated.emit(all_urls)

            if parent and hasattr(parent, "handle_multi_url_close"):
                try:
                    parent.handle_multi_url_close(payload)
                except Exception as e:
                    print(f"[MultiURLDialog.emit_updated_urls] handle_multi_url_close failed: {e}")
            try:
                if mgr:
                    for w in self.line_widgets:
                        url = (w.get_url() or "").strip()
                        if not url:
                            continue
                        norm = canonicalize_youtube_url(url)
                        if norm in mgr.cache:
                            data = mgr.cache[norm]
                            title = data.get("title", "Unknown")
                            duration = data.get("duration", 0)
                            mins, secs = int(duration // 60), int(duration % 60)
                            resolutions = data.get("resolutions", [])
                            best = resolutions[0] if resolutions else "N/A"
                            try:
                                w.set_meta(f"Title: {title} | Duration: {mins:02d}:{secs:02d} | Best: {best}")
                            except Exception:
                                pass
            except Exception as e:
                print(f"[MultiURLDialog.emit_updated_urls] Metadata UI refresh failed: {e}")

            if parent and hasattr(parent, "_recompute_status"):
                QTimer.singleShot(100, parent._recompute_status)

            try:
                if parent and hasattr(parent, "metadata_manager"):
                    mgr = parent.metadata_manager
                    all_cached = all(u in getattr(mgr, "cache", {}) for u in selected_urls)
                    total_count = len(all_urls)
                    selected_count = len(selected_urls)

                    if selected_count == 0:
                        if hasattr(parent, "progress_bar"):
                            parent.progress_bar.setFormat("No videos selected.")
                            parent.progress_bar.setValue(0)
                        if hasattr(parent, "download_btn"):
                            parent.download_btn.setEnabled(False)
                        if hasattr(parent, "set_combos_enabled"):
                            parent.set_combos_enabled(False)
                        if hasattr(parent, "video_info_label"):
                            parent.video_info_label.setText("No videos selected – please choose at least one to download.")
                        return

                    if all_cached:
                        if hasattr(parent, "progress_bar"):
                            parent.progress_bar.setFormat("Ready to download...")
                        if hasattr(parent, "download_btn"):
                            parent.download_btn.setEnabled(True)
                        if hasattr(parent, "set_combos_enabled"):
                            parent.set_combos_enabled(True)
                        if hasattr(parent, "video_info_label"):
                            parent.video_info_label.setText(f"{selected_count}/{total_count} videos ready to download.")
                    else:
                        if hasattr(parent, "progress_bar"):
                            parent.progress_bar.setFormat("Loading video info...")
                            parent.progress_bar.setValue(0)
                        if hasattr(parent, "download_btn"):
                            parent.download_btn.setEnabled(False)
                        if hasattr(parent, "set_combos_enabled"):
                            parent.set_combos_enabled(False)
                        if hasattr(parent, "video_info_label"):
                            parent.video_info_label.setText(f"{selected_count}/{total_count} videos loading...")
            except Exception as e:
                print(f"[MultiURLDialog.emit_updated_urls] Status sync failed: {e}")

        except Exception as e:
            print(f"[MultiURLDialog.emit_updated_urls] Error: {e}")

    def extract_valid_urls(text):
        url_pattern = re.compile(
            r'(?i)\b((?:https?://|www\.)[^\s<>"]+|youtu\.be/[^\s<>"]+|youtube\.com/[^\s<>"]+)'
        )
        raw_urls = url_pattern.findall(text)
        valid_urls = []
        for url in raw_urls:
            if url.startswith("www."):
                url = "https://" + url
            if any(d in url for d in ("youtube.com", "youtu.be")) and " " not in url:
                valid_urls.append(url.strip())
        return valid_urls

    def fetch_meta_for_widget(self, widget):
        print(f"[FETCH] start {widget.get_url()}")
        url = widget.get_url()
        if not url:
            return
        if not is_supported_url(url):
            try:
                widget.set_meta("<span style='color:#e66;'>Unsupported URL</span>")
                QTimer.singleShot(2500, lambda: widget.set_meta(""))
            except Exception:
                pass
            return

        parent = getattr(self, "_owner", None) or self.parent()
        mgr = getattr(parent, "metadata_manager", None)

        if mgr and url in getattr(mgr, "failed", set()):
            print(f"[SKIP] Skipping previously failed URL: {url}")
            try:
                widget.set_meta("<span style='color:#e66;'>Invalid or failed video link</span>")
                if hasattr(widget, "checkbox"):
                    widget.checkbox.setChecked(False)
                if hasattr(widget, "line_edit"):
                    widget.line_edit.setEnabled(False)
            except Exception:
                pass
            return

        raw = url.strip()
        is_radio = ("list=RD" in raw) or ("start_radio=1" in raw)
        if is_radio:
            canon = canonicalize_youtube_url(raw)
            if "list=RD" not in canon:
                sep = '&' if '?' in canon else '?'
                canon = f"{canon}{sep}list=RD"
        else:
            canon = canonicalize_youtube_url(raw)

        def _canon_of_widget(w):
            try:
                t = (w.get_url() or "").strip()
                if not t:
                    return ""
                if ("list=RD" in t) or ("start_radio=1" in t):
                    c = canonicalize_youtube_url(t)
                    if "list=RD" not in c:
                        sep = '&' if '?' in c else '?'
                        c = f"{c}{sep}list=RD"
                    return c
                return canonicalize_youtube_url(t)
            except Exception:
                return ""

        duplicates = [w for w in self.line_widgets if w is not widget and _canon_of_widget(w) == canon]
        if duplicates:
            try:
                widget.line_edit.clear()
            except Exception:
                pass
            parent = getattr(self, "_owner", None)
            if parent and hasattr(parent, "progress_bar"):
                try:
                    parent.progress_bar.setFormat("⚠️ Duplicate URL ignored")

                    def _reset_after_duplicate():
                        if getattr(parent, "_still_loading_meta", False):
                            return
                        parent.progress_bar.setFormat("Ready to download...")

                    QTimer.singleShot(2000, _reset_after_duplicate)
                except Exception:
                    pass

            if self.line_widgets and self.line_widgets[-1].is_empty():
                last = self.line_widgets[-1]
                try:
                    self.line_widgets.remove(last)
                    last.setParent(None)
                    last.deleteLater()
                except Exception:
                    pass
            return

        parent = getattr(self, "_owner", None) or self.parent()
        if parent and hasattr(parent, 'metadata_manager'):
            mgr = parent.metadata_manager
        else:
            if not hasattr(self, '_local_metadata_manager'):
                self._local_metadata_manager = MetadataManager()
            mgr = self._local_metadata_manager

        if not hasattr(self, "_mgr_callbacks"):
            self._mgr_callbacks = {}
        old_cb = self._mgr_callbacks.pop(widget, None)
        if old_cb:
            try:
                old_mgr, old_on_fetched, old_on_error, old_on_status, old_expected = old_cb
                try:
                    old_mgr.resolutions_fetched.disconnect(old_on_fetched)
                except Exception:
                    pass
                try:
                    old_mgr.error.disconnect(old_on_error)
                except Exception:
                    pass
                try:
                    old_mgr.status_update.disconnect(old_on_status)
                except Exception:
                    pass
                if hasattr(old_mgr, "cancel") and old_expected:
                    try:
                        old_mgr.cancel(old_expected)
                    except Exception:
                        pass
            except Exception:
                pass

        if parent and hasattr(parent, "download_btn"):
            parent.download_btn.setEnabled(False)
        try:
            if parent and hasattr(parent, "progress_bar"):
                parent.progress_bar.setFormat("Loading video info...")
        except Exception:
            pass

        if canon in mgr.cache:
            data = mgr.cache[canon]
            if data.get("is_playlist") and data.get("is_radio_playlist"):
                title = data.get("title", "Radio/Mix")
                track_count = len(data.get("urls", []))
                widget.set_meta(f"Title: {title} | Tracks: {track_count}")
            else:
                duration = data.get("duration", 0)
                mins, secs = int(duration // 60), int(duration % 60)
                resolutions = data.get("resolutions", [])
                best = resolutions[0] if resolutions else "N/A"
                widget.set_meta(f"Title: {data.get('title','Unknown')} | Duration: {mins:02d}:{secs:02d} | Best: {best}")
            try:
                if hasattr(self, "_loading_timers") and widget in self._loading_timers:
                    t = self._loading_timers.pop(widget)
                    t.stop()
            except Exception:
                pass
            p = getattr(self, "_owner", None) or self.parent()
            try:
                if p and not getattr(p, "_still_loading_meta", False):
                    if hasattr(p, "progress_bar"):
                        p.progress_bar.setFormat("Ready to download...")
                    if hasattr(p, "video_info_label"):
                        p.video_info_label.setText("Ready to download...")

                if parent and hasattr(parent, "download_btn"):
                    if not getattr(parent, "_still_loading_meta", False):
                        parent.download_btn.setEnabled(True)
            except Exception:
                pass

            return

        spinner_index = 0
        try:
            widget.set_meta(f"{spinner_frame(spinner_index)} Loading video info.")
        except RuntimeError:
            pass
        timer = QTimer(self)

        expected_url = canonicalize_youtube_url(canon)

        def on_fetched(url_sig, data):
            if url_sig != expected_url:
                return
            print(f"[FETCHED] {url_sig}: {data.get('title', 'N/A')}...")
            try:
                if data.get("is_playlist") and data.get("is_radio_playlist"):
                    title = data.get("title", "Radio/Mix")
                    track_count = len(data.get("urls", []))
                    widget.set_meta(f"Title: {title} | Tracks: {track_count}")
                else:
                    duration = data.get("duration", 0)
                    mins, secs = int(duration // 60), int(duration % 60)
                    resolutions = data.get("resolutions", [])
                    best = resolutions[0] if resolutions else "N/A"
                    widget.set_meta(f"Title: {data.get('title','Unknown')} | Duration: {mins:02d}:{secs:02d} | Best: {best}")
            except Exception:
                pass
            if timer.isActive():
                timer.stop()
            try:
                if hasattr(self, "_loading_timers") and widget in self._loading_timers:
                    self._loading_timers.pop(widget, None)
            except Exception:
                pass

        def on_error(url_sig, error_msg):
            if url_sig != expected_url:
                return
            print(f"[ERROR] {url_sig}: {error_msg}")
            try:
                widget.set_meta(f"Error: {error_msg[:50]}")
            except Exception:
                pass
            if timer.isActive():
                timer.stop()
            if mgr and hasattr(mgr, "failed"):
                mgr.failed.add(url)
            try:
                if hasattr(widget, "checkbox"):
                    widget.checkbox.setChecked(False)
                if hasattr(widget, "line_edit"):
                    widget.line_edit.setEnabled(False)
            except Exception:
                pass
            try:
                if hasattr(self, "_loading_timers") and widget in self._loading_timers:
                    self._loading_timers.pop(widget, None)
            except Exception:
                pass

        def on_status(url_sig, status_msg):
            if url_sig != expected_url:
                return
            print(f"[STATUS] {url_sig}: {status_msg}")
            if "Ready to download" in status_msg:
                if timer.isActive():
                    timer.stop()
                try:
                    if hasattr(self, "_loading_timers") and widget in self._loading_timers:
                        self._loading_timers.pop(widget, None)
                except Exception:
                    pass

        def spinner_tick():
            nonlocal spinner_index
            if widget and widget.meta_label:
                try:
                    spinner_index = (spinner_index + 1) % len(SPINNER_FRAMES)
                    widget.set_meta(f"{spinner_frame(spinner_index)} Loading video info...")
                except RuntimeError:
                    timer.stop()
                    try:
                        if hasattr(self, "_loading_timers") and widget in self._loading_timers:
                            self._loading_timers.pop(widget, None)
                    except Exception:
                        pass

        timer.timeout.connect(spinner_tick)
        timer.start(SPINNER_INTERVAL)

        try:
            if not hasattr(self, "_loading_timers"):
                self._loading_timers = {}
            self._loading_timers[widget] = timer
        except Exception:
            pass

        mgr.resolutions_fetched.connect(on_fetched)
        mgr.error.connect(on_error)
        mgr.status_update.connect(on_status)

        self._mgr_callbacks[widget] = (mgr, on_fetched, on_error, on_status, expected_url)

        if "list=RD" in canon or "start_radio=1" in canon:
            print("[META] forcing radio mode fetch (clean URL)")
            clean_url = canonicalize_youtube_url(canon).split("&list=RD")[0].strip()
            mgr.request(clean_url)
        else:
            mgr.request(expected_url)

        def on_timeout():
            nonlocal spinner_index
            spinner_index += 1
            try:
                widget.set_meta(f"{spinner_frame(spinner_index)} Loading video info...")
            except RuntimeError:
                pass

        timer.timeout.connect(on_timeout)
        timer.start(SPINNER_INTERVAL)
        if not hasattr(self, '_loading_timers'):
            self._loading_timers = {}
        self._loading_timers[widget] = timer

        expected = canon

        def _widget_current_canon_matches():
            try:
                return _canon_of_widget(widget) == expected
            except Exception:
                return False
        if not hasattr(mgr, "_done_widgets"):
            mgr._done_widgets = set()

        def on_fetched(u, data):
            print(f"[FETCHED] got {u}")
            mgr._done_widgets.add(expected)
            try:
                mgr.status_update.disconnect(on_status)
            except Exception:
                pass

            if "list=RD" in u:
                title = str(data.get("title", "")).lower()
                urls_in_data = data.get("urls", [])
                if (
                    not data.get("is_radio_playlist")
                    and (
                        "líbí se" in title
                        or "like this video" in title
                        or "mix" not in title
                        or len(urls_in_data) <= 1
                    )
                ):
                    print("[SKIP] Ignoring RD placeholder metadata")
                    return

            same_base = u.split("&list=")[0] == expected.split("&list=")[0]
            if (u != expected and not same_base) or u in getattr(mgr, "_cancelled", set()):
                return
            if not _widget_current_canon_matches():
                return

            if widget not in self.line_widgets:
                try:
                    mgr.resolutions_fetched.disconnect(on_fetched)
                    mgr.error.disconnect(on_error)
                    mgr.status_update.disconnect(on_status)
                except Exception:
                    pass
                self._mgr_callbacks.pop(widget, None)
                return
            try:
                timer.stop()
            except Exception:
                pass
            self._loading_timers.pop(widget, None)

            if data.get("is_radio_playlist"):
                try:
                    title = data.get("title", "Radio/Mix playlist")
                    count = len(data.get("urls", []))
                    widget.set_meta(f"{title} | {count} items (radio mix)")
                except RuntimeError:
                    pass
                if parent and hasattr(parent, "download_btn"):
                    try:
                        if not getattr(parent, "_still_loading_meta", False):
                            parent.download_btn.setEnabled(True)
                            parent.progress_bar.setFormat("Ready to download...")
                    except Exception:
                        pass

                mgr._cancelled.add(expected)
                return

            title = data.get("title", "Unknown")
            duration = data.get("duration", 0)
            mins, secs = int(duration // 60), int(duration % 60)
            resolutions = data.get("resolutions", [])
            best = resolutions[0] if resolutions else "N/A"

            try:
                widget.set_meta(f"Title: {title} | Duration: {mins:02d}:{secs:02d} | Best: {best}")
            except RuntimeError:
                pass

            if parent and hasattr(parent, "download_btn"):
                try:
                    if not getattr(parent, "_still_loading_meta", False):
                        parent.download_btn.setEnabled(True)
                        parent.progress_bar.setFormat("Ready to download...")
                except Exception:
                    pass

        def on_error(u, msg):
            if u != expected:
                return
            if not _widget_current_canon_matches():
                return
            try:
                if not hasattr(mgr, "_done_widgets"):
                    mgr._done_widgets = set()
                mgr._done_widgets.add(expected)
            except Exception:
                pass
            try:
                timer.stop()
            except Exception:
                pass
            try:
                self._loading_timers.pop(widget, None)
            except Exception:
                pass
            try:
                if mgr:
                    mgr.cache.pop(u, None)
                    if not hasattr(mgr, "failed"):
                        mgr.failed = set()
                    mgr.failed.add(u)
                    if hasattr(mgr, "_cancelled"):
                        mgr._cancelled.add(u)
            except Exception:
                pass
            try:
                if parent and hasattr(parent, "urls_to_download"):
                    parent.urls_to_download = [
                        x for x in parent.urls_to_download
                        if canonicalize_youtube_url(x) != canonicalize_youtube_url(u)
                    ]
            except Exception:
                pass
            msg_text = str(msg).strip().lower()
            if "private" in msg_text:
                short_msg = "<span style='color:#e66;'>Private or restricted video</span>"
            else:
                short_msg = "<span style='color:#e66;'>Invalid / unavailable video</span>"

            try:
                widget.set_meta(short_msg)
                if hasattr(widget, "checkbox"):
                    widget.checkbox.setChecked(False)
                    widget.checkbox.setEnabled(False)
                if hasattr(widget, "line_edit"):
                    widget.line_edit.setEnabled(False)
            except Exception:
                pass
            try:
                remaining = [
                    e for e in getattr(parent, "saved_multilist", [])
                    if e.get("checked") and canonicalize_youtube_url(e["url"]) not in getattr(mgr, "failed", set())
                ]
                if not remaining:
                    parent._still_loading_meta = False
                    if hasattr(parent, "video_info_label"):
                        parent.video_info_label.setText("No valid videos.")
                    if hasattr(parent, "progress_bar"):
                        parent.progress_bar.setFormat("Error")
                    if hasattr(parent, "download_btn"):
                        parent.download_btn.setEnabled(False)
            except Exception:
                pass

        def on_status(u, text):
            if expected in getattr(mgr, "_done_widgets", set()):
                return
            try:
                norm_u = canonicalize_youtube_url(u)
                expected_norm = canonicalize_youtube_url(expected)
                if norm_u != expected_norm:
                    return
            except Exception:
                pass
            if not _widget_current_canon_matches():
                return
            try:
                clean_text = (text or "").strip().lower()
                if clean_text.startswith("ready"):
                    try:
                        if widget in self._loading_timers:
                            t = self._loading_timers.pop(widget)
                            t.stop()
                    except Exception:
                        pass
                    widget.clear_meta()
                    p = getattr(self, "_owner", None) or self.parent()
                    try:
                        if p and hasattr(p, "progress_bar"):
                            p.progress_bar.setFormat("Ready to download...")
                        if p and hasattr(p, "video_info_label"):
                            p.video_info_label.setText("Ready to download...")
                    except Exception:
                        pass
                    return
                widget.set_meta(f"{spinner_frame(spinner_index)} {text}")
            except RuntimeError:
                pass
        try:
            p = getattr(self, "_owner", None) or self.parent()
            if p and hasattr(p, "progress_bar"):
                p.progress_bar.setFormat("Loading video info...")
                p.progress_bar.setValue(0)
        except Exception:
            pass

        mgr.resolutions_fetched.connect(on_fetched)
        mgr.error.connect(on_error)
        mgr.status_update.connect(on_status)
        self._mgr_callbacks[widget] = (mgr, on_fetched, on_error, on_status, expected)

        if "list=RD" in canon or "start_radio=1" in canon:
            print("[META] forcing radio mode fetch (clean URL)")
            clean_url = canonicalize_youtube_url(canon).split("&list=RD")[0].strip()
            mgr.request(clean_url)
        else:
            mgr.request(canonicalize_youtube_url(canon))

    def on_line_edited(self, widget):
        if widget is getattr(self, "first_line", None):
            if widget.is_empty():
                self.check_and_remove_empty_line_if_only_first()
            else:
                self.fetch_meta_for_widget(widget)
        else:
            if self.line_widgets and widget is self.line_widgets[-1] and not widget.is_empty():
                self.add_line()
            if not widget.is_empty():
                self.fetch_meta_for_widget(widget)
            else:
                widget.clear_meta()
        self.update_remove_buttons()
        self.emit_updated_urls()

    def accept(self):
        try:
            entries = []

            # sebereme URL z vytvořených combi řádků
            for row in self.rows:
                try:
                    url = (row.url or "").strip()
                except Exception:
                    url = ""

                if not url:
                    continue

                checked = True
                try:
                    if row.checkbox:
                        checked = row.checkbox.isChecked()
                except Exception:
                    pass

                entries.append({"url": url, "checked": checked})

            urls = [e["url"] for e in entries]

            parent = getattr(self, "_owner", None)

            if parent and hasattr(parent, "progress_bar"):
                try:
                    mgr = getattr(parent, "metadata_manager", None)
                    urls_norm = [canonicalize_youtube_url(u) for u in urls]

                    if not urls_norm:
                        parent.progress_bar.setFormat("Ready...")
                        parent.progress_bar.setValue(0)

                        if hasattr(parent, "download_btn"):
                            parent.download_btn.setEnabled(False)
                        if hasattr(parent, "set_combos_enabled"):
                            parent.set_combos_enabled(False)
                        if hasattr(parent, "video_info_label"):
                            parent.video_info_label.setText("")

                    else:
                        all_cached = False
                        if mgr:
                            try:
                                cache = getattr(mgr, "cache", {})
                                all_cached = all(
                                    canonicalize_youtube_url(u) in cache
                                    for u in urls_norm
                                )
                            except Exception:
                                all_cached = False

                        if all_cached:
                            parent.progress_bar.setFormat("Ready to download...")
                            if hasattr(parent, "download_btn"):
                                parent.download_btn.setEnabled(True)
                            if hasattr(parent, "set_combos_enabled"):
                                parent.set_combos_enabled(True)
                            if hasattr(parent, "video_info_label"):
                                parent.video_info_label.setText("Ready to download...")
                        else:
                            parent.progress_bar.setFormat("Loading video info...")
                            parent.progress_bar.setValue(0)
                            if hasattr(parent, "download_btn"):
                                parent.download_btn.setEnabled(False)
                            if hasattr(parent, "set_combos_enabled"):
                                parent.set_combos_enabled(False)
                            if hasattr(parent, "video_info_label"):
                                parent.video_info_label.setText("Loading video info...")

                except Exception:
                    pass

            # zavolání callbacku
            if parent and hasattr(parent, "handle_multi_url_close"):
                try:
                    parent.handle_multi_url_close(entries)
                except Exception as e:
                    print(f"[MultiURLDialog.accept] handle_multi_url_close failed: {e}")

            # event + cleanup + zavření okna
            self.closed.emit(entries)
            self._cleanup_threads()
            self.close()

        except Exception as e:
            print(f"[MultiURLDialog.accept] Error: {e}")

    def reject(self):
        parent = getattr(self, "_owner", None)

        # --------------------------------------------------
        # 1) HARD CANCEL všech rozjetých metadata fetchů
        # --------------------------------------------------
        try:
            for row in getattr(self, "rows", []):
                try:
                    self.cancel_meta_fetch_for_widget(row)
                except Exception:
                    pass
        except Exception:
            pass

        # --------------------------------------------------
        # 2) Obnovení UI stavu (podle tvého vzoru)
        # --------------------------------------------------
        if parent and hasattr(parent, "progress_bar"):
            try:
                initial = []
                if hasattr(parent, "saved_multilist") and parent.saved_multilist:
                    initial = [
                        e.get("url", "")
                        for e in parent.saved_multilist
                        if e.get("url")
                    ]

                mgr = getattr(parent, "metadata_manager", None)
                initial_norm = [canonicalize_youtube_url(u) for u in initial]

                if not initial_norm:
                    parent.progress_bar.setFormat("Ready...")
                    parent.progress_bar.setValue(0)

                    if hasattr(parent, "download_btn"):
                        parent.download_btn.setEnabled(False)
                    if hasattr(parent, "set_combos_enabled"):
                        parent.set_combos_enabled(False)
                    if hasattr(parent, "video_info_label"):
                        parent.video_info_label.setText("")

                else:
                    all_cached = False
                    if mgr:
                        try:
                            all_cached = all(
                                u in getattr(mgr, "cache", {})
                                for u in initial_norm
                            )
                        except Exception:
                            all_cached = False

                    if all_cached:
                        parent.progress_bar.setFormat("Ready to download...")
                        if hasattr(parent, "download_btn"):
                            parent.download_btn.setEnabled(True)
                        if hasattr(parent, "set_combos_enabled"):
                            parent.set_combos_enabled(True)
                        if hasattr(parent, "video_info_label"):
                            parent.video_info_label.setText("Ready to download...")
                    else:
                        parent.progress_bar.setFormat("Loading video info...")
                        parent.progress_bar.setValue(0)
                        if hasattr(parent, "download_btn"):
                            parent.download_btn.setEnabled(False)
                        if hasattr(parent, "set_combos_enabled"):
                            parent.set_combos_enabled(False)
                        if hasattr(parent, "video_info_label"):
                            parent.video_info_label.setText("Loading video info...")

            except Exception:
                pass

        # --------------------------------------------------
        # 3) Vrácení původního stavu + zavření dialogu
        # --------------------------------------------------
        try:
            if hasattr(parent, "saved_multilist"):
                self.closed.emit(parent.saved_multilist)
            else:
                self.closed.emit([])
        except Exception:
            pass

        self.close()


    def cancel_meta_fetch_for_widget(self, widget):
        # --------------------------------------------------
        # 1) Zastavení loading timeru (pokud existuje)
        # --------------------------------------------------
        timer = getattr(self, "_loading_timers", {}).pop(widget, None)
        if timer:
            try:
                timer.stop()
            except Exception:
                pass

        # --------------------------------------------------
        # 2) Odpojení metadata manager callbacků + cancel
        # --------------------------------------------------
        cb = getattr(self, "_mgr_callbacks", {}).pop(widget, None)
        if cb:
            mgr, on_fetched, on_error, on_status, expected_url = cb

            if mgr and hasattr(mgr, "cancel"):
                try:
                    mgr.cancel(expected_url)
                except Exception:
                    pass

            try:
                mgr.resolutions_fetched.disconnect(on_fetched)
            except Exception:
                pass
            try:
                mgr.error.disconnect(on_error)
            except Exception:
                pass
            try:
                mgr.status_update.disconnect(on_status)
            except Exception:
                pass

        # --------------------------------------------------
        # 3) Kill threadu (pokud byl ještě někde použit)
        #    – bezpečně, bez pádu
        # --------------------------------------------------
        thread = getattr(self, "info_threads", {}).pop(widget, None)
        if thread:
            try:
                if thread.isRunning():
                    thread.terminate()
            except Exception:
                pass

        # --------------------------------------------------
        # 4) Vyčištění UI metadat (spinner / text / label)
        # --------------------------------------------------
        try:
            if hasattr(widget, "clear_meta"):
                widget.clear_meta()
        except Exception:
            pass


class RoundedProgressBar(QProgressBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTextVisible(True)
        self.setStyleSheet("QProgressBar { border: none; background: transparent; color: white; }")

    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionProgressBar()
        self.initStyleOption(opt)
        rect = self.rect()
        bg_rect = rect.adjusted(1, 1, -1, -1)
        outer_radius = 10
        chunk_radius = 9
        border_color = QColor("#555")
        bg_color = QColor("#404040")
        chunk_color = QColor("#2a82da")
        text_color = QColor("#cccccc")
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = painter.pen()
        pen.setColor(border_color)
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(bg_rect, outer_radius, outer_radius)
        inner_rect = bg_rect.adjusted(1, 1, -1, -1)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(inner_rect, outer_radius - 1, outer_radius - 1)
        if self.maximum() > self.minimum():
            progress = (self.value() - self.minimum()) / (self.maximum() - self.minimum())
        else:
            progress = 0.0
        progress = max(0.0, min(1.0, progress))
        progress_area = inner_rect.adjusted(1, 0, -1, 0)
        fill_rect = QRect(progress_area)
        fill_rect = fill_rect.adjusted(0, 1, 0, -1)
        min_vis_width = max(2 * chunk_radius, 12)
        target_width = int(progress_area.width() * progress)   
        if 0 < target_width < min_vis_width:
            target_width = min(min_vis_width, progress_area.width())
        fill_rect.setWidth(target_width)
        if target_width > 0:
            painter.setBrush(chunk_color)
            painter.drawRoundedRect(fill_rect, chunk_radius, chunk_radius)
        painter.setPen(text_color)
        if opt.textVisible:
            painter.drawText(inner_rect, Qt.AlignmentFlag.AlignCenter, opt.text)

class ProgressAggregator(QObject):
    overall_progress = pyqtSignal(int, str)

    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
        self._percents = {}
        self._last_emit = None
        self._last_text = None
        self._current_index = 0

    def register_urls(self, urls, initial_text="Preparing downloads…"):
        with self._lock:
            urls = urls or []
            self._percents = {u: 0 for u in urls}
            self._last_emit = None
            self._last_text = None
            total = len(self._percents)
            self._current_index = 1 if total > 0 else 0
            try:
                txt = f"{self._current_index}/{total} | 0% | {initial_text}" if total > 0 else "Ready to download…"
                self.overall_progress.emit(0, txt)
            except Exception:
                pass

    def update(self, url, percent, txt=None):
        if url is None:
            return
        with self._lock:
            if url not in self._percents:
                self._percents[url] = 0
                if self._current_index == 0:
                    self._current_index = 1
            p = max(0, min(100, int(round(percent))))
            self._percents[url] = p
            self._emit_current(extra_text=txt)

    def set_done(self, url=None):
        with self._lock:
            total = len(self._percents)
            if url is None:
                for k in self._percents:
                    self._percents[k] = 100
                self._current_index = total
            else:
                if url in self._percents:
                    self._percents[url] = 100
                    keys = list(self._percents.keys())
                    try:
                        idx = keys.index(url) + 1 
                    except ValueError:
                        idx = None
                    if idx is not None and idx >= self._current_index:
                        self._current_index = min(total, self._current_index + 1)
            self._emit_current(extra_text="Done")

    def reset(self):
        with self._lock:
            self._percents.clear()
            self._last_emit = None
            self._last_text = None
            self._current_index = 0
            try:
                self.overall_progress.emit(0, "Ready to download…")
            except Exception:
                pass

    def _emit_current(self, extra_text=None):
        total = len(self._percents)
        if total == 0:
            val = 0
            base = "0/0"
        else:
            s = sum(self._percents.values())
            val = int(round(s / total))
            cur = min(max(1, self._current_index), total)
            base = f"{cur}/{total}"
        text = base
        if val == self._last_emit and text == self._last_text:
            return
        self._last_emit = val
        self._last_text = text
        try:
            self.overall_progress.emit(val, text)
        except Exception:
            pass

class YouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
    
        self.config_manager = ConfigManager()
        self.yt_dlp_path = YTDLP_PATH
        self.ffmpeg_path = FFMPEG_PATH
        missing = check_dependencies()
        if missing:
            QMessageBox.critical(
                self,
                "Missing Dependency",
                f"The required file '{missing}' was not found.\nThe application will now exit."
            )
            sys.exit(1)

        self.setWindowTitle("Ultimate video downloader v1.0")
        self.setFixedSize(750, 560)
        self.default_resolutions = ["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p"]
        self.compression_presets = ["Original (without compression)", "Very High Quality (low compression)", "High Quality (Compressed)", "Medium Quality", "Low Quality", "Very Low Quality"]
        self.mp3_bitrates = ["320", "256", "192", "128", "96"]
        self.video_info = {}
        self.download_thread, self.info_thread = None, None
        self.urls_to_download = []
        self.meta_load_times = []
        self.metadata_manager = MetadataManager()
        videos_path = Path.home() / "Videos"
        self.save_path = str((videos_path if videos_path.exists() else Path.home() / "Downloads") / "YTDownloads")
        os.makedirs(self.save_path, exist_ok=True)
        self.config_manager = ConfigManager()
        self.session_manager = None
        self.last_url_for_retry = None
        self.is_retrying = False
        self._cancelled_by_user = False
        self.init_ui()
        self.progress_bar.setFormat("Ready...")
        self.progress_bar.setValue(0)
        self.set_combos_enabled(False)
        app.setStyleSheet("QPushButton:focus { outline: none; } QToolButton:focus { outline: none; }")
        self.download_btn.setEnabled(False)
        self.log_checkbox.setEnabled(True)

    def center_on_screen(self):
        frameGm = self.frameGeometry()
        screen = QApplication.primaryScreen().availableGeometry().center()
        frameGm.moveCenter(screen)
        self.move(frameGm.topLeft())

    def closeEvent(self, event):
        import psutil, os, signal

        try:
            # 🟥 Kill yt-dlp / ffmpeg procesů
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    name = proc.info['name'] or ""
                    cmd = " ".join(proc.info.get('cmdline') or [])

                    if ("yt-dlp" in name.lower() or
                        "ffmpeg" in name.lower() or
                        "ffprobe" in name.lower() or
                        "yt-dlp" in cmd or
                        "ffmpeg" in cmd):
                        proc.kill()
                except:
                    pass
        except:
            pass

        # 🧨 ULTIMATE EXIT: okamžitý konec procesu
        os._exit(0)



    def show_youtube_login_required(self):
        QMessageBox.information(
            self,
            "YouTube login required",
            "To fix this download, please sign in to YouTube in your browser.\n\n"
            "Any Google/YouTube account works. After signing in, retry the download."
        )

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self._last_single_url = ""

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 0)

        # --------------------------
        # Title
        # --------------------------
        title_label = QLabel(f"🎬 {self.windowTitle()}")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #398ee3; margin-bottom: 10px;"
        )
        main_layout.addWidget(title_label)

        # --------------------------
        # URL Group
        # --------------------------
        self.url_group = QGroupBox("🎞 Video Source ")
        url_layout = QVBoxLayout(self.url_group)
        url_input_layout = QHBoxLayout()
        self.url_input = QLineEdit(
            placeholderText="Enter a YouTube URL and press Enter, or use buttons..."
        )
        self.url_input.setClearButtonEnabled(True)
        if hasattr(self, "paste_btn"):
            self.paste_btn.setEnabled(True)
        self.url_input.returnPressed.connect(self.fetch_video_info)
        self.url_input.textChanged.connect(self.on_url_text_changed)
        self.btn_paste = QPushButton("Paste URL", clicked=self.paste_url)
        self.btn_multi_url = QPushButton("Multiple URLs", clicked=self.open_multi_url_dialog)
        url_input_layout.addWidget(self.url_input)
        url_input_layout.addWidget(self.btn_paste)
        url_input_layout.addWidget(self.btn_multi_url)
        url_layout.addLayout(url_input_layout)

        self.video_info_label = QLabel("")
        self.video_info_label.setStyleSheet("color: #aaa; font-style: italic; font-size: 11px;")
        self.video_info_label.setWordWrap(True)
        url_layout.addWidget(self.video_info_label)
        main_layout.addWidget(self.url_group)
        self.video_info_label.setWordWrap(False)

        # --------------------------
        # Download Settings (pevná výška, zarovnané popisky)
        # --------------------------
        settings_group = QGroupBox("📝 Download Settings ")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setContentsMargins(8, 0, 8, 6)
        settings_layout.setSpacing(8)
        self.settings_stack = QStackedWidget()

        # MP4 panel
        mp4_panel = QWidget()
        mp4_layout = QGridLayout(mp4_panel)
        mp4_layout.setContentsMargins(0, 0, 0, 0)
        mp4_layout.setVerticalSpacing(10)

        # Formát (nahoru)
        lbl_format = QLabel("Format:")
        lbl_format.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        mp4_layout.addWidget(lbl_format, 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4 (video+audio)", "MP3"])
        mp4_layout.addWidget(self.format_combo, 0, 1)
        self.format_combo.setFixedWidth(self.format_combo.sizeHint().width() + 195)

        # Video kvalita
        lbl_quality = QLabel("Video Quality:")
        lbl_quality.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        mp4_layout.addWidget(lbl_quality, 1, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(self.default_resolutions)
        self.quality_combo.setCurrentText("1080p")
        mp4_layout.addWidget(self.quality_combo, 1, 1)

        # Komprese
        lbl_compression = QLabel("Compression:")
        lbl_compression.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        mp4_layout.addWidget(lbl_compression, 2, 0)
        self.compression_combo = QComboBox()
        self.compression_combo.addItems(self.compression_presets)
        mp4_layout.addWidget(self.compression_combo, 2, 1)

        # MP3 panel
        mp3_panel = QWidget()
        mp3_layout = QGridLayout(mp3_panel)
        mp3_layout.setContentsMargins(0, 0, 0, 0)
        mp3_layout.setVerticalSpacing(15)

        lbl_format2 = QLabel("Format:")
        lbl_format2.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        mp3_layout.addWidget(lbl_format2, 0, 0)

        # teď stejný seznam jako hlavní format_combo
        self.format_combo2 = QComboBox()
        self.format_combo2.addItems(["MP4 (video+audio)", "MP3"])
        self.format_combo2.setCurrentText("MP3")
        mp3_layout.addWidget(self.format_combo2, 0, 1)
        
        lbl_bitrate = QLabel("MP3 Bitrate (kbps):")
        lbl_bitrate.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        mp3_layout.addWidget(lbl_bitrate, 1, 0)
        self.mp3_bitrate_combo = QComboBox()
        self.mp3_bitrate_combo.addItems(self.mp3_bitrates)
        self.mp3_bitrate_combo.setCurrentText("320")
        mp3_layout.addWidget(self.mp3_bitrate_combo, 1, 1)
        self.mp3_bitrate_combo.setFixedWidth(self.mp3_bitrate_combo.sizeHint().width() + 278)
        mp3_layout.setContentsMargins(0, 3, 0, 0)

        # filler pro výšku
        filler = QWidget()
        filler.setMinimumHeight(
            self.quality_combo.sizeHint().height()
            + self.compression_combo.sizeHint().height()
            + 12
        )
        mp3_layout.addWidget(filler, 2, 0, 1, 2)
        
        # propojení přepínání
        def _on_format2_changed(idx):
            selected = self.format_combo2.currentText()
            self.format_combo.setCurrentText(selected)
            if selected.startswith("MP4"):
                self.settings_stack.setCurrentIndex(0)
            else:
                self.settings_stack.setCurrentIndex(1)
        self.format_combo2.currentIndexChanged.connect(_on_format2_changed)

        # Stack
        self.settings_stack.addWidget(mp4_panel)
        self.settings_stack.addWidget(mp3_panel)
        STACK_H = max(mp4_panel.sizeHint().height(), mp3_panel.sizeHint().height(), 160)
        self.settings_stack.setFixedHeight(STACK_H)
        settings_layout.addWidget(self.settings_stack)
        main_layout.addWidget(settings_group)

        # Přepínání formátu
        def _on_format_changed(idx):
            is_mp4 = self.format_combo.currentText().startswith("MP4")
            self.settings_stack.setCurrentIndex(0 if is_mp4 else 1)
        self.format_combo.currentIndexChanged.connect(_on_format_changed)
        self.update_ui_visibility = lambda: _on_format_changed(self.format_combo.currentIndex())
        self.update_ui_visibility()

        # --------------------------
        # Progress bar a tlačítka
        # --------------------------
        self.progress_bar = RoundedProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Ready to download...")
        self.progress_bar.setFixedHeight(32)
        main_layout.addWidget(self.progress_bar)
        self.progress_bar.setStyleSheet("QProgressBar { border: none; background: transparent; color: white; }")

        btn_layout = QHBoxLayout()
        self.folder_btn = QPushButton(
            f".../{os.path.basename(self.save_path)} 📁", clicked=self.select_folder
        )
        self.download_btn = QPushButton(
            "Download ⬇️", clicked=self.start_or_cancel_download
        )
        btn_layout.addWidget(self.folder_btn)
        btn_layout.addWidget(self.download_btn)
        main_layout.addLayout(btn_layout)
        # 🟢 OPRAVENO — spusti se jen když je povolený update v INI
        try:
            if self.config_manager and self.config_manager.get_yt_dlp_update():
                update_thread = threading.Thread(
                    target=check_and_update_ytdlp,
                    args=(self,),
                    daemon=True
                )
                update_thread.start()
            else:
                pass  # Update disabled → nic se neloguje tady
        except Exception as e:
            print(f"[AutoFix] Could not read yt_dlp_update flag: {e}")

        # --------------------------
        # GPU Info + Log checkbox
        # --------------------------
        info_layout = QHBoxLayout()
        gpu_mode, gpu_encoder = check_gpu_support()
        mode_labels = {
            "qsv": "Intel QSV",
            "nvenc": "NVIDIA NVENC",
            "amf": "AMD AMF",
            "vaapi": "VAAPI",
            "videotoolbox": "VideoToolbox",
            "cpu": "CPU Only",
        }
        gpu_text = mode_labels.get(gpu_mode, "Unknown")
        if gpu_mode != "cpu":
            gpu_text = f"{gpu_text} ({gpu_encoder})"
        gpu_info = QLabel(f"Encoding by: {gpu_text}")
        gpu_info.setStyleSheet(
            "color: #aaa; font-size: 10px; padding-left: 1px; margin-bottom: 12px;"
        )
        gpu_info.setAlignment(Qt.AlignmentFlag.AlignLeft)
        info_layout.addWidget(gpu_info)
        info_layout.addStretch(1)

        self.log_checkbox = QCheckBox("Log")
        self.log_checkbox.setToolTip(
            "Zapne nebo vypne ukládání logu (soubor log.txt ve složce programu)"
        )
        self.log_checkbox.setStyleSheet(
            "QCheckBox{ color:#aaa; font-size:10px; font-weight:bold; padding-left:1px; "
            "margin-bottom:12px; margin-right: 5px; }"
            "QCheckBox::indicator{ width:18px; height:18px; border:2px solid #555; "
            "border-radius:4px; background:#2d2d2d; }"
            "QCheckBox::indicator:hover{ border-color:#6a9bd8; }"
            "QCheckBox::indicator:checked{ background:rgba(66,133,244,1); "
            "border-color:#2a82da; }"
        )

        logging_enabled = self.config_manager.get_logging_enabled()
        self.log_checkbox.blockSignals(True)
        self.log_checkbox.setChecked(logging_enabled)
        self.log_checkbox.blockSignals(False)

        if logging_enabled:
            enable_logging()
        else:
            disable_logging()

        def on_log_state_changed():
            enabled = self.log_checkbox.isChecked()
            self.config_manager.set_logging_enabled(enabled)
            if enabled:
                enable_logging()
                print("[LOG] Logging enabled")
            else:
                disable_logging()
                print("[LOG] Logging disabled")

        self.log_checkbox.stateChanged.connect(lambda _: on_log_state_changed())
        info_layout.addWidget(self.log_checkbox)
        main_layout.addLayout(info_layout)
        self.load_config()

        # ✔ OPRAVENO — správné volání s argumentem self
        update_thread = threading.Thread(
            target=check_and_update_ytdlp,
            args=(self,),
            daemon=True
        )
        update_thread.start()

        self.update_ui_visibility()
        self.setStyleSheet(self.get_stylesheet())

    def load_config(self):
        try:
            self._yt_update_enabled = self.config.get_yt_dlp_update()
        except Exception:
            self._yt_update_enabled = True

    def save_config(self):
        try:
            current_state = self.config_manager.get_yt_dlp_update()
            self.config_manager.set_yt_dlp_update(current_state)
        except Exception as e:
            print(f"[Config] Chyba při ukládání konfigurace: {e}")

    def closeEvent(self, event):
        """Zajistí uložení konfigurace při zavření aplikace."""
        self.save_config()
        super().closeEvent(event)

    def refresh_session_and_retry(self):
        if self.session_manager is None:
            self.session_manager = _SESSION_MANAGER
        self.progress_bar.setFormat("Ban detected. Attempting to refresh session...")
        QApplication.processEvents()
        try:
            self.session_manager.createsessionfromurl("https://www.youtube.com", namesession="default", headless=True, waitms=4000)
            self.progress_bar.setFormat("Session refreshed. Retrying download...")
            if self.last_url_for_retry:
                self.fetch_video_info(force_url=self.last_url_for_retry) 
        except Exception as e:
            self.is_retrying = False 
            show_download_error_message(self, original_error=f"Session refresh failed: {e}")

    def set_loading_ui(self, frame):
        try:
            txt = f"{frame}    Loading video info..."
            if hasattr(self, "video_info_label"):
                self.video_info_label.setText(txt)
            if hasattr(self, "progress_bar"):
                self.progress_bar.setFormat("Loading video info...")
                self.progress_bar.setValue(0)
        except Exception:
            pass

    def get_stylesheet(self):
        return """
            QMainWindow, QWidget { background-color: #2d2d2d; }
            QGroupBox { font-weight: bold; color: #fff; border: 2px solid #555; border-radius: 12px; margin-top: 8px; padding-top: 10px; min-height: 95px; }
            QGroupBox::title { color:#4b97e3; subcontrol-origin: margin; subcontrol-position: top left; padding: 0 8px; background-color: #2d2d2d; }
            QLabel { color: #bababa; font-size: 12px; font-weight: bold; }
            QLineEdit { background-color: #404040; border: 2px solid #555; border-radius: 12px; padding: 10px; color: #fff; font-size: 12px; }
            QLineEdit::clear-button { background-color: transparent; border: none; image: url(cross-icon.png); /* Fallback, styling is tricky */ }
            QComboBox { background-color: #404040; border: 2px solid #555; border-radius: 12px; padding: 10px; color: #fff; }
            QComboBox::disabled { color: #636363; } QComboBox::drop-down { border: none; } ComboBox::down-arrow { border: none; }
            QComboBox QAbstractItemView { color: #fff; border: 2px solid #555; border-radius: 10px; background-color: #404040; selection-background-color: #2a82da; }
            QPushButton { background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgb(122, 150, 230), stop:0.5 rgb(42, 130, 218), stop:1 rgb(24, 92,158)); border-radius: 12px; padding: 12px 16px; color: #fff; font-weight: bold; border: 2px solid #555; }
            QPushButton:hover { background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgb(85, 163, 235), stop:0.5 rgb(55, 140, 225), stop:1 rgb(35, 102, 168)); border: 2px solid #555; }
            QPushButton:pressed { background: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgb(20, 80, 140), stop:0.5 rgb(32, 110, 185), stop:1 rgb(50, 140, 210)); border: 2px solid #555;}
            QPushButton:disabled { background-color: #404040; color: #999; border: 2px solid #555; }
            QProgressBar { border: 2px solid #555; border-radius: 10px; text-align: center; background-color: #404040; color: white; font-weight: bold; }
        """
 
    def on_url_text_changed(self, text):
        text = text.strip()
        old_url = getattr(self, "_last_single_url", "").strip()

        if not text:
            # === ZDE JE OPRAVENÁ A FUNKČNÍ "KILL BILL" STOPKA ===

            # 1. OKAMŽITĚ zablokujeme tlačítko a resetujeme UI
            self.download_btn.setEnabled(False)
            self.download_btn.setStyleSheet(
                "QPushButton { opacity: 0.5; } QPushButton:disabled { opacity: 0.3; }"
            )
            self.video_info_label.setText("")
            self.progress_bar.setValue(0)
            self.reset_to_default_qualities()

            # 2. Zastavíme časovač animace, pokud běží
            if hasattr(self, "_loading_timer") and self._loading_timer:
                try:
                    self._loading_timer.stop()
                except Exception:
                    pass
                self._loading_timer = None

            # 3. Použijeme stejný systém rušení jako v multi režimu
            try:
                self.cancel_single_meta_fetch()
                print(f"[DEBUG GUI] cancel_single_meta_fetch() called for old URL: {old_url}")
            except Exception as e:
                print(f"[DEBUG GUI] cancel_single_meta_fetch() failed: {e}")

            try:
                has_other_urls = any(
                    getattr(w, "line_edit", None) and w.line_edit.text().strip()
                    for w in getattr(self, "url_widgets", [])
                )
            except Exception:
                has_other_urls = False

            if has_other_urls:
                self.progress_bar.setFormat("Ready to download...")
            else:
                self.progress_bar.setFormat("Ready...")

            QApplication.processEvents()
            print("[DEBUG GUI] Forced disable + visual fade")

        self._last_single_url = text
        self._check_and_update_ui_state()

    def cancel_single_meta_fetch(self):
        """
        Bezpečně zruší právě běžící fetch pro single URL (odpojí signály,
        zruší požadavek v metadata_manager, zastaví animaci a vyčistí UI).
        """
        try:
            if hasattr(self, "_loading_timer") and self._loading_timer:
                try:
                    if self._loading_timer.isActive():
                        self._loading_timer.stop()
                except Exception:
                    pass
                self._loading_timer = None
        except Exception:
            pass

        try:
            cb = getattr(self, "_single_mgr_callback", None)
            if cb:
                mgr, on_res, on_err, on_stat, expected = cb
                try:
                    if mgr and hasattr(mgr, "resolutions_fetched"):
                        mgr.resolutions_fetched.disconnect(on_res)
                except Exception:
                    pass
                try:
                    if mgr and hasattr(mgr, "error"):
                        mgr.error.disconnect(on_err)
                except Exception:
                    pass
                try:
                    if mgr and hasattr(mgr, "status_update"):
                        mgr.status_update.disconnect(on_stat)
                except Exception:
                    pass
                try:
                    if mgr and hasattr(mgr, "cancel"):
                        mgr.cancel(expected)
                except Exception:
                    pass
        except Exception:
            pass

        try:
            self.video_info_label.setText("")
        except Exception:
            pass
        try:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Ready...")
        except Exception:
            pass
        try:
            self.set_combos_enabled(False)
        except Exception:
            pass
        try:
            self._cancelled_by_user = True
        except Exception:
            pass

        try:
            self._single_mgr_callback = None
        except Exception:
            pass

    def set_combos_enabled(self, enabled):
        self.format_combo.setEnabled(enabled)
        self.quality_combo.setEnabled(enabled)
        self.compression_combo.setEnabled(enabled)
        self.mp3_bitrate_combo.setEnabled(enabled)

    def _check_and_update_ui_state(self):
        has_any_url = bool(self.url_input.text().strip() or (self.urls_to_download and any(self.urls_to_download)))
        if not (self.download_thread and self.download_thread.isRunning()):
            self.download_btn.setEnabled(has_any_url)
        if not has_any_url:
            self.set_combos_enabled(False)

    def _recompute_status(self):
        if self.download_thread and self.download_thread.isRunning():
            return

        mgr = getattr(self, "metadata_manager", None)
        is_loading = False

        try:
            if mgr:
                if hasattr(mgr, "is_loading"):
                    try:
                        is_loading = mgr.is_loading()
                    except Exception:
                        is_loading = bool(getattr(mgr, "_queue", None) and not mgr._queue.empty())
                elif hasattr(mgr, "_queue"):
                    is_loading = not mgr._queue.empty()
        except Exception:
            is_loading = False

        try:
            if hasattr(self, "saved_multilist") and self.saved_multilist:
                valid_urls = []
                selected_urls = []

                failed_set = set()
                try:
                    failed_set = getattr(mgr, "failed", set()) if mgr else set()
                except Exception:
                    failed_set = set()

                for entry in self.saved_multilist:
                    url = entry.get("url", "").strip() if isinstance(entry, dict) else str(entry).strip()
                    if not url or url in failed_set:
                        continue
                    valid_urls.append(url)
                    if entry.get("checked", True):
                        selected_urls.append(url)

                total_count = len(valid_urls)
                selected_count = len(selected_urls)

                if total_count > 0:
                    text = f"{selected_count} / {total_count} video{'s' if total_count != 1 else ''} in list – manage via multi-selection"
                    self.url_input.setText(text)
                    self.url_input.setReadOnly(True)
                    if hasattr(self, "paste_btn"):
                        self.paste_btn.setEnabled(False)
                else:
                    self.url_input.clear()
                    self.url_input.setReadOnly(False)
                    if hasattr(self, "paste_btn"):
                        self.paste_btn.setEnabled(True)

            elif hasattr(self, "urls_to_download") and self.urls_to_download:
                urls = [u for u in self.urls_to_download if u]
                count_text = f"{len(urls)} video{'s' if len(urls) != 1 else ''} in list – manage it via multi-selection"
                self.url_input.setText(count_text)
                self.url_input.setReadOnly(True)
                if hasattr(self, "paste_btn"):
                    self.paste_btn.setEnabled(False)
            else:
                self.url_input.clear()
                self.url_input.setReadOnly(False)
                if hasattr(self, "paste_btn"):
                    self.paste_btn.setEnabled(True)

        except Exception as e:
            print(f"[MainWindow._recompute_status] Error: {e}")

        try:
            urls = [u for u in getattr(self, "urls_to_download", []) if u]
            if not urls and not self.url_input.text().strip():
                self.progress_bar.setFormat("Ready...")
                self.progress_bar.setValue(0)
                self.download_btn.setEnabled(False)
                self.set_combos_enabled(False)
                self.video_info_label.setText("")
                return

            if urls:
                all_cached = False
                radio_cached = False
                if mgr:
                    try:
                        cache = getattr(mgr, "cache", {})
                        all_cached = all(u in cache for u in urls)
                        for u in urls:
                            if "list=RD" in u or "start_radio=1" in u:
                                canon = canonicalize_youtube_url(u)
                                v = cache.get(canon, {})
                                if v.get("is_radio_playlist", False) or v.get("title"):
                                    radio_cached = True
                                    break
                    except Exception:
                        all_cached = False

                if all_cached or radio_cached:
                    self.progress_bar.setFormat("Ready to download...")
                    self.download_btn.setEnabled(True)
                    self.set_combos_enabled(True)
                    self.video_info_label.setText("Ready to download...")
                else:
                    self.progress_bar.setFormat("Loading video info...")
                    self.progress_bar.setValue(0)
                    self.download_btn.setEnabled(False)
                    self.set_combos_enabled(False)
        except Exception as e:
            print(f"[MainWindow._recompute_status] Progress error: {e}")

    def update_ui_visibility(self):
        is_mp4 = self.format_combo.currentText() == 'MP4 (video+audio)'
        self.video_quality_label.setVisible(is_mp4)
        self.quality_combo.setVisible(is_mp4)
        self.compression_label.setVisible(is_mp4)
        self.compression_combo.setVisible(is_mp4)
        self.mp3_bitrate_label.setVisible(not is_mp4)
        self.mp3_bitrate_combo.setVisible(not is_mp4)

    def fetch_video_info(self, force_url=None):
        url = force_url if force_url else self.url_input.text().strip()

        if not url or not is_supported_url(url):
            self.progress_bar.setFormat("Clipboard does not contain a valid YouTube/Facebook URL.")
            self.progress_bar.setValue(0)
            self.download_btn.setEnabled(True)
            try:
                QMessageBox.warning(self, "Invalid URL", "Clipboard does not contain a valid YouTube/Facebook URL.")
            except Exception:
                pass

            self.url_input.blockSignals(True)
            self.url_input.clear()
            self.url_input.blockSignals(False)
            self.url_input.setClearButtonEnabled(False)
            self.progress_bar.setFormat("Ready...")
            if hasattr(self, "video_info_label"):
                self.video_info_label.setText("")
            return
        if not self.urls_to_download:
            if not self.is_retrying:
                self.last_url_for_retry = url

            self.progress_bar.setFormat("Wait...")
            self.progress_bar.setValue(0)
            self.download_btn.setEnabled(False)
            self.video_info_label.setStyleSheet(
                "QLabel { color:#1b84c4; margin-left:2px; padding:2px 0 2px 0; }"
            )

            mgr = self.metadata_manager
            norm = normalize_url(url)
            if is_youtube_url(norm) and ("list=RD" in norm or "start_radio=1" in norm):
                print("[META] Forcing radio mode fetch for single paste.")
                mgr._queue.put(norm)
            else:
                mgr.request(norm)

            def _stop_all_timers():
                try:
                    if hasattr(self, "_loading_timer") and getattr(self, "_loading_timer", None) is not None:
                        try:
                            if self._loading_timer.isActive():
                                self._loading_timer.stop()
                        except Exception:
                            pass
                        self._loading_timer = None
                except Exception:
                    pass
                try:
                    if hasattr(self, "_multi_spinner_timer") and getattr(self, "_multi_spinner_timer", None) is not None:
                        try:
                            if self._multi_spinner_timer.isActive():
                                self._multi_spinner_timer.stop()
                        except Exception:
                            pass
                        self._multi_spinner_timer = None
                except Exception:
                    pass
            if norm in getattr(mgr, "cache", {}):
                _stop_all_timers()
                data = mgr.cache[norm]
                try:
                    self.update_quality_combo(data)
                except Exception:
                    pass
                self.download_btn.setEnabled(True)
                self.progress_bar.setFormat("Ready to download...")
                if hasattr(self, "video_info_label"):
                    self.video_info_label.setText("Ready to download...")
                return

            _stop_all_timers()
            # zvýšíme index (pro animaci)
            self._spinner_index = getattr(self, "_spinner_index", 0)
            frame = spinner_frame(self._spinner_index)

            self.video_info_label.setText(f"{frame}    Loading video info...")

            self._loading_timer = QTimer(self)

            def on_tick():
                try:
                    self._spinner_index += 1
                    frame = spinner_frame(self._spinner_index)
                    self.video_info_label.setText(f"{frame}    Loading video info...")
                except Exception:
                    pass

            self._loading_timer.timeout.connect(on_tick)
            self._loading_timer.start(150)


            def on_res(u, data):
                if u != norm or u in getattr(mgr, "_cancelled", set()):
                    return
                _stop_all_timers()
                self.is_retrying = False
                if "entries" in data or data.get("is_playlist"):
                    reply = QMessageBox.question(
                        self,
                        "Playlist detected",
                        "This link is a playlist.\nDo you want to split it into individual videos?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        entries = data.get("entries", [])
                        urls = [e.get("webpage_url") for e in entries if e.get("webpage_url")]
                        if urls:
                            self.urls_to_download = urls
                            try:
                                self.video_info_label.setText("")
                            except Exception:
                                pass
                            self.open_multi_url_dialog()
                        try:
                            mgr.resolutions_fetched.disconnect(on_res)
                        except Exception:
                            pass
                        try:
                            mgr.error.disconnect(on_err)
                        except Exception:
                            pass
                        try:
                            mgr.status_update.disconnect(on_stat)
                        except Exception:
                            pass
                        return
                    else:
                        try:
                            self.update_quality_combo(data)
                        except Exception:
                            pass
                        self.download_btn.setEnabled(True)
                        self.progress_bar.setFormat("Ready to download...")
                else:
                    try:
                        self.update_quality_combo(data)
                    except Exception:
                        pass
                    self.download_btn.setEnabled(True)
                    self.progress_bar.setFormat("Ready to download...")
                try:
                    mgr.resolutions_fetched.disconnect(on_res)
                except Exception:
                    pass
                try:
                    mgr.error.disconnect(on_err)
                except Exception:
                    pass
                try:
                    mgr.status_update.disconnect(on_stat)
                except Exception:
                    pass

            def on_err(u, msg):
                if u != norm or u in getattr(mgr, "_cancelled", set()):
                    return
                error_msg_lower = msg.lower()
                is_ban_error = (
                    "sign in" in error_msg_lower
                    or "confirm you are not a bot" in error_msg_lower
                    or "unavailable" in error_msg_lower
                )
                if is_ban_error and not self.is_retrying:
                    self.is_retrying = True
                    _stop_all_timers()
                    self.refresh_session_and_retry()
                    return
                _stop_all_timers()
                self.is_retrying = False
                show_download_error_message(self, original_error=msg)
                self.progress_bar.setFormat("Error fetching info")
                self.download_btn.setEnabled(True)
                try:
                    self.video_info_label.setText("")
                except Exception:
                    pass
                try:
                    mgr.resolutions_fetched.disconnect(on_res)
                except Exception:
                    pass
                try:
                    mgr.error.disconnect(on_err)
                except Exception:
                    pass
                try:
                    mgr.status_update.disconnect(on_stat)
                except Exception:
                    pass

            def on_stat(u, s):
                if u != norm or u in getattr(mgr, "_cancelled", set()):
                    return
                self.progress_bar.setFormat(s)
            self._meta_start_time = time.time()
            self._single_mgr_callback = (mgr, on_res, on_err, on_stat, norm)
            mgr.resolutions_fetched.connect(on_res)
            mgr.error.connect(on_err)
            mgr.status_update.connect(on_stat)
            mgr.request(norm)


    def update_quality_combo(self, data):
        self.download_btn.setStyleSheet("QPushButton { background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgb(70, 190, 220), stop:0.5 rgb(50, 160, 210), stop:1 rgb(40, 120, 180)); border-radius: 12px; padding: 12px 16px; color: #fff; font-weight: bold; border: 2px solid #444; } QPushButton:hover { background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgb(90, 210, 235), stop:0.5 rgb(70, 180, 220), stop:1 rgb(50, 140, 190)); } QPushButton:pressed { background: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgb(30, 100, 150), stop:0.5 rgb(40, 130, 180), stop:1 rgb(60, 160, 200)); }")
        self.quality_combo.clear()
        self.quality_combo.addItems(data["resolutions"])
        self.video_info = data
        duration = data.get("duration", 0)
        full_text = f"🍿 Video: {data.get('title', 'N/A')} | Duration: {int(duration/60):02d}:{int(duration%60):02d} | Best: {data['resolutions'][0] if data['resolutions'] else 'N/A'}"
        self.video_info_label.setText(full_text)
        self.video_info_label.setToolTip(full_text)
        if "1080p" in data["resolutions"]:
            self.quality_combo.setCurrentText("1080p")
        self.download_btn.setEnabled(True)
        self.progress_bar.setFormat("Ready to download...")
        self.set_combos_enabled(True)

    def info_fetch_error(self, message):
        msg = (message or "").strip().lower()
        if self._cancelled_by_user or "cancelled" in msg:
            self.progress_bar.setFormat("Cancelled...")
            self.download_btn.setEnabled(True)
            return
        self.progress_bar.setFormat("Error fetching info")
        show_download_error_message(self, original_error=message)
        self.download_btn.setEnabled(True)

    DEFAULT_BROWSER = None
    _DETECTED_BROWSER = None

    def detect_default_browser():
        import sys
        if sys.platform != "win32":
            return None
        try:
            import winreg
            path = r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
                progid, _ = winreg.QueryValueEx(key, "ProgId")
                progid = progid.lower()
                if "chrome" in progid:
                    return "chrome"
                if "firefox" in progid:
                    return "firefox"
                if "edge" in progid or "microsoft" in progid:
                    return "edge"
                if "brave" in progid:
                    return "brave"
        except Exception:
            pass
        return None
    _DETECTED_BROWSER = detect_default_browser()
    DEFAULT_BROWSER = _DETECTED_BROWSER or "firefox"

    def paste_url(self):
        """Vloží URL z clipboardu do hlavního single pole (YT i FB povoleno) a ukáže popup při chybě."""
        clip = QApplication.clipboard().text().strip()
        if not clip:
            msg = "Schránka je prázdná."
            self.progress_bar.setFormat(msg)
            try:
                QMessageBox.warning(self, "Prázdná schránka", msg)
            except Exception:
                pass
            return
        url_pattern = re.compile(
            r'^https?://(?:www\.)?(?:youtube\.com|youtu\.be|facebook\.com|fb\.watch)/\S+',
            re.IGNORECASE
        )
        parts = [p.strip() for p in re.split(r'[\r\n]+', clip) if p.strip()]
        valid = next((p for p in parts if url_pattern.match(p)), None)
        if not valid:
            msg = "Neplatná nebo žádná URL nebyla rozpoznána."
            self.progress_bar.setFormat(msg)
            try:
                QMessageBox.warning(self, "Neplatná URL", msg)
            except Exception:
                pass
            return
        if is_youtube_url(valid) and ("list=RD" in valid or "start_radio=1" in valid):
            norm = valid
        else:
            norm = normalize_url(valid)
        self.url_input.setText(norm)
        try:
            self.fetch_video_info()
        except Exception as e:
            msg = f"Chyba při načítání informací:\n\n{str(e)}"
            self.progress_bar.setFormat(f"Chyba: {str(e)}")
            try:
                QMessageBox.warning(self, "Chyba", msg)
            except Exception:
                pass

    def open_multi_dialog(self):
        dialog = MultiURLDialog(self)
        dialog.urls_updated.connect(self.sync_with_multi)
        dialog.exec()

    def sync_with_multi(self, urls):
        try:
            urls_set = set(canonicalize_youtube_url(u) for u in (urls or []) if u)
            try:
                if hasattr(self, "btn_paste"):
                    self.btn_paste.setEnabled(not bool(urls_set))
            except Exception as e:
                print(f"[sync_with_multi] Early paste button update failed: {e}")

            if not any(is_supported_url(u) for u in urls_set):
                if hasattr(self, "_multi_spinner_timer") and self._multi_spinner_timer.isActive():
                    self._multi_spinner_timer.stop()
                self.video_info_label.setText("")
                self.progress_bar.setFormat("Ready...")
                self.progress_bar.setValue(0)
                self.download_btn.setEnabled(False)
                self.set_combos_enabled(False)
                return

            current_raw = self.url_input.text().strip()
            current_single = ""
            if current_raw and re.match(r'^https?://(www\.)?(youtube\.com|youtu\.be)/\S+', current_raw):
                current_single = canonicalize_youtube_url(current_raw)

            mgr = getattr(self, "metadata_manager", None)
            is_loading = False
            try:
                if mgr:
                    if hasattr(mgr, "is_loading"):
                        try:
                            is_loading = mgr.is_loading()
                        except Exception:
                            is_loading = bool(getattr(mgr, "_queue", None) and not mgr._queue.empty())
                    elif hasattr(mgr, "_queue"):
                        is_loading = not mgr._queue.empty()
            except Exception:
                is_loading = False

            try:
                if hasattr(self, "btn_paste"):
                    self.btn_paste.setEnabled(not bool(urls_set))
            except Exception as e:
                print(f"[sync_with_multi] Paste button update failed: {e}")

            if mgr and urls_set:
                all_cached = True
                for u in urls_set:
                    norm = canonicalize_youtube_url(u)
                    if norm not in mgr.cache:
                        all_cached = False
                        break
                if all_cached:
                    if hasattr(self, "_multi_spinner_timer") and self._multi_spinner_timer.isActive():
                        self._multi_spinner_timer.stop()
                    self.progress_bar.setFormat("Ready to download...")
                    self.download_btn.setEnabled(True)
                    self.set_combos_enabled(True)
                    self.video_info_label.setText("Ready to download...")
                    return

            if is_loading:
                try:
                    self.progress_bar.setFormat("Loading video info...")
                    self.progress_bar.setValue(0)
                    self.download_btn.setEnabled(False)
                    self.set_combos_enabled(False)

                    self._spinner_index = getattr(self, "_spinner_index", 0)
                    if not hasattr(self, "_multi_spinner_timer"):
                        self._multi_spinner_timer = QTimer(self)

                        def spin_tick():
                            try:
                                self._spinner_index += 1
                                frame = spinner_frame(self._spinner_index)
                                self.set_loading_ui(frame)

                            except Exception:
                                pass

                        self._multi_spinner_timer.timeout.connect(spin_tick)

                    if not self._multi_spinner_timer.isActive():
                        self._multi_spinner_timer.start(150)

                    frame = spinner_frame(self._spinner_index)
                    self.set_loading_ui(frame)

                except Exception as e:
                    print(f"[sync_with_multi] Spinner setup failed: {e}")
                return

            if current_single and current_single not in urls_set:
                try:
                    if hasattr(self, "_multi_spinner_timer") and self._multi_spinner_timer.isActive():
                        self._multi_spinner_timer.stop()
                    self.video_info_label.setText("")
                except Exception:
                    pass
                try:
                    self.video_info = {}
                except Exception:
                    pass
                try:
                    self.set_combos_enabled(False)
                    self.download_btn.setEnabled(False)
                    self.progress_bar.setFormat("Ready...")
                    self.progress_bar.setValue(0)
                except Exception:
                    pass
                return

            if urls_set and not is_loading:
                try:
                    self._spinner_index = getattr(self, "_spinner_index", 0)
                    if not hasattr(self, "_multi_spinner_timer"):
                        self._multi_spinner_timer = QTimer(self)

                        def spin_tick():
                            try:
                                self._spinner_index += 1
                                frame = spinner_frame(self._spinner_index)
                                self.set_loading_ui(frame)

                            except Exception:
                                pass

                        self._multi_spinner_timer.timeout.connect(spin_tick)
                        self._multi_spinner_timer.start(150)
                    else:
                        if not self._multi_spinner_timer.isActive():
                            self._multi_spinner_timer.start(150)

                    self.progress_bar.setFormat("Loading video info...")
                    self.progress_bar.setValue(0)
                    self.download_btn.setEnabled(True)
                    self.set_combos_enabled(True)
                    frame = spinner_frame(self._spinner_index)
                    self.set_loading_ui(frame)

                except Exception:
                    pass
                return

            if current_single and current_single in urls_set:
                try:
                    if hasattr(self, "_multi_spinner_timer") and self._multi_spinner_timer.isActive():
                        self._multi_spinner_timer.stop()
                    if mgr and current_single in getattr(mgr, "cache", {}):
                        self.progress_bar.setFormat("Ready...")
                        self.download_btn.setEnabled(True)
                        data = mgr.cache.get(current_single, {})
                        if data:
                            try:
                                self.update_quality_combo(data)
                                self.set_combos_enabled(True)
                            except Exception:
                                pass
                        self.video_info_label.setText("Ready to download...")
                    else:
                        self.progress_bar.setFormat("Loading video info...")
                        self.download_btn.setEnabled(False)
                        self.video_info_label.setText("Loading video info...")
                    self.progress_bar.setValue(0)
                except Exception:
                    pass
                return

            if not urls_set:
                try:
                    if hasattr(self, "_multi_spinner_timer") and self._multi_spinner_timer.isActive():
                        self._multi_spinner_timer.stop()
                    self.url_input.setReadOnly(False)
                    self.video_info_label.setText("")
                    self.video_info = {}
                    self.progress_bar.setFormat("Ready...")
                    self.progress_bar.setValue(0)
                    self.download_btn.setEnabled(False)
                    self.set_combos_enabled(False)
                except Exception:
                    pass
        except Exception as e:
            print(f"[sync_with_multi] Error: {e}")


    def open_multi_url_dialog(self):
        try:
            if hasattr(self, "_loading_timer") and self._loading_timer and self._loading_timer.isActive():
                self._loading_timer.stop()
                self._loading_timer = None
            if hasattr(self, "loading_overlay") and self.loading_overlay:
                self.loading_overlay.hide()
        except Exception:
            pass
        self.reset_to_default_qualities()
        main_url = self.url_input.text().strip()
        urls = []
        if self.urls_to_download:
            urls = [canonicalize_youtube_url(u) for u in self.urls_to_download]
        elif main_url:
            urls = [canonicalize_youtube_url(main_url)]
        source_urls = getattr(self, "saved_multilist", None)
        if source_urls:
            self.multi_url_dialog = MultiURLDialog(self, urls=source_urls)
        else:
            self.multi_url_dialog = MultiURLDialog(self, urls=urls)
        self.multi_url_dialog.closed.connect(self.handle_multi_url_close)
        self.multi_url_dialog.show()
        if urls:
            count_text = f"{len(urls)} video{'s' if len(urls) != 1 else ''} in list – manage it via multi-selection"
            self.url_input.setText(count_text)
            self.url_input.setReadOnly(True)
            self.url_input.setClearButtonEnabled(False)
            if hasattr(self, "paste_btn"):
                self.paste_btn.setEnabled(False)
        else:
            self.url_input.clear()
            self.url_input.setReadOnly(True)
            self.url_input.setClearButtonEnabled(False)
            if hasattr(self, "paste_btn"):
                self.paste_btn.setEnabled(False)
        try:
            if hasattr(self, "sync_with_multi"):
                self.sync_with_multi(urls)
        except Exception as e:
            print(f"[multi sync init] {e}")

    def handle_multi_url_close(self, data):
        print("HANDLE MULTI URL CLOSE CALLED")

        try:
            had_urls = bool(
                data and any(
                    (d.get("url") if isinstance(d, dict) else d).strip()
                    for d in data
                )
            )

            mgr = getattr(self, "metadata_manager", None)

            self.urls_to_download = []
            self.saved_multilist = []

            if not data:
                self.urls_to_download = []

            elif isinstance(data[0], dict):
                for entry in data:
                    url = entry.get("url", "").strip()
                    if not url:
                        continue

                    checked = entry.get("checked", True)
                    is_failed = bool(mgr and url in getattr(mgr, "failed", set()))

                    is_radio = ("list=RD" in url or "start_radio=1" in url)
                    is_cached = False

                    if mgr:
                        try:
                            canon = canonicalize_youtube_url(url)
                            cache = getattr(mgr, "cache", {})
                            item = cache.get(canon, {})
                            if item and (item.get("is_radio_playlist") or item.get("title")):
                                is_cached = True
                        except Exception:
                            pass

                    self.saved_multilist.append({
                        "url": url,
                        "checked": checked and not is_failed
                    })

                    if checked and not is_failed:
                        self.urls_to_download.append(url)

                    if mgr:
                        try:
                            canon = canonicalize_youtube_url(url)

                            if canon in getattr(mgr, "failed", set()):
                                continue
                            if not checked:
                                continue
                            if canon in getattr(mgr, "cache", {}):
                                continue
                            if is_radio and is_cached:
                                continue

                            mgr.request([canon])
                        except Exception as e:
                            print(f"[handle_multi_url_close] Fetch error for {url}: {e}")

            else:
                for u in data:
                    if not u:
                        continue

                    is_failed = bool(mgr and u in getattr(mgr, "failed", set()))

                    self.saved_multilist.append({
                        "url": u,
                        "checked": not is_failed
                    })

                    if not is_failed:
                        self.urls_to_download.append(u)

                    if mgr:
                        try:
                            mgr.request([canonicalize_youtube_url(u)])
                        except Exception as e:
                            print(f"[handle_multi_url_close] Fetch error for {u}: {e}")

            if not had_urls:
                try:
                    if hasattr(self, "url_input"):
                        self.url_input.clear()
                        self.url_input.setReadOnly(False)
                        self.url_input.setClearButtonEnabled(True)
                    if hasattr(self, "btn_paste"):
                        self.btn_paste.setEnabled(True)
                except Exception:
                    pass

                self._recompute_status()
                return

            if hasattr(self, "btn_paste"):
                self.btn_paste.setEnabled(False)
            if hasattr(self, "url_input"):
                self.url_input.setReadOnly(True)
                self.url_input.setClearButtonEnabled(False)

            selected_count = sum(1 for e in self.saved_multilist if e.get("checked"))
            total_count = len(self.saved_multilist)

            to_fetch = []
            if mgr:
                for u in self.urls_to_download:
                    norm = canonicalize_youtube_url(u)
                    if norm not in mgr.cache and norm not in getattr(mgr, "failed", set()):
                        to_fetch.append(norm)

            still_loading = bool(to_fetch)

            self._multi_selection_active = total_count > 0
            self._selected_count_at_close = selected_count
            self._total_count_at_close = total_count
            self._still_loading_meta = still_loading
            self._spinner_index = getattr(self, "_spinner_index", 0)

            def _tick_loading_ui():
                if not getattr(self, "_still_loading_meta", False):
                    return

                self._spinner_index += 1
                frame = spinner_frame(self._spinner_index)

                if hasattr(self, "progress_bar"):
                    self.progress_bar.setValue(0)
                if hasattr(self, "video_info_label"):
                    self.set_loading_ui(frame)

                QTimer.singleShot(350, _tick_loading_ui)

            def _wait_for_finish():
                if not getattr(self, "_still_loading_meta", False):
                    return
                if not mgr:
                    QTimer.singleShot(250, _wait_for_finish)
                    return

                selected_norms = [
                    canonicalize_youtube_url(e["url"])
                    for e in self.saved_multilist
                    if e.get("checked")
                ]

                all_cached = (
                    len(selected_norms) > 0 and
                    all(u in getattr(mgr, "cache", {}) for u in selected_norms)
                )

                if all_cached:
                    self._still_loading_meta = False
                    if hasattr(self, "progress_bar"):
                        self.progress_bar.setFormat("Ready to download...")
                    if hasattr(self, "download_btn"):
                        self.download_btn.setEnabled(True)
                    if hasattr(self, "set_combos_enabled"):
                        self.set_combos_enabled(True)
                    if hasattr(self, "video_info_label"):
                        self.video_info_label.setText("Ready to download...")
                else:
                    QTimer.singleShot(250, _wait_for_finish)

            if selected_count == 0:
                self._still_loading_meta = False
                if hasattr(self, "progress_bar"):
                    self.progress_bar.setFormat("No videos selected.")
                    self.progress_bar.setValue(0)
                if hasattr(self, "download_btn"):
                    self.download_btn.setEnabled(False)
                if hasattr(self, "set_combos_enabled"):
                    self.set_combos_enabled(False)
                if hasattr(self, "video_info_label"):
                    self.video_info_label.setText(
                        "No videos selected – please choose at least one to download."
                    )

            elif still_loading:
                if hasattr(self, "download_btn"):
                    self.download_btn.setEnabled(False)
                if hasattr(self, "set_combos_enabled"):
                    self.set_combos_enabled(False)
                _tick_loading_ui()
                _wait_for_finish()

            else:
                all_cached = True
                if mgr:
                    selected_norms = [
                        canonicalize_youtube_url(e["url"])
                        for e in self.saved_multilist
                        if e.get("checked")
                    ]
                    all_cached = (
                        len(selected_norms) > 0 and
                        all(u in getattr(mgr, "cache", {}) for u in selected_norms)
                    )

                if all_cached and selected_count > 0:
                    if hasattr(self, "progress_bar"):
                        self.progress_bar.setFormat("Ready to download...")
                    if hasattr(self, "download_btn"):
                        self.download_btn.setEnabled(True)
                    if hasattr(self, "set_combos_enabled"):
                        self.set_combos_enabled(True)
                    if hasattr(self, "video_info_label"):
                        self.video_info_label.setText("Ready to download...")
                else:
                    self._still_loading_meta = True
                    if hasattr(self, "download_btn"):
                        self.download_btn.setEnabled(False)
                    if hasattr(self, "set_combos_enabled"):
                        self.set_combos_enabled(False)
                    _tick_loading_ui()
                    _wait_for_finish()

            self._recompute_status()
            try:
                self.refresh_url_list_display()
            except Exception:
                pass

        except Exception as e:
            print(f"[MainWindow.handle_multi_url_close] Error: {e}")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Folder", str(Path(self.save_path).parent))
        if folder:
            self.save_path = os.path.join(folder, "YTDownloads")
            os.makedirs(self.save_path, exist_ok=True)
            self.folder_btn.setText(f"📁 .../{os.path.basename(self.save_path)}")

    def start_or_cancel_download(self):
        if self.download_thread and self.download_thread.isRunning():
            self._cancelled_by_user = True
            self.download_thread.cancel()
            self.progress_bar.setFormat("Cancelled...")
            self.progress_bar.setStyleSheet(" QProgressBar { color: #e74c3c;} QProgressBar::chunk { background-color: #2a82da; border-radius: 8px; margin: 1px;}")
            self.progress_bar.setValue(0)
            self.download_btn.setEnabled(True)
            self.show_download_cancelled_message()
            def reset_ui():
                self._cancelled_by_user = False
                if self.url_input.text().strip() or (self.urls_to_download and any(self.urls_to_download)):
                    self.progress_bar.setFormat("Ready to download...")
                else:
                    self.progress_bar.setFormat("Ready...")
                self.progress_bar.setStyleSheet(" QProgressBar { color: white;} QProgressBar::chunk { background-color: #2a82da; border-radius: 8px; margin: 1px;}")
                self.progress_bar.setValue(0)
                self.set_ui_for_download(False)
            QTimer.singleShot(1500, reset_ui)
        else:
            self.start_download()

    def start_download(self):
        self.is_retrying = False
        self.last_url_for_retry = (self.urls_to_download or [self.url_input.text().strip()]).__getitem__(0)
        urls = self.urls_to_download or (
            [self.url_input.text().strip()] if self.url_input.text().strip() else []
        )
        urls = [u.strip() for u in urls if u.strip()]
        if not urls:
            QMessageBox.warning(self, "No URLs", "Please enter at least one YouTube URL.")
            return
        self.set_ui_for_download(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Preparing...")  
        titles = []
        mgr = getattr(self, "metadata_manager", None)
        if mgr:
            for u in urls:
                meta = mgr.cache.get(u, {})
                titles.append(meta.get("title", f"video_{len(titles)+1}"))
        else:
            titles = [self.video_info.get("title") or f"video_{i+1}" for i in range(len(urls))]

        params = {
            "urls": urls,
            "save_path": self.save_path,
            "format_opt": self.format_combo.currentText(),
            "video_quality": self.quality_combo.currentText(),
            "available_resolutions": self.video_info.get("resolutions", []),
            "compression_mode": self.compression_combo.currentText(),
            "mp3_bitrate": int(self.mp3_bitrate_combo.currentText()),
            "duration_s": self.video_info.get("duration", 0),
            "title": self.video_info.get("title") if len(urls) == 1 else None,
            "titles": titles,
            "cookie_session": "default",
        }

        try:
            PROGRESS_AGGREGATOR.register_urls(urls)
        except Exception as e:
            print(f"[DEBUG] Aggregator init failed: {e}")
        try:
            PROGRESS_AGGREGATOR.overall_progress.disconnect()
        except Exception:
            pass
        PROGRESS_AGGREGATOR.overall_progress.connect(self.on_aggregated_progress)
        self.download_thread = DownloadThread(**params)
        self.download_thread.progress.connect(self.update_progress_per_file)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.error.connect(self.download_error)
        self.download_thread.start()
        print(f"[INFO] Starting download for {len(urls)} URLs...")

    def update_progress_per_file(self, percent, text):
        print(f"  [file] {text}")

    def on_aggregated_progress(self, percent, status_text):
        try:
            self.progress_bar.setValue(percent)
            self.progress_bar.setFormat(f"({status_text})  Downloading…  {percent}%")
        except:
            pass

    def update_progress(self, percent, status_text):
        pass

    def show_download_cancelled_message(self):
        QMessageBox.information(self, "Download Cancelled", "The download was cancelled by the user.")

    def download_finished(self, is_last):
        if is_last:
            self.progress_bar.setFormat("Download complete!")
            self.progress_bar.setValue(100)
            reply = QMessageBox.information(
                self,
                "Complete!",
                f"All videos downloaded successfully.\nSaved to: {self.save_path}",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Open
            )
            if reply == QMessageBox.StandardButton.Open:
                try:
                    if sys.platform == "win32":
                        os.startfile(self.save_path)
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", self.save_path])
                    else:
                        subprocess.Popen(["xdg-open", self.save_path])
                except Exception:
                    pass
            self.set_ui_for_download(False)
 
    def download_error(self, msg):
        txt = (msg or "").strip().lower()
        if self._cancelled_by_user or txt in ("download cancelled by user.", "download cancelled by user"):
            self.progress_bar.setFormat("Cancelled...")
            self.progress_bar.setValue(0)
            return
        show_download_error_message(self, original_error=msg)
        self.progress_bar.setFormat("Download failed.")
        self.set_ui_for_download(False)

    def set_ui_for_download(self, is_downloading):
        if is_downloading:
            self.download_btn.setText("Cancel")
            self.download_btn.setEnabled(True)
            self.download_btn.setStyleSheet(""" QPushButton {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                stop:0 rgb(231, 76, 60), stop:0.5 rgb(211, 56, 40), stop:1 rgb(192, 57, 43));
                border-radius: 12px; padding: 12px 16px; color: #fff; font-weight: bold;
                border: 2px solid #555;
            } QPushButton:hover {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                stop:0 rgb(255, 92, 92), stop:0.5 rgb(231, 76, 60), stop:1 rgb(211, 56, 40));
                border: 2px solid #555;
            } QPushButton:pressed {
                background: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0,
                stop:0 rgb(160, 30, 20), stop:0.5 rgb(192, 57, 43), stop:1 rgb(211, 56, 40));
                border: 2px solid #444;
            } QPushButton:disabled {
                background-color: #555; color: #999; border: 2px solid #666;
            }""")
        else:
            self.download_btn.setText("Download ⬇️")
            self.download_btn.setEnabled(True)
            self.download_btn.setStyleSheet(""" QPushButton {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                stop:0 rgb(122, 150, 230), stop:0.5 rgb(42, 130, 218), stop:1 rgb(24, 92,158));
                border-radius: 12px; padding: 12px 16px; color: #fff; font-weight: bold;
                border: 2px solid #555;
            } QPushButton:hover {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                stop:0 rgb(85, 163, 235), stop:0.5 rgb(55, 140, 225), stop:1 rgb(35, 102, 168));
                border: 2px solid #555;
            } QPushButton:pressed {
                background: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0,
                stop:0 rgb(20, 80, 140), stop:0.5 rgb(32, 110, 185), stop:1 rgb(50, 140, 210));
                border: 2px solid #555;
            } QPushButton:disabled {
                background-color: #555; color: #999; border: 2px solid #666;
            }""")
        for widget in [self.url_input, self.btn_paste, self.btn_multi_url,
                    self.format_combo, self.quality_combo, self.mp3_bitrate_combo,
                    self.compression_combo, self.folder_btn]:
            try:
                widget.setEnabled(not is_downloading)
            except Exception:
                pass
        if is_downloading:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Downloading...")
        else:
            if not getattr(self, "_cancelled_by_user", False):
                self.progress_bar.setFormat("Ready to download...") 
                self.progress_bar.setValue(0)

    def reset_ui(self):
        self._cancelled_by_user = False
        if self.url_input.text().strip() or (self.urls_to_download and any(self.urls_to_download)):
            self.progress_bar.setFormat("Ready to download...")
        else:
            self.progress_bar.setFormat("Ready...")
        self.progress_bar.setStyleSheet(""" 
            QProgressBar { color: white;} 
            QProgressBar::chunk { background-color: #2a82da; border-radius: 8px; margin: 1px;}
        """)
        self.progress_bar.setValue(0)
        self.set_ui_for_download(False)

    def reset_to_default_qualities(self):
        self.quality_combo.clear()
        self.quality_combo.addItems(self.default_resolutions)
        self.quality_combo.setCurrentText("1080p")

def get_bin_dir():
    primary = os.path.join(APP_DIR, "bin")
    # ŽÁDNÝ fallback do AppData, jen portable bin/
    try:
        os.makedirs(primary, exist_ok=True)
        testfile = os.path.join(primary, "_write_test.tmp")
        with open(testfile, "w") as f:
            f.write("ok")
        os.remove(testfile)
        return primary
    except:
        # kdyby náhodou neměl práva → furt vrátíme primary, ne AppData!
        return primary


# --- BIN DIR ---
BIN_DIR = get_bin_dir()


# --- BIN PROGRAMS ---
YTDLP_PATH   = os.path.join(BIN_DIR, "yt-dlp.exe" if sys.platform == "win32" else "yt-dlp")
FFMPEG_PATH  = os.path.join(BIN_DIR, "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
FFPROBE_PATH = os.path.join(BIN_DIR, "ffprobe.exe" if sys.platform == "win32" else "ffprobe")

def run_ytdlp_update():
    try:
        print(f"[AutoFix] Updating yt-dlp: {YTDLP_PATH}")
        proc = subprocess.Popen(
            [YTDLP_PATH, "-U", "--update-to", "nightly"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        stdout, stderr = proc.communicate(timeout=120)
        print("[AutoFix] yt-dlp update completed.")
        print("STDOUT:", stdout)
        if stderr:
            print("STDERR:", stderr)
    except Exception as e:
        print(f"[AutoFix] yt-dlp update failed: {e}")

def download_latest_ytdlp():
    """
    Stáhne yt-dlp nightly do TEMP a poté přesune do BIN_DIR.
    Použije se pouze při chybějícím souboru.
    """
    nightly_url = (
        "https://github.com/yt-dlp/yt-dlp-nightly-builds/releases/latest/download/yt-dlp.exe"
        if sys.platform == "win32"
        else "https://github.com/yt-dlp/yt-dlp-nightly-builds/releases/latest/download/yt-dlp"
    )

    temp_dl = os.path.join(TEMP_DIR, "yt-dlp_download.exe")

    try:
        print(f"[AutoFix] yt-dlp missing → downloading from: {nightly_url}")
        urllib.request.urlretrieve(nightly_url, temp_dl)

        os.chmod(temp_dl, 0o755)
        shutil.move(temp_dl, YTDLP_PATH)

        print("[AutoFix] yt-dlp download completed ✅")

    except Exception as e:
        print(f"[AutoFix] Failed to download yt-dlp.exe: {e}")



_YTDLP_UPDATE_LOG_SHOWN = False


def check_and_update_ytdlp(window=None):
    """
    Kontrola aktualizací yt-dlp:
      - Pokud chybí → stáhnout
      - Pokud existuje a update je povolen → zavolat update přes yt-dlp -U
      - Pokud update zakázaný → nechat být (ani nekontrolovat verzi!)
    """
    global _YTDLP_UPDATE_LOG_SHOWN

    # --- 1. read ini ---
    try:
        if window:
            allow_update = window.config_manager.get_yt_dlp_update()
        else:
            allow_update = CONFIG.getboolean("general", "yt_dlp_update", fallback=True)
            print("ALLOW UPDATE =", allow_update)
    except Exception:
        allow_update = True

    # --- 2. pokud update NE, tak okamžitě končit (žádné volání yt-dlp!) ---
    if not allow_update:
        #print("[AutoFix] yt-dlp update skipped (disabled in config.ini) ☠️")
        return

    # --- 3. zajistit, že se update řeší jen jednou ---
    if _YTDLP_UPDATE_LOG_SHOWN:
        return
    _YTDLP_UPDATE_LOG_SHOWN = True

    # --- 4. pokud yt-dlp neexistuje → stáhnout a skončit ---
    if not os.path.exists(YTDLP_PATH):
        download_latest_ytdlp()
        return

    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    # --- 5. zobrazit lokální verzi (povoleno jen pokud update = true) ---
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        res = subprocess.run(
            [YTDLP_PATH, "--version"],
            capture_output=True,
            text=True,
            creationflags=creation_flags,
            startupinfo=startupinfo,
            cwd=BIN_DIR
        )
        print(f"[AutoFix] yt-dlp version: {res.stdout.strip()}")

    except Exception as e:
        print(f"[AutoFix] yt-dlp version check failed: {e}")
        return

    # --- 6. provést update (yt-dlp rozhodne, zda je potřeba) ---
    try:
        print("[AutoFix] Checking yt-dlp updates…")

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        proc = subprocess.Popen(
            [YTDLP_PATH, "-U", "--update-to", "nightly"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creation_flags,
            startupinfo=startupinfo,
            cwd=BIN_DIR
        )

        stdout, stderr = proc.communicate(timeout=60)
        msg = (stdout + stderr).lower()

        if "updated" in msg:
            print("[AutoFix] yt-dlp UPDATED!")

        elif "up to date" in msg:
            print("[AutoFix] yt-dlp is up to date ✅")

        else:
            clean_msg = stdout.strip() if stdout.strip() else stderr.strip()
            print(f"[AutoFix] Update message: {clean_msg}")

    except Exception as e:
        print(f"[AutoFix] yt-dlp update failed: {e}")

def download_ffmpeg_binaries():
    """
    Stáhne FFmpeg ZIP do bin/temp pouze pokud ffmpeg/ffprobe chybí
    nebo jsou staré. Instalace proběhne do BIN_DIR.
    TEMP_DIR se používá jen pro stahování a extrakci.
    """

    # -------------- CONFIG ----------------
    MAX_AGE_DAYS = 30   # ffmpeg update interval
    # --------------------------------------

    def file_age_days(p):
        try:
            return (time.time() - os.path.getmtime(p)) / 86400
        except:
            return 9999

    ffmpeg_ok = (
        os.path.exists(FFMPEG_PATH)
        and os.path.exists(FFPROBE_PATH)
        and file_age_days(FFMPEG_PATH) < MAX_AGE_DAYS
        and file_age_days(FFPROBE_PATH) < MAX_AGE_DAYS
    )

    if ffmpeg_ok:
        print("[AutoFix] FFmpeg + FFprobe OK ✅")
        return

    print("[AutoFix] FFmpeg missing or outdated → downloading…")

    # URL
    ffmpeg_url = (
        "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        if sys.platform == "win32"
        else "https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.tar.xz"
    )

    # Temp cesty
    zip_path = os.path.join(TEMP_DIR, "ffmpeg_download.zip")
    extract_path = os.path.join(TEMP_DIR, "ffmpeg_extract")

    # Vytvoření temp složek
    os.makedirs(TEMP_DIR, exist_ok=True)
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path, ignore_errors=True)

    # -------------------------------------
    # 1) DOWNLOAD ZIP → TEMP_DIR
    # -------------------------------------
    try:
        urllib.request.urlretrieve(ffmpeg_url, zip_path)
        print("[AutoFix] FFmpeg ZIP downloaded.")
    except Exception as e:
        print(f"[AutoFix] Failed to download FFmpeg: {e}")
        return "ffmpeg"

    # -------------------------------------
    # 2) EXTRACT ZIP → TEMP_DIR/ffmpeg_extract
    # -------------------------------------
    try:
        os.makedirs(extract_path, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_path)

        print("[AutoFix] FFmpeg ZIP extracted.")
    except Exception as e:
        print(f"[AutoFix] Failed to extract FFmpeg ZIP: {e}")
        return "ffmpeg"

    # -------------------------------------
    # 3) FIND BINARIES
    # -------------------------------------
    ffmpeg_exe = None
    ffprobe_exe = None

    for root, dirs, files in os.walk(extract_path):
        for f in files:
            fname = f.lower()
            if fname == "ffmpeg.exe":
                ffmpeg_exe = os.path.join(root, f)
            elif fname == "ffprobe.exe":
                ffprobe_exe = os.path.join(root, f)

    if not (ffmpeg_exe and ffprobe_exe):
        print("[AutoFix] FFmpeg binaries not found in archive!")
        return "ffmpeg"

    # -------------------------------------
    # 4) MOVE → BIN_DIR
    # -------------------------------------
    try:
        shutil.copy2(ffmpeg_exe, FFMPEG_PATH)
        shutil.copy2(ffprobe_exe, FFPROBE_PATH)
        print("[AutoFix] FFmpeg + FFprobe installed successfully ✔")
    except Exception as e:
        print(f"[AutoFix] Failed to move FFmpeg binaries: {e}")
        return "ffmpeg"

    # -------------------------------------
    # 5) CLEANUP
    # -------------------------------------
    try:
        os.remove(zip_path)
        shutil.rmtree(extract_path, ignore_errors=True)
    except:
        pass

    return None

_SESSION_MANAGER = None

# =====================================================================
#  APP START
# =====================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # --------------------------------------------------------
    #  LOAD CONFIG + ENABLE LOGGING HNED TADY
    # --------------------------------------------------------
    CONFIG = ConfigManager()

    try:
        if CONFIG.get_logging_enabled():
            enable_logging()
    except:
        pass
    # --------------------------------------------------------

    splash = SplashWidget("⏳ Initializing Video Downloader…")
    splash.show()
    app.processEvents()

    print(f"Python ver: {sys.executable}")

    # --------------------------------------------------------
    #  STAŽENÍ FFMPEG / PŘÍPRAVA BINÁREK
    # --------------------------------------------------------
    try:
        download_ffmpeg_binaries()
    except Exception as e:
        print(f"[Warning] FFmpeg auto-download failed: {e}")

    app.processEvents()

    # --------------------------------------------------------
    #  NAČTENÍ COOKIES SETTINGS
    # --------------------------------------------------------
    try:
        harvest_cookies = CONFIG.config.getboolean(
            'settings',
            'harvest_cookies',
            fallback=True
        )
    except Exception:
        harvest_cookies = True

    _SESSION_MANAGER = SessionManager()
    METADATA_MANAGER = MetadataManager()
    PROGRESS_AGGREGATOR = ProgressAggregator()
    app.processEvents()

    # --------------------------------------------------------
    #  DEPENDENCY CHECK (YT-DLP + FFMPEG MUSÍ BÝT READY)
    # --------------------------------------------------------
    dep_result = {}

    def run_dep_check():
        try:
            dep_result["err"] = check_dependencies()
        except Exception as e:
            dep_result["err"] = str(e)

    dep_thread = threading.Thread(target=run_dep_check, daemon=True)
    dep_thread.start()

    while dep_thread.is_alive():
        app.processEvents()
        time.sleep(0.05)

    if dep_result.get("err"):
        QMessageBox.warning(
            None,
            "Missing Dependency",
            f"Missing: {dep_result['err']}\nRestart app."
        )

    # --------------------------------------------------------
    #  COOKIE EXPORT TEĎ (NE DŘÍV!) — YT-DLP JE UŽ 100% READY
    # --------------------------------------------------------
    try:
        if harvest_cookies:
            DEFAULT_BROWSER = detect_default_browser()
            if not DEFAULT_BROWSER:
                print("[WARNING] Default browser nelze zjistit! (harvest ON)")
            else:
                print(f"[Browser] Detected default browser: {DEFAULT_BROWSER}")
                export_default_browser_cookies(DEFAULT_BROWSER)
        else:
            print("[Cookies] harvest skipped (disabled in config.ini) ☠️")
    except Exception as e:
        print(f"[Cookies] Export failed: {e}")

    # --------------------------------------------------------
    #  YT-DLP UPDATE (TEĎ JE BINÁRKA READY, TAKŽE BEZ PROBLÉMŮ)
    # --------------------------------------------------------
    try:
        allow_update = False
        try:
            allow_update = CONFIG.config.getboolean(
                "yt-dlp",
                "yt_dlp_update",
                fallback=True
            )
        except Exception:
            allow_update = True

        if allow_update:
            check_and_update_ytdlp(None)   # window může být None, funkce to umí
        else:
            print("[AutoFix] yt-dlp update skipped (disabled in config.ini) ☠️")

    except Exception as e:
        print(f"[Warning] yt-dlp check failed: {e}")

    # --------------------------------------------------------
    #  MAIN WINDOW
    # --------------------------------------------------------
    window = YouTubeDownloader()
    window.showNormal()
    app.processEvents()

    # --------------------------------------------------------
    #  BRUTÁLNÍ FOCUS FIX + ZAVŘENÍ SPLASH
    # --------------------------------------------------------
    def bring_window_to_front():
        try:
            window.show()
            window.setWindowState(window.windowState() & ~Qt.WindowState.WindowMinimized)

            window.setWindowState(window.windowState() | Qt.WindowState.WindowActive
)
            window.raise_()
            window.activateWindow()

            # extra síla pro Windows
            try:
                window.setWindowFlags(window.windowFlags() | Qt.WindowStaysOnTopHint)
                window.show()
                window.raise_()
                window.activateWindow()

                # po chvilce zrušíme "always on top"
                QTimer.singleShot(
                    200, lambda: window.setWindowFlags(
                        window.windowFlags() & ~Qt.WindowStaysOnTopHint
                    )
                )
            except:
                pass

        except Exception as e:
            print(f"[Focus] Failed: {e}")

        # SPLASH ZAVŘÍT AŽ TEĎ – když okno už je bezpečně nahoře
        try:
            splash.close()
        except:
            pass

    QTimer.singleShot(100, bring_window_to_front)

    sys.exit(app.exec())

