import os
import cv2
import time
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
from datetime import datetime

# ---------------------------------------------------
# --------------- Konfigurasi Awal ------------------
# ---------------------------------------------------
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


# ---------------------------------------------------
# --------------------- GUI -------------------------
# ---------------------------------------------------
class CameraApp:
    """Aplikasi GUI pengambilan gambar dengan webcam."""
    def __init__(self, root):
        self.root = root
        # Hitung ukuran layar
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Ukuran proporsional
        window_width = int(screen_width * 0.85)
        window_height = int(screen_height * 0.85)

        # Posisi tengah
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # State Global
        self.selected_camera_id = ctk.StringVar(value="0")
        self.selected_mode = ctk.StringVar(value=MODES[1])
        self.selected_resolution = ctk.StringVar(value="640x480")
        self.available_camera_ids = detect_available_cameras()
        self.brightness_value = ctk.IntVar(value=0)

        self.current_camera_id = 0
        self.window_width = int(screen_width * 0.85)
        self.setting_info_label = None

        # Inisialisasi kamera
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.set_resolution("640x480")
        self.is_updating = True  # flag untuk pause/resume update_frame

        # Inisialisasi nilai default untuk settingan pengambilan gambar
        self.capture_settings = {
            "count": 1,
            "delay": 2,
        }

        self.root.title("OutReady - Capture Image")
        self.build_ui()
        self.update_frame()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # -------------------------------------------
    # --------------- Build UI ------------------
    # -------------------------------------------
    def build_ui(self):
        self.build_top_controls()
        self.build_right_controls()
        self.build_left_controls()  # Label baru dibangun terakhir
        self.build_canvas()
        self.build_buttons()

    # -------------------------------------------
    # ----------- Panel Kontrol Atas -----------
    # -------------------------------------------
    def build_top_controls(self):
        """Bangun panel kontrol atas secara modular dan scalable."""
        # Buat frame utama panel atas
        self.top_controls_frame = ctk.CTkFrame(self.root)
        self.top_controls_frame.pack(padx=10, pady=10, fill="x")

        # Builder section terpisah
        self.top_feature_builders = [
            self.build_camera_id_selector,
            self.build_camera_mode_control,
            self.build_resolution_selector,
        ]

        # Bangun tiap section di dalam panel atas
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
        # Hitung 20% dari lebar jendela untuk panel kanan (kamu sudah simpan ke self.window_width sebelumnya)
        right_width = int(self.window_width * 0.20)

        # Buat frame utama panel kanan
        self.right_controls_frame = ctk.CTkFrame(self.root, width=right_width)
        self.right_controls_frame.pack(side="right", padx=10, pady=10, fill="y")

        # Builder section terpisah
        self.feature_builders = [
            self.build_brightness_control,
            # Tambahkan fungsi-fungsi kontrol lain di sini
            # self.build_contrast_control,
            # self.build_zoom_control,
        ]

        # Bangun tiap section di dalam panel kanan
        for builder in self.feature_builders:
            section_frame = ctk.CTkFrame(self.right_controls_frame)
            section_frame.pack(pady=10, fill="x", padx=5)
            builder(section_frame)

    # -------------------------------------------
    # ----------- Panel Kontrol Kiri ------------
    # -------------------------------------------
    def build_left_controls(self):
        """Bangun panel kontrol kiri secara modular dan scalable."""
        # Hitung 20% dari lebar jendela untuk panel kiri (kamu sudah simpan ke self.window_width sebelumnya)
        left_width = int(self.window_width * 0.20)

        # Buat frame utama panel kiri
        self.left_controls_frame = ctk.CTkFrame(self.root, width=left_width)
        self.left_controls_frame.pack(side="left", padx=10, pady=10, fill="y")

        # Builder section terpisah
        self.feature_builders = [
            # Tambahkan fungsi-fungsi kontrol lain di sini
            self.build_setting_info_section,
        ]

        # Bangun tiap section di dalam panel kiri
        for builder in self.feature_builders:
            section_frame = ctk.CTkFrame(self.left_controls_frame)
            section_frame.pack(pady=10, fill="x", padx=5)
            section_frame.pack_propagate(False)
            builder(section_frame)

