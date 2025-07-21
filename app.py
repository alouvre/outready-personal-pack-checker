import os
import cv2
import time
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
from datetime import datetime

# ==== Konfigurasi awal ====
SAVE_DIR = "dataset/raw"
MODES = ["Default", "Mirror"]
RESOLUTIONS = {
    "640x480": (640, 480),
    "1280x720": (1280, 720),
    # "1920x1080": (1920, 1080),
}

# Ukuran tetap untuk tampilan preview (canvas)
CANVAS_WIDTH = 640
CANVAS_HEIGHT = 480

# Pastikan folder penyimpanan ada
os.makedirs(SAVE_DIR, exist_ok=True)

# ==== CustomTkinter Config ====
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


# ==== GUI ====
class CameraApp:
    """Aplikasi GUI pengambilan gambar dengan webcam."""
    def __init__(self, root):
        self.root = root
        self.root.geometry("1080x720")

        # State
        self.selected_mode = ctk.StringVar(value=MODES[1])
        self.selected_resolution = ctk.StringVar(value="640x480")
        self.selected_camera_id = ctk.StringVar(value="0")
        self.available_camera_ids = detect_available_cameras()
        self.brightness_value = ctk.IntVar(value=0)
        self.current_camera_id = 0

        # Inisialisasi kamera
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.set_resolution("640x480")
        self.is_updating = True  # flag untuk pause/resume update_frame

        self.root.title("OutReady - Capture Image")
        self.build_ui()
        self.update_frame()

    # Bangun UI
    def build_ui(self):
        self.build_top_controls()
        self.build_right_controls()
        self.build_canvas()
        self.build_buttons()

    # -------------------------------------------
    # ----------- Panel Kontrol Atas -----------
    # -------------------------------------------
    def build_top_controls(self):
        """Bangun panel kontrol atas secara modular dan scalable."""
        self.top_controls_frame = ctk.CTkFrame(self.root)
        self.top_controls_frame.pack(padx=10, pady=10, fill="x")

        self.top_feature_builders = [
            self.build_camera_id_selector,
            self.build_camera_mode_control,
            self.build_resolution_selector,
            # Tambahkan fungsi kontrol lainnya di sini:
            # self.build_device_selector,
        ]

        for builder in self.top_feature_builders:
            section_frame = ctk.CTkFrame(
                self.top_controls_frame,
                fg_color="transparent"
                )
            section_frame.pack(side="left", padx=10, pady=10)
            builder(section_frame)

    # -------------------------------------------
    # ----------- Panel Kontrol Kanan -----------
    # -------------------------------------------
    def build_right_controls(self):
        """Bangun panel kontrol kanan secara modular dan scalable."""
        self.right_controls_frame = ctk.CTkFrame(self.root)
        self.right_controls_frame.pack(side="right", padx=10, pady=10, fill="y")

        self.feature_builders = [
            self.build_brightness_control,
            # Tambahkan fungsi-fungsi kontrol lain di sini
            # self.build_contrast_control,
            # self.build_zoom_control,
        ]

        for builder in self.feature_builders:
            section_frame = ctk.CTkFrame(self.right_controls_frame)
            section_frame.pack(pady=10, fill="x", padx=5)
            builder(section_frame)

