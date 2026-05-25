# Cara Menjalankan Project (Docker Version)

Project ini sekarang sudah sepenuhnya di-dockerize. Artinya, kamu tidak perlu menginstall Python, virtual environment, atau OpenCV secara manual di komputermu. Semua kebutuhan (Dashboard + Engine 3D NodeODM) sudah terpaket jadi satu.

## Prasyarat
- Komputer dengan sistem operasi Linux/Ubuntu (Direkomendasikan agar akses `/dev/video*` lancar).
- Terinstall **Docker** dan **Docker Compose**.

## Langkah Menjalankan

1. Buka Terminal di dalam folder project ini.
2. Jalankan perintah berikut:
   ```bash
   docker-compose up --build
   ```
   *(Catatan: Perintah ini mungkin membutuhkan waktu agak lama saat pertama kali dijalankan karena Docker akan mendownload image NodeODM (~beberapa GB) dan menginstall OpenCV di dalam container).*
3. Setelah muncul log `Running on http://0.0.0.0:5000`, buka browser dan kunjungi:
   **[http://localhost:5000](http://localhost:5000)**

## Catatan Penting
- Container ini disetting dengan mode `privileged: true` dan me-mount `/dev:/dev`. Hal ini bertujuan agar jika kamu **Mencabut atau Mencolok Kamera USB (Webcam)**, sistem di dashboard bisa langsung mendeteksinya secara *real-time* tanpa harus restart container.
- Hasil foto 2D akan disimpan secara permanen di folder `sfm_dataset`.
- Hasil render 3D (.obj) akan disimpan secara permanen di folder `output_assets`.
- Untuk mematikan server, tekan `CTRL+C` di terminal tempat docker berjalan, lalu ketik `docker-compose down`.
