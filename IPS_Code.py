import sys
import os
import subprocess
import time

class C:
    CYAN = '\033[36m'
    MAGENTA = '\033[35m'
    GREEN = '\033[92m'
    YELLOW = '\033[33m'
    RED = '\033[91m'
    GREY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    WHITE = '\033[97m'

def install(package):
    print(f"{C.YELLOW}[INSTALLER]{C.RESET} Installing requirement: {C.WHITE}{package}{C.RESET}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"{C.GREEN}[SUCCESS]{C.RESET} {package} installed successfully.\n")
    except subprocess.CalledProcessError:
        print(f"{C.RED}[ERROR]{C.RESET} Failed to install {package}. Please install manually.")
        sys.exit(1)

required_libs = {
    "flask": "flask",
    "PIL": "Pillow",
    "cv2": "opencv-python",
    "numpy": "numpy"
}

for lib_import, lib_install in required_libs.items():
    try:
        __import__(lib_import)
    except ImportError:
        install(lib_install)

import threading
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request, cli
from PIL import Image
import cv2
import numpy as np

cli.show_server_banner = lambda *_: None
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
log.disabled = True

def timestamp():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""{C.CYAN}{C.BOLD}
      ___ ____  ____  
      |_ _|  _ \/ ___| 
       | || |_) \___ \ 
       | ||  __/ ___) |
      |___|_|   |____/ {C.RED} // made with a lot of hate > w < //{C.RESET}
    """)
    
    print(f"    {C.MAGENTA}- FOLLOW ME:{C.RESET} TikTok {C.WHITE}@justobsessiom{C.RESET} | YT {C.WHITE}@JustObsessiom{C.RESET}")
    print(f"    {C.YELLOW}- SUPPORT:{C.RESET}   Thanks for using this tool! Use it wisely hehe.")
    print("\n")

def animate_waiting():
    dots = [".  ", ".. ", "..."]
    idx = 0
    while True:
        sys.stdout.write(f"\r{C.BOLD}    listening{dots[idx%3]}{C.RESET}")
        sys.stdout.flush()
        time.sleep(0.5)
        idx += 1

def smart_print(action, target, status, info=""):
    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()

    ts = f"{C.GREY}[{timestamp()}]{C.RESET}"
    act = f"{C.CYAN}{C.BOLD}{action:<12}{C.RESET}"
    tgt = f"{C.MAGENTA}target={C.RESET}'{target}'"
    
    if status == "OK":
        stat = f"{C.GREEN}[SUCCESS]{C.RESET}"
    elif status == "WAIT":
        stat = f"{C.YELLOW}[PENDING]{C.RESET}"
    elif status == "FAIL":
        stat = f"{C.RED}[ERROR]{C.RESET}"
    elif status == "START":
        stat = f"{C.GREEN}[STARTED]{C.RESET}"
    elif status == "PROCESSING":
        stat = f"{C.CYAN}[WORK]{C.RESET}"
    else:
        stat = f"{C.GREY}[{status}]{C.RESET}"
        
    extra = f" {C.GREY}>> {info}{C.RESET}" if info else ""
    
    print(f"{ts} {act} | {tgt} | status={stat}{extra}")

app = Flask(__name__)
PORT = 5000
current_file_path = None
file_type = None
VIDEO_FRAMES_DATA = {}
VIDEO_INFO = {}

if len(sys.argv) > 1 and sys.argv[1] == "--dialog":
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
        path = filedialog.askopenfilename(
            title="INCEL Media Selector",
            filetypes=[("Media", "*.jpg *.png *.jpeg *.mp4 *.avi *.mov *.webm"), ("All", "*.*")]
        )
        if path: print(path)
    except: pass
    sys.exit(0)

def open_file_dialog():
    try:
        cmd = [sys.executable, "--dialog"] if getattr(sys, 'frozen', False) else [sys.executable, __file__, "--dialog"]
        return subprocess.check_output(cmd, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0).decode("utf-8").strip()
    except: return None

def process_video_fast(path, res):
    global VIDEO_FRAMES_DATA, VIDEO_INFO
    smart_print("THREAD_START", "VideoProcessor", "OK", f"Processing {os.path.basename(path)}")
    
    try:
        cap = cv2.VideoCapture(path)
        if not cap.isOpened(): return

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        aspect = width / height
        out_w, out_h = (res, int(res / aspect)) if aspect >= 1 else (int(res * aspect), res)

        VIDEO_INFO = {"totalFrames": total, "width": max(1, out_w), "height": max(1, out_h), "fps": cap.get(cv2.CAP_PROP_FPS)}
        
        idx = 0
        while True:
            ret, frame = cap.read()
            if not ret: break
            VIDEO_FRAMES_DATA[idx] = cv2.cvtColor(cv2.resize(frame, (out_w, out_h), interpolation=cv2.INTER_NEAREST), cv2.COLOR_BGR2RGB).reshape(-1, 3).tolist()
            idx += 1
        
        cap.release()
        smart_print("THREAD_END", "VideoProcessor", "OK", f"Cached {idx} frames in memory")
        
    except Exception as e:
        smart_print("THREAD_ERR", "VideoProcessor", "FAIL", str(e))

@app.route('/seleccionar', methods=['GET'])
def select_file():
    global current_file_path, file_type, VIDEO_INFO, VIDEO_FRAMES_DATA
    
    smart_print("SYS_DIALOG", "UserInterface", "WAIT", "Waiting for user selection...")
    path = open_file_dialog()
    
    if path and os.path.exists(path):
        current_file_path = path
        name = os.path.basename(path)
        ext = os.path.splitext(path)[1].lower()
        file_type = 'video' if ext in ['.mp4', '.avi', '.mov', '.webm'] else 'image'
        
        VIDEO_INFO = {}; VIDEO_FRAMES_DATA = {}
        
        smart_print("FILE_LOAD", name, "OK", f"Type: {file_type.upper()}")
        return jsonify({"status": "ok", "msg": name, "type": file_type})
    
    smart_print("FILE_LOAD", "None", "FAIL", "Selection cancelled")
    return jsonify({"status": "cancel"})

@app.route('/construir', methods=['GET'])
def build_image():
    res = request.args.get('res', default=100, type=int)
    
    if file_type != 'image' or not current_file_path:
        smart_print("BUILD_REQ", "StaticImage", "FAIL", "No image selected")
        return jsonify({"error": "No image"})

    smart_print("BUILD_REQ", os.path.basename(current_file_path), "PROCESSING", f"Resolution: {res}x{res}")
    
    try:
        with Image.open(current_file_path) as img:
            img = img.resize((res, res), Image.Resampling.NEAREST).convert("RGB")
            w, h = img.size
            data = [{"x": i % w, "z": i // w, "color": "#{:02x}{:02x}{:02x}".format(*p)} for i, p in enumerate(img.getdata())]
            
            smart_print("DATA_SEND", "RobloxPlugin", "OK", f"Payload: {len(data)} voxels")
            return jsonify(data)
    except Exception as e:
        smart_print("BUILD_ERR", "Processing", "FAIL", str(e))
        return jsonify({"error": str(e)})

@app.route('/init', methods=['GET'])
def init_video():
    res = request.args.get('res', default=50, type=int)
    if file_type == 'video' and current_file_path:
        if not VIDEO_INFO or VIDEO_INFO.get('width') != res:
            smart_print("VIDEO_INIT", "BackgroundWorker", "START", f"Re-baking at {res}px")
            threading.Thread(target=process_video_fast, args=(current_file_path, res)).start()
        return jsonify({"status": "started"})
    return jsonify({"error": "No video"})

@app.route('/frame/<int:index>', methods=['GET'])
def get_frame(index):
    if index % 100 == 0:
         smart_print("STREAM", f"Frame_{index}", "SENDING", "Syncing with client...")
         
    if index in VIDEO_FRAMES_DATA:
        return jsonify({"colors": VIDEO_FRAMES_DATA[index]})
    return jsonify({"status": "buffering"})

if __name__ == '__main__':
    print_banner()
    
    anim_thread = threading.Thread(target=animate_waiting)
    anim_thread.daemon = True
    anim_thread.start()
    
    try:
        app.run(host='127.0.0.1', port=PORT, threaded=True)
    except Exception as e:
        print(f"\n{C.RED}[CRITICAL ERROR]{C.RESET} {e}")