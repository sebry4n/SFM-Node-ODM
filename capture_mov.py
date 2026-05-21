import cv2
import requests
import time
import json
import os

# Konfigurasi
URL_RELAY = "http://192.168.200.219/relay/all" 
OUTPUT_DIR = "sfm_dataset"
DELAY_STABIL = 2.0 

# Buat folder jika belum ada
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"Folder '{OUTPUT_DIR}' telah dibuat.")

def send_command(states):
    payload = {'states': json.dumps(states)}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        r = requests.post(URL_RELAY, data=payload, headers=headers, timeout=3)
        print(f"Relay: {states}")
    except Exception as e:
        print(f"Koneksi Gagal: {e}")

def capture(index):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Kamera tidak terdeteksi!")
        return
    
    # Stabilisasi sensor
    for _ in range(10):
        cap.read()
        
    ret, frame = cap.read()
    if ret:
        # Simpan ke folder sfm_dataset
        img_path = os.path.join(OUTPUT_DIR, f"frame_{index:03d}.jpg")
        cv2.imwrite(img_path, frame)
        print(f"Saved: {img_path}")
    
    cap.release()

def main():
    print(f"Memulai pengambilan data untuk SfM di folder: {OUTPUT_DIR}\n")
    
    # Loop untuk 12 posisi sesuai permintaan sebelumnya
    for i in range(12):
        # Pola biner: bit 0-7 dikontrol oleh angka i
        # LSB ke MSB (pos 1: 000, pos 2: 100, dst)
        current_states = ["on" if (i >> j) & 1 else "off" for j in range(8)]
        
        print(f"--- Iterasi {i+1}/12 ---")
        
        # 1. Update Relay
        send_command(current_states)
        
        # 2. Tunggu hardware/posisi stabil
        time.sleep(DELAY_STABIL)
        
        # 3. Ambil foto
        capture(i + 1)

    print(f"\nDon! {i+1} images captured in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()