# -----------------------------------------------
# ----------------- Panel Utama -----------------
# -----------------------------------------------
    def build_canvas(self):
        """Bangun area tampilan kamera."""
        self.image_label = ctk.CTkLabel(self.root, text="")
        self.image_label.pack(expand=False, fill="both", pady=10)

    def build_buttons(self):
        """Bangun tombol kontrol bawah."""
        button_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        button_frame.pack(pady=10)

        self.start_btn = ctk.CTkButton(
            button_frame,
            text="Start",
            font=("Arial", 14),
            # command=self.capture_loop,
            command=self.start_capture_process,
            corner_radius=32,
            height=40,
            width=150
        )
        self.start_btn.pack(side="left", padx=10, expand=True)

        self.capture_setting_btn = ctk.CTkButton(
            button_frame,
            text="Capture Setting",
            font=("Arial", 14),
            # command=self.capture_loop,
            command=self.open_capture_setting_popup,
            corner_radius=32,
            height=40,
            width=150
        )
        self.capture_setting_btn.pack(side="left", padx=10, expand=True)

    def update_frame(self):
        """Ambil frame dari kamera, olah, dan tampilkan."""
        if self.is_updating and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                messagebox.showerror("Gagal", "Tidak dapat mengambil gambar.")
                self.is_updating = True
                return

            if ret:
                # Resize frame ke ukuran canvas tetap
                resized = cv2.resize(frame, (CANVAS_WIDTH, CANVAS_HEIGHT))

                # Simpan frame terakhir untuk disimpan saat klik tombol
                processed = self.process_frame(resized)
                self.current_frame = processed.copy()

                # Convert ke ImageTk
                frame_rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ctk.CTkImage(light_image=img, size=(CANVAS_WIDTH, CANVAS_HEIGHT))

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

    def start_capture_process(self):
        """Inisiasi proses capture burst dengan indikator visual non-blocking."""
        self.image_index = 0
        self.total_images = self.capture_settings["count"]
        self.delay_ms = int(self.capture_settings["delay"] * 1000)  # dalam milidetik
        self.capture_loop()

    def capture_loop(self):
        """Mengambil sejumlah gambar dengan jeda tertentu untuk kebutuhan dataset burst."""
        """Loop pengambilan gambar secara non-blocking + indikator visual."""
        # try:
        if self.image_index < self.total_images:
            ret, frame = self.cap.read()
            if not ret:
                messagebox.showerror("Gagal", "Tidak dapat mengambil gambar.")
                return

            # Simpan gambar
            save_dir = os.path.join(SAVE_DIR)
            os.makedirs(save_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}.jpg" # Tambahkan settingan milih jpg atau png atau yang lain
            path = os.path.join(SAVE_DIR, filename)
            cv2.imwrite(path, self.current_frame)

            # ✅ Update label info capture (misalnya di panel kiri)
            if hasattr(self, "setting_info_label"):
                self.setting_info_label.configure(
                    text=f"Mengambil gambar {self.image_index + 1}/{self.total_images}"
                )

            self.image_index += 1

            # ⏳ Delay antar capture, non-blocking
            self.root.after(self.delay_ms, self.capture_loop)

        else:
            # ✅ Setelah selesai ambil semua gambar
            if hasattr(self, "setting_info_label"):
                self.setting_info_label.configure(text="Pengambilan selesai ✅")

        # except Exception as e:
        #     messagebox.showerror("[ERROR]", f"Terjadi kesalahan saat menyimpan gambar.\n{e}")

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
            parent, values=MODES, variable=self.selected_mode,
            command=lambda _: self.update_setting_info_display()
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
            self.update_setting_info_display()

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
            self.update_setting_info_display()
        except Exception as e:
            messagebox.showerror("Gagal Mengatur Resolusi", str(e))

    # ------------------------------------------------------
    # ----------- Fitur-Fitur Panel Kontrol Kanan ----------
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
            anchor="w"
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
        self.update_setting_info_display()

    def reset_brightness(self):
        """Reset nilai brightness ke default."""
        self.brightness_value.set(0)
        self.update_brightness_label(0)

    # ------------------------------------------------------
    # ----------- Fitur-Fitur Panel Kontrol Kiri -----------
    # ------------------------------------------------------
    def build_setting_info_section(self, parent):
        """Panel info pengaturan pengambilan gambar."""
        label_row = ctk.CTkFrame(parent, fg_color="transparent")
        label_row.pack(fill="x", padx=5, pady=(0, 5))

        # Judul section
        title = ctk.CTkLabel(
            label_row,
            text="Information Setting",
            font=("Arial", 12, "bold"),
            anchor="w")
        title.pack(fill="x", pady=(0, 5))

        # Label info setting (multiline)
        self.setting_info_label = ctk.CTkLabel(
            label_row,
            text=self.get_capture_setting_text(),
            font=("Arial", 12),
            justify="left",
            anchor="w"
        )
        self.setting_info_label.pack(fill="x", pady=(0, 5))

    def get_capture_setting_text(self):
        return (
            f"Total Image: {self.capture_settings['count']}\n"
            f"Delay: {self.capture_settings['delay']} s\n"
            f"Camera ID: {self.selected_camera_id.get()}\n"
            f"Mode: {self.selected_mode.get()}\n"
            f"Resolution: {self.selected_resolution.get()}\n"
            f"Brightness: {self.brightness_value.get()}\n"
        )

    def update_setting_info_display(self):
        try:
            self.setting_info_label.configure(text=self.get_capture_setting_text())
        except AttributeError:
            # Label belum dibangun
            pass

