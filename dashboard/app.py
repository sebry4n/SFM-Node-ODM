import os
import cv2
import time
import json
import queue
import threading
import subprocess
import requests
from flask import Flask, render_template, Response, jsonify

app = Flask(__name__)

URL_RELAY = "http://192.168.200.219/relay/all"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sfm_dataset")
os.makedirs(OUTPUT_DIR, exist_ok=True)

log_queue = queue.Queue()
latest_frame = None
camera_lock = threading.Lock()

def add_log(msg):
    print(msg)
    log_queue.put(msg)

def camera_loop():
    global latest_frame
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if ret:
            with camera_lock:
                latest_frame = frame.copy()
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
            time.sleep(2.0)
            
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
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "odm.py")
        # Run using virtual environment's python if possible, or just python3
        # Since app.py is running in venv, sys.executable points to it.
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
