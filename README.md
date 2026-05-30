# UR5 Photogrammetry & 3D Scanner Auto-Scan

Projek ini adalah sistem otomasi 3D Scanner (Fotogrametri) menggunakan integrasi antara **Hardware (ESP/Relay)**, **Web Dashboard (Flask)**, dan **OpenDroneMap (NodeODM)**. Sistem akan memutar objek dalam 12 posisi, mengambil foto otomatis, dan memprosesnya menjadi model 3D (`.obj`) secara langsung.

## Arsitektur Sistem
1. **Frontend (Dashboard)**: Dibangun dengan HTML, Vanilla CSS (Dark Mode), dan JavaScript. Dilengkapi dengan **Three.js** untuk me-render hasil 3D langsung di browser.
2. **Backend (Python Flask)**: Mengurus logika *routing*, video stream, dan *real-time logging*. Backend menggunakan `cv2` untuk kontrol kamera, deteksi *hardware name* kamera, dan matikan fitur *autofokus*.
3. **Hardware Control**: Backend mengirim *HTTP Request* ke Relay IP (misal: `192.168.200.219`) untuk memutar meja dan lampu sesuai 12 posisi yang diatur secara biner.
4. **Mesin Fotogrametri**: NodeODM berjalan di Docker dan dieksekusi via `odm.py` untuk menjahit foto-foto yang diambil menjadi *3D model* utuh beresolusi tinggi (*Ultra Quality*, *Orthophoto*, *Background Removal*).

---

## 🚀 Cara Menjalankan

Ada dua cara untuk menjalankan projek ini:

### Cara 1: Menggunakan Docker (Sangat Disarankan)
Cara ini paling mudah karena **Dashboard** dan **NodeODM** akan otomatis berjalan tanpa perlu menginstall library OpenCV secara manual di komputermu.

1. Buka terminal di dalam folder project ini.
2. Jalankan perintah:
   ```bash
   docker-compose up --build
   ```
   *(NodeODM akan otomatis jalan di port 3001, dan Dashboard di port 5000).*
3. Buka browser dan kunjungi: **[http://localhost:5000](http://localhost:5000)**

### Cara 2: Manual Menggunakan Python Venv
Gunakan cara ini jika hanya ingin menjalankan Dashboard tanpa docker (Namun, NodeODM tetap wajib dijalankan di Docker).

1. Jalankan NodeODM di terminal terpisah:
   ```bash
   docker run -p 3001:3000 opendronemap/nodeodm
   ```
2. Setup *Virtual Environment* untuk Dashboard:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r dashboard/requirements.txt
   ```
3. Jalankan aplikasi:
   ```bash
   cd dashboard
   python app.py
   ```
4. Buka browser: **[http://localhost:5000](http://localhost:5000)**

---

## 🛠 Panduan Penggunaan Dashboard

1. **Pilih Kamera**: Sistem mendukung kamera terintegrasi dan *webcam/external camera*. Pilih nama kameramu di dropdown. Jika kamera terputus atau dicabut, sistem akan otomatis melakukan *fallback* ke kamera lain yang tersedia. Fitur **Autofokus** sudah dimatikan agar objek tidak blur.
2. **Mulai Capture (12 Posisi)**:
   - Tekan tombol **Mulai Capture**.
   - Sistem akan menyalakan relay/memutar hardware, lalu menjepret foto.
   - Akan ada **Jeda (delay) 10 detik** setiap kali jepret agar putaran meja benar-benar stabil, baru lanjut ke posisi berikutnya.
   - Hasil foto masuk ke `sfm_dataset` dan akan otomatis tampil di **Galeri Dataset** web.
3. **Proses 3D Model**:
   - Setelah 12 foto siap, klik **Proses 3D Model**.
   - Proses ini akan mengirim foto ke NodeODM. Waktu pemrosesan bergantung spesifikasi PC.
   - Jika selesai, file hasilnya (`.obj`, `.tif`, `.png`) akan ada di folder `output_assets`.
   - Browser akan otomatis merender (menampilkan) 3D Model yang bisa diputar-putar langsung di halaman web. File mentah juga bisa langsung didownload melalui *List Download* di kanan viewer.