# -------------------------------------------
# --------------- Panel Utama ---------------
# -------------------------------------------
    def build_canvas(self):
        """Bangun area tampilan kamera."""
        self.image_label = ctk.CTkLabel(self.root, text="")
        self.image_label.pack(pady=10)

    def build_buttons(self):
        """Bangun tombol kontrol bawah."""
        self.capture_btn = ctk.CTkButton(
            self.root,
            text="Take Picture",
            font=("Arial", 14),
            command=self.capture_image,
            corner_radius=32,
            height=40,
            width=35
        )
        self.capture_btn.pack(pady=10)

    def update_frame(self):
        """Ambil frame dari kamera, olah, dan tampilkan."""
        if self.is_updating and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Simpan frame terakhir untuk disimpan saat klik tombol
                processed = self.process_frame(frame)
                self.current_frame = processed.copy()

                # Resize frame ke ukuran canvas tetap
                resized = cv2.resize(processed, (CANVAS_WIDTH, CANVAS_HEIGHT))

                # Convert ke ImageTk
                frame_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ctk.CTkImage(light_image=img, size=(CANVAS_WIDTH, CANVAS_HEIGHT))
                self.image_label.configure(image=imgtk)
                self.image_label.image = imgtk

                self.image_label.configure(image=imgtk)
                self.image_label.image = imgtk

        self.root.after(10, self.update_frame)

    def process_frame(self, frame):
        """Proses frame: mirror dan brightness."""
        # Mirror jika dipilih
        if self.selected_mode.get() == "Mirror":
            frame = cv2.flip(frame, 1)

        # Brightness adjustment
        brightness = self.brightness_value.get()
        return cv2.convertScaleAbs(frame, alpha=1.0, beta=brightness)

    def capture_image(self):
        """Simpan frame saat ini ke file .jpg."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"image_{timestamp}.jpg"
        path = os.path.join(SAVE_DIR, filename)
        cv2.imwrite(path, self.current_frame)
        messagebox.showinfo("Sukses", f"Gambar disimpan di:\n{path}")

    # ------------------------------------------------------
    # ----------- Fitur-Fitur Panel Kontrol Atas -----------
    # ------------------------------------------------------
    def build_camera_mode_control(self, parent):
        """Kontrol pilihan mode kamera (normal/mirror)."""
        ctk.CTkLabel(
            parent,
            text="Camera Mode:",
            font=("Arial", 12)
            ).pack(anchor="w")
        self.mode_menu = ctk.CTkOptionMenu(
            parent, values=MODES, variable=self.selected_mode
        )
        self.mode_menu.pack()

    def build_camera_id_selector(self, parent):
        ctk.CTkLabel(
            parent,
            text="Camera ID:",
            font=("Arial", 12)
            ).pack(anchor="w")
        camera_menu = ctk.CTkOptionMenu(
            parent,
            values=self.available_camera_ids,
            variable=self.selected_camera_id,
            command=self.change_camera
        )
        camera_menu.pack()

    def change_camera(self, selected_id):
        try:
            selected_id = int(selected_id)
            if selected_id == self.current_camera_id:
                return  # Kamera sama, tidak perlu ganti

            if not self.is_camera_available(selected_id):
                raise ValueError("Kamera tidak tersedia.")

            # Pause update frame
            self.is_updating = False

            if self.cap.isOpened():
                self.cap.release()
                time.sleep(0.3)

            self.cap = cv2.VideoCapture(selected_id)
            self.change_resolution(self.selected_resolution.get())

            # Update ID kamera aktif
            self.current_camera_id = selected_id

            self.is_updating = True  # resume update

        except Exception as e:
            messagebox.showerror(
                "Gagal Mengganti Kamera",
                f"Tidak bisa mengakses kamera ID {selected_id}.\n\n{e}"
            )

    def is_camera_available(self, index):
        test_cap = cv2.VideoCapture(index)
        if test_cap is None or not test_cap.isOpened():
            return False
        test_cap.release()
        return True

    def build_resolution_selector(self, parent):
        ctk.CTkLabel(
            parent,
            text="Resolution:",
            font=("Arial", 12)
            ).pack(anchor="w")
        resolution_menu = ctk.CTkOptionMenu(
            parent, values=list(RESOLUTIONS.keys()), variable=self.selected_resolution,
            command=self.set_resolution
        )
        resolution_menu.pack()

    def change_resolution(self, selected_resolution):
        try:
            width, height = map(int, selected_resolution.split("x"))
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        except Exception as e:
            messagebox.showerror("Resolusi Gagal", f"Resolusi tidak bisa diatur: {e}")

    def set_resolution(self, resolution):
        self.is_updating = False
        try:
            width, height = RESOLUTIONS[resolution]
            if self.cap and self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            self.is_updating = True
        except Exception as e:
            messagebox.showerror("Gagal Mengatur Resolusi", str(e))

    # ------------------------------------------------------
    # ----------- Fitur-Fitur Panel Kontrol Kanan -----------
    # ------------------------------------------------------
    def build_brightness_control(self, parent):
        """Bangun kontrol brightness dalam frame terpisah."""
        label_row = ctk.CTkFrame(parent, fg_color="transparent")
        label_row.pack(fill="x", padx=5, pady=(0, 5))

        # Label kiri
        ctk.CTkLabel(
            label_row,
            text="Brightness",
            font=("Arial", 12),
            ).grid(row=0, column=0, sticky="w")

        # Label kanan (dalam kotak)
        self.brightness_label = ctk.CTkLabel(
            label_row,
            text=f"{self.brightness_value.get()}",
            font=("Arial", 12),
            fg_color="#e0e0e0",  # warna latar abu-abu muda
            corner_radius=8,
            text_color="black",
            width=35,
            height=18,
            anchor="center"
        )
        self.brightness_label.grid(row=0, column=1, sticky="e", padx=(5, 0))
        label_row.grid_columnconfigure(0, weight=1)  # Membuat label kiri mendorong ke kiri

        self.brightness_slider = ctk.CTkSlider(
            parent,
            from_=-100,
            to=100,
            variable=self.brightness_value,
            orientation="horizontal",
            width=200,
            command=self.update_brightness_label  # <-- diperbaiki
        )
        self.brightness_slider.pack(pady=(0, 5))

        ctk.CTkButton(
            parent,
            text="Reset",
            font=("Arial", 12),
            command=self.reset_brightness,
            width=35,
            height=20
        ).pack(pady=5)

    def update_brightness_label(self, value):
        """Update label nilai brightness saat slider digeser."""
        self.brightness_label.configure(text=f"{int(float(value))}")

    def reset_brightness(self):
        """Reset nilai brightness ke default."""
        self.brightness_value.set(0)
        self.update_brightness_label(0)

    def on_closing(self):
        """Lepaskan kamera dan keluar aplikasi."""
        if self.cap.isOpened():
            self.cap.release()
        self.root.destroy()


def detect_available_cameras(max_tested=5):
    available = []
    for i in range(max_tested):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            available.append(str(i))
            cap.release()
    return available


if __name__ == "__main__":
    root = ctk.CTk()
    app = CameraApp(root)
    root.mainloop()
