import os
import cv2
import time
import json
import queue
import threading
import subprocess
import requests
from flask import Flask, render_template, Response, jsonify, send_from_directory, request

app = Flask(__name__)

URL_RELAY = "http://192.168.200.219/relay/all"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "sfm_dataset")
ASSETS_DIR = os.path.join(BASE_DIR, "output_assets")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

log_queue = queue.Queue()
latest_frame = None
camera_lock = threading.Lock()

camera_index = 0
cap = None

def add_log(msg):
    print(msg)
    log_queue.put(msg)

cap_lock = threading.Lock()

def init_camera(idx):
    global cap
    with cap_lock:
        if cap is not None:
            cap.release()
        cap = cv2.VideoCapture(idx)
       
        cap.set(cv2.CAP_PROP_AUTOFOCUS,1) # Matikan Autofokus (0) kalo nyala (1)

init_camera(camera_index)

def get_camera_list():
    cams = []
    seen_names = {}
    for path in glob.glob('/sys/class/video4linux/video*'):
        try:
            idx = int(os.path.basename(path).replace('video', ''))
            with open(os.path.join(path, 'name'), 'r') as f:
                name = f.read().strip()
            if name not in seen_names or idx < seen_names[name]:
                seen_names[name] = idx
        except Exception:
            pass
    for name, idx in seen_names.items():
        cams.append({"index": idx, "name": f"{name} (video{idx})"})
    cams.sort(key=lambda x: x["index"])
    return cams

def camera_loop():
    global latest_frame, camera_index
    fail_count = 0
    while True:
        ret = False
        with cap_lock:
            if cap is not None and cap.isOpened():
                ret, frame = cap.read()
                
        if ret:
            with camera_lock:
                latest_frame = frame.copy()
            fail_count = 0
        else:
            fail_count += 1
            if fail_count > 15: # Timeout ~0.5 detik
                cams = get_camera_list()
                available = [c["index"] for c in cams]
                if available and camera_index not in available:
                    new_idx = available[0]
                    add_log(f"Kamera terputus! Fallback otomatis ke kamera {new_idx}")
                    camera_index = new_idx
                    init_camera(camera_index)
                fail_count = 0
        time.sleep(0.03)

threading.Thread(target=camera_loop, daemon=True).start()

def generate_video():
    while True:
        if latest_frame is not None:
            with camera_lock:
                ret, buffer = cv2.imencode('.jpg', latest_frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.05)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_video(), mimetype='multipart/x-mixed-replace; boundary=frame')

import glob

@app.route('/api/cameras', methods=['GET'])
def get_cameras():
    return jsonify({"cameras": get_camera_list(), "current": camera_index})

@app.route('/api/camera/switch', methods=['POST'])
def switch_camera():
    global camera_index
    data = request.json
    idx = data.get('index', 0)
    camera_index = int(idx)
    init_camera(camera_index)
    add_log(f"Switched to camera {camera_index}")
    return jsonify({"status": "success", "current": camera_index})

@app.route('/api/capture', methods=['POST'])
def capture_start():
    def task():
        add_log("Mulai capture 12 posisi...")
        for i in range(12):
            states = ["on" if (i >> j) & 1 else "off" for j in range(8)]
            add_log(f"Posisi {i+1}/12 - Relay: {states}")
            try:
                requests.post(URL_RELAY, data={'states': json.dumps(states)}, timeout=3)
            except Exception as e:
                add_log(f"Relay Error: {e}")
            time.sleep(13.0)
            
            if latest_frame is not None:
                img_path = os.path.join(OUTPUT_DIR, f"frame_{i+1:03d}.jpg")
                with camera_lock:
                    cv2.imwrite(img_path, latest_frame)
                add_log(f"Tersimpan: {img_path}")
        add_log("Capture selesai!")
        
    threading.Thread(target=task).start()
    return jsonify({"status": "started"})

@app.route('/api/process', methods=['POST'])
def process_odm():
    def task():
        add_log("Mulai proses 3D dengan OpenDroneMap...")
        script_path = os.path.join(BASE_DIR, "odm.py")
        import sys
        process = subprocess.Popen([sys.executable, script_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            add_log(line.strip())
        process.wait()
        add_log("Proses 3D Selesai!")
        
    threading.Thread(target=task).start()
    return jsonify({"status": "started"})

@app.route('/api/logs')
def logs():
    def generate():
        while True:
            msg = log_queue.get()
            yield f"data: {msg}\n\n"
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/dataset', methods=['GET'])
def get_dataset():
    files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.jpg') or f.endswith('.png')])
    return jsonify({"files": files})

@app.route('/dataset/<path:filename>')
def serve_dataset(filename):
    return send_from_directory(OUTPUT_DIR, filename)

@app.route('/api/results', methods=['GET'])
def get_results():
    results = []
    if os.path.exists(ASSETS_DIR):
        for root, dirs, files in os.walk(ASSETS_DIR):
            for file in files:
                rel_dir = os.path.relpath(root, ASSETS_DIR)
                if rel_dir == ".":
                    path = file
                else:
                    path = os.path.join(rel_dir, file)
                results.append(path)
    return jsonify({"files": results})

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(ASSETS_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