# --------------------------------------------------------------
# ------------------- Pop up Capture Setting -------------------
# --------------------------------------------------------------
    def open_capture_setting_popup(self):
        if not self.cap or not self.cap.isOpened():
            messagebox.showerror(
                "Kamera Tidak Aktif",
                "Tidak dapat membuka popup capture karena kamera tidak aktif."
                )
            return

        # Pause update frame sementara
        self.is_updating = True

        popup = ctk.CTkToplevel(self.root)
        popup.title("Pengaturan Capture Gambar")
        popup.geometry("420x250")
        popup.transient(self.root)         # Supaya tetap di depan
        popup.grab_set()                   # Modal: tidak bisa interaksi jendela utama
        popup.focus_force()

        # Posisikan di tengah layar utama
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        popup.update_idletasks()
        pw = popup.winfo_width()
        ph = popup.winfo_height()
        popup.geometry(f"+{x + (w - pw)//2}+{y + (h - ph)//2}")

        # ================== UI Elements ===================
        # Frame utama
        content = ctk.CTkFrame(popup)
        content.pack(expand=True, fill="both", padx=20, pady=20)
        content.grid_columnconfigure(1, weight=1)

        # INPUT : Jumlah Gambar
        ctk.CTkLabel(
            content,
            text="Total Image:",
            font=("Arial", 12),
            anchor="w").grid(row=0, column=0, sticky="w", padx=5, pady=(5, 0))
        count_entry = ctk.CTkEntry(content)
        count_entry.insert(0, "1")

        count_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=(5, 0))

        # INPUT : Delay antar gambar
        ctk.CTkLabel(
            content,
            text="Delay (seconds):",
            font=("Arial", 12),
            anchor="w").grid(row=1, column=0, sticky="w", padx=5, pady=(10, 0))

        delay_entry = ctk.CTkEntry(content)
        delay_entry.insert(0, "0.2")
        delay_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=(10, 0))

        # Tombol Simpan
        def save_settings():
            try:
                count = max(1, int(count_entry.get()))
            except ValueError:
                count = 1
            try:
                delay = max(0.0, float(delay_entry.get()))
            except ValueError:
                delay = 0.2

            if not count:
                messagebox.showwarning("Jumlah Gambar Kosong", "Mohon masukkan jumlah gambar.")
                return

            self.capture_settings["count"] = count
            self.capture_settings["delay"] = delay
            self.update_setting_info_display()

            popup.destroy()
            self.is_updating = True

        save_btn = ctk.CTkButton(
            content,
            text="Save",
            command=save_settings,
            font=("Arial", 14),
            corner_radius=32,
            height=32
        )
        save_btn.grid(row=2, column=0, columnspan=2, pady=(20, 10))

        # Handle saat popup ditutup manual
        def on_close():
            self.is_updating = True
            popup.destroy()

        popup.protocol("WM_DELETE_WINDOW", on_close)

# ------------------------------------------------------
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
