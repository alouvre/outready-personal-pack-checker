# OutReady

**OutReady** adalah prototipe asisten pribadi berbasis AI yang membantu pengguna memeriksa kelengkapan barang bawaan sebelum keluar rumah. Sistem ini menggunakan Object Detection dan pengingat berbasis kamera untuk memastikan semua item penting sudah dibawa.

## Fitur Utama

- Pengambilan dataset gambar melalui GUI
- Labeling dengan Label Studio
- Pelatihan model Object Detection (YOLO)
- Sistem deteksi real-time dengan notifikasi


## Struktur Proyek

├──outready-personal-pack-checker/
     ├── app.py                 # GUI untuk ambil gambar dataset
     ├── requirements.txt       # Semua dependencies Python
     ├── dataset/
     │   ├── raw/               # Hasil capture gambar mentah
     │   └── labeled/           # Label hasil dari Label Studio (format COCO/Yolo/XML)
     │
     ├── label_studio_config/   # Konfigurasi labeling custom
     │
     ├── training/
     │   ├── prepare_dataset.py # Convert dari Label Studio ke format Yolo/COCO
     │   ├── train.py           # Script training object detection model
     │   └── model/             # Folder menyimpan checkpoint model
     │
     ├── inference/
     │   ├── detect.py          # Skrip inferensi dari model terlatih
     │   └── assets/            # Contoh gambar deteksi dan visualisasi
     │
     └── README.md              # Penjelasan proyek