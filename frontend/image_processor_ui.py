import sys
import os
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QFrame, QScrollArea,
    QSizePolicy, QProgressBar, QStatusBar, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QImage, QFont, QColor, QPalette, QIcon


# ─── CONFIG ───────────────────────────────────────────────────────────────────
API_BASE_URL = "http://localhost:8000"

ROUTERS = {
    "Frijol Negro": f"{API_BASE_URL}/v1/negro/process-image/",
    "Bayo":         f"{API_BASE_URL}/v1/bayo/process-image/",
    "Peruano":      f"{API_BASE_URL}/v1/peruano/process-image/",
}
ACTIVE_ROUTER = "Frijol Negro"
PROCESS_ENDPOINT = ROUTERS[ACTIVE_ROUTER]


# ─── HILO PARA PETICIÓN API (no bloquea la UI) ────────────────────────────────
class ImageWorker(QThread):
    # Modificado: ahora retorna (bytes_imagen, content_type, piedras_count)
    finished = pyqtSignal(bytes, str, int)  
    error    = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, file_path: str, endpoint: str):
        super().__init__()
        self.file_path = file_path
        self.endpoint = endpoint

    def run(self):
        try:
            self.progress.emit(30)
            file_name = os.path.basename(self.file_path)
            ext = os.path.splitext(file_name)[1].lower()
            mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                        ".png": "image/png", ".bmp": "image/bmp",
                        ".gif": "image/gif", ".webp": "image/webp"}
            mime = mime_map.get(ext, "image/png")

            with open(self.file_path, "rb") as f:
                files = {"file": (file_name, f, mime)}
                self.progress.emit(60)
                response = requests.post(self.endpoint, files=files, timeout=60)

            self.progress.emit(90)
            if response.status_code == 200:
                ct = response.headers.get("content-type", "image/png")
                try:
                    # AJUSTE AQUÍ: Leemos 'X-Piedras-Count' que envía tu backend de FastAPI
                    count = int(response.headers.get("X-Piedras-Count", -1))
                except (ValueError, TypeError):
                    count = -1
                self.finished.emit(response.content, ct, count)
            else:
                self.error.emit(f"Error {response.status_code}: {response.text[:200]}")
        except requests.exceptions.ConnectionError:
            self.error.emit("No se pudo conectar con el servidor.\nVerifica que FastAPI esté corriendo.")
        except Exception as e:
            self.error.emit(str(e))


# ─── PANEL DE IMAGEN ──────────────────────────────────────────────────────────
class ImagePanel(QFrame):
    """Panel con scroll que muestra una imagen centrada."""

    def __init__(self, placeholder_text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("imagePanel")
        self.setMinimumSize(280, 320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.img_label = QLabel(placeholder_text)
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setObjectName("imgPlaceholder")
        self.img_label.setWordWrap(True)
        self.img_label.setMinimumSize(260, 300)

        self.scroll.setWidget(self.img_label)
        layout.addWidget(self.scroll)

    def set_image_from_path(self, path: str):
        pix = QPixmap(path)
        self._display_pixmap(pix)

    def set_image_from_bytes(self, data: bytes):
        img = QImage()
        img.loadFromData(data)
        pix = QPixmap.fromImage(img)
        self._display_pixmap(pix)

    def _display_pixmap(self, pix: QPixmap):
        if pix.isNull():
            self.img_label.setText("No se pudo cargar la imagen.")
            return
        scaled = pix.scaled(
            self.img_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.img_label.setPixmap(scaled)

    def clear(self, text=""):
        self.img_label.setPixmap(QPixmap())
        self.img_label.setText(text)


# ─── VENTANA PRINCIPAL ────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Processor · Bean API")
        self.setMinimumSize(900, 600)
        self.resize(1080, 680)
        self._selected_path = None
        self._worker = None
        self._active_router = "Frijol Negro"
        self._router_btns = {}

        self._apply_stylesheet()
        self._build_ui()

    # ── ESTILOS ───────────────────────────────────────────────────────────────
    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow, QWidget#root {
                background-color: #1a1a2e;
            }
            /* BARRA SUPERIOR */
            QWidget#topBar {
                background-color: #16213e;
                border-bottom: 2px solid #e94560;
                min-height: 52px;
                max-height: 52px;
            }
            QLabel#appTitle {
                color: #eaeaea;
                font-size: 17px;
                font-weight: 700;
                letter-spacing: 1px;
                font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
            }
            QLabel#apiUrl {
                color: #e94560;
                font-size: 11px;
                font-family: 'Consolas', 'Menlo', monospace;
            }
            /* PANEL LATERAL */
            QWidget#sidePanel {
                background-color: #16213e;
                border-right: 1px solid #0f3460;
                min-width: 180px;
                max-width: 210px;
            }
            QLabel#sideTitle {
                color: #e94560;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 2px;
                font-family: 'Consolas', monospace;
                padding: 4px 0px;
            }
            QLabel#metaKey {
                color: #888;
                font-size: 10px;
                font-family: 'Consolas', monospace;
            }
            QLabel#metaVal {
                color: #eaeaea;
                font-size: 11px;
                font-family: 'Consolas', monospace;
                word-wrap: true;
            }
            /* PANELES DE IMAGEN */
            QFrame#imagePanel {
                background-color: #0f3460;
                border-radius: 10px;
                border: 1px solid #1e4a8a;
            }
            QLabel#imgPlaceholder {
                color: #aaa;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
            }
            /* ETIQUETAS DE PANEL */
            QLabel#panelLabel {
                color: #aaa;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 1px;
                font-family: 'Segoe UI', sans-serif;
                padding-bottom: 4px;
            }
            /* BOTONES */
            QPushButton#btnUpload {
                background-color: transparent;
                border: 2px solid #e94560;
                color: #e94560;
                border-radius: 7px;
                padding: 8px 18px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton#btnUpload:hover {
                background-color: #e9456015;
            }
            QPushButton#btnUpload:pressed {
                background-color: #e9456030;
            }
            QPushButton#btnProcess {
                background-color: #e94560;
                border: none;
                color: #fff;
                border-radius: 7px;
                padding: 10px 28px;
                font-size: 13px;
                font-weight: 700;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton#btnProcess:hover {
                background-color: #c73050;
            }
            QPushButton#btnProcess:pressed {
                background-color: #a02040;
            }
            QPushButton#btnProcess:disabled {
                background-color: #444;
                color: #777;
            }
            /* BEAN COUNT */
            QFrame#beanCountFrame {
                background-color: #0f3460;
                border-radius: 8px;
                border: 1px solid #1e4a8a;
            }
            QLabel#beanCountTitle {
                color: #888;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 2px;
                font-family: 'Consolas', monospace;
            }
            QLabel#beanCountValue {
                color: #e94560;
                font-size: 28px;
                font-weight: 700;
                font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
            }
            QLabel#beanCountUnit {
                color: #aaa;
                font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
            }
            /* ROUTER BUTTONS */
            QPushButton#btnRouter {
                background-color: transparent;
                border: 1px solid #1e4a8a;
                color: #888;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 600;
                font-family: 'Segoe UI', sans-serif;
                text-align: left;
            }
            QPushButton#btnRouter:hover {
                border-color: #e94560;
                color: #e94560;
            }
            QPushButton#btnRouterActive {
                background-color: #e9456018;
                border: 1px solid #e94560;
                color: #e94560;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 700;
                font-family: 'Segoe UI', sans-serif;
                text-align: left;
            }
            /* SAVE BUTTON */
            QPushButton#btnSave {
                background-color: transparent;
                border: 1px solid #555;
                color: #aaa;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton#btnSave:hover {
                border-color: #e94560;
                color: #e94560;
            }
            QPushButton#btnSave:disabled {
                color: #444;
                border-color: #333;
            }
            /* PROGRESS */
            QProgressBar {
                background-color: #0f3460;
                border: none;
                border-radius: 4px;
                height: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #e94560;
                border-radius: 4px;
            }
            /* STATUS BAR */
            QStatusBar {
                background-color: #16213e;
                color: #777;
                font-size: 11px;
                font-family: 'Consolas', monospace;
                border-top: 1px solid #0f3460;
            }
            QLabel#divider {
                background-color: #0f3460;
                max-height: 1px;
                min-height: 1px;
            }
        """)

    # ── CONSTRUCCIÓN DE LA UI ─────────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Barra superior ──
        main_layout.addWidget(self._build_top_bar())

        # ── Cuerpo ──
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_side_panel())
        body.addLayout(self._build_content_area(), stretch=1)
        main_layout.addLayout(body, stretch=1)

        # ── Status bar ──
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Listo · Selecciona una imagen para comenzar.")

    def _build_top_bar(self):
        bar = QWidget()
        bar.setObjectName("topBar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 0, 20, 0)

        title = QLabel("IMAGE PROCESSOR")
        title.setObjectName("appTitle")

        self.api_lbl = QLabel(f"→ {ROUTERS[self._active_router]}")
        self.api_lbl.setObjectName("apiUrl")

        lay.addWidget(title)
        lay.addStretch()
        lay.addWidget(self.api_lbl)
        return bar

    def _build_side_panel(self):
        panel = QWidget()
        panel.setObjectName("sidePanel")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(16, 20, 16, 20)
        lay.setSpacing(10)

        title = QLabel("METADATA")
        title.setObjectName("sideTitle")
        lay.addWidget(title)

        divider = QLabel()
        divider.setObjectName("divider")
        lay.addWidget(divider)

        # Campos de metadata
        self._meta_fields = {}
        fields = [
            ("Archivo",   "—"),
            ("Tipo",      "—"),
            ("Tamaño",    "—"),
            ("Estado",    "Sin imagen"),
        ]
        for key, val in fields:
            k_lbl = QLabel(key.upper())
            k_lbl.setObjectName("metaKey")
            v_lbl = QLabel(val)
            v_lbl.setObjectName("metaVal")
            v_lbl.setWordWrap(True)
            lay.addWidget(k_lbl)
            lay.addWidget(v_lbl)
            self._meta_fields[key] = v_lbl
            sp = QLabel()
            sp.setFixedHeight(6)
            lay.addWidget(sp)

        lay.addStretch()

        # ── Router buttons ──
        router_title = QLabel("ROUTER")
        router_title.setObjectName("sideTitle")
        lay.addWidget(router_title)

        router_divider = QLabel()
        router_divider.setObjectName("divider")
        lay.addWidget(router_divider)

        for name in ROUTERS:
            btn = QPushButton(f"● {name}")
            btn.setObjectName("btnRouterActive" if name == self._active_router else "btnRouter")
            btn.clicked.connect(lambda checked, n=name: self._switch_router(n))
            lay.addWidget(btn)
            self._router_btns[name] = btn

        lay.addSpacing(10)
        self.btn_save = QPushButton("Guardar resultado")
        self.btn_save.setObjectName("btnSave")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._save_result)
        lay.addWidget(self.btn_save)

        return panel

    def _build_content_area(self):
        lay = QVBoxLayout()
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(14)

        # ── Fila de imágenes ──
        panels_row = QHBoxLayout()
        panels_row.setSpacing(14)

        left_col = QVBoxLayout()
        lbl_orig = QLabel("IMAGEN ORIGINAL")
        lbl_orig.setObjectName("panelLabel")
        self.panel_original = ImagePanel("Sube una imagen\npara verla aquí")
        left_col.addWidget(lbl_orig)
        left_col.addWidget(self.panel_original, stretch=1)

        right_col = QVBoxLayout()
        lbl_res = QLabel("RESULTADO")
        lbl_res.setObjectName("panelLabel")
        self.panel_result = ImagePanel("El resultado\naparecerá aquí")
        right_col.addWidget(lbl_res)
        right_col.addWidget(self.panel_result, stretch=1)

        panels_row.addLayout(left_col)
        panels_row.addLayout(right_col)
        lay.addLayout(panels_row, stretch=1)

        # ── Fila de Contador (Modificado el título para que sea genérico a Piedras/Elementos) ──
        self.bean_count_frame = QFrame()
        self.bean_count_frame.setObjectName("beanCountFrame")
        self.bean_count_frame.setFixedHeight(64)
        bc_lay = QHBoxLayout(self.bean_count_frame)
        bc_lay.setContentsMargins(16, 8, 16, 8)
        bc_lay.setSpacing(10)

        bc_icon = QLabel("🪨")
        bc_icon.setFont(QFont("Segoe UI Emoji", 20))

        bc_text_col = QVBoxLayout()
        bc_text_col.setSpacing(0)
        # Cambiado a "PIEDRAS DETECTADAS"
        self.lbl_bean_title = QLabel("PIEDRAS DETECTADAS") 
        self.lbl_bean_title.setObjectName("beanCountTitle")
        self.lbl_bean_count = QLabel("—")
        self.lbl_bean_count.setObjectName("beanCountValue")
        bc_text_col.addWidget(self.lbl_bean_title)
        bc_text_col.addWidget(self.lbl_bean_count)

        self.lbl_bean_unit = QLabel("piedras extrañas encontradas")
        self.lbl_bean_unit.setObjectName("beanCountUnit")

        bc_lay.addWidget(bc_icon)
        bc_lay.addLayout(bc_text_col)
        bc_lay.addStretch()
        bc_lay.addWidget(self.lbl_bean_unit, alignment=Qt.AlignmentFlag.AlignBottom)

        # Mostrarlo inicialmente si está en Frijol Negro
        self.bean_count_frame.setVisible(self._active_router == "Frijol Negro")
        lay.addWidget(self.bean_count_frame)

        # ── Barra de progreso ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(5)
        lay.addWidget(self.progress_bar)

        # ── Botones de acción ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()

        self.btn_upload = QPushButton("📁  Seleccionar imagen")
        self.btn_upload.setObjectName("btnUpload")
        self.btn_upload.clicked.connect(self._select_image)

        self.btn_process = QPushButton("Procesar →")
        self.btn_process.setObjectName("btnProcess")
        self.btn_process.setEnabled(False)
        self.btn_process.clicked.connect(self._process_image)

        btn_row.addWidget(self.btn_upload)
        btn_row.addWidget(self.btn_process)
        lay.addLayout(btn_row)

        return lay

    # ── ROUTER SWITCHING ──────────────────────────────────────────────────────
    def _switch_router(self, name: str):
        self._active_router = name
        for n, btn in self._router_btns.items():
            btn.setObjectName("btnRouterActive" if n == name else "btnRouter")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.api_lbl.setText(f"→ {ROUTERS[name]}")
        self.status_bar.showMessage(f"Router activo: {name}  ({ROUTERS[name]})")
        
        # El contenedor se muestra para todos, pero limpiaremos el valor si cambias de router
        is_negro = name == "Frijol Negro"
        self.bean_count_frame.setVisible(is_negro)
        if not is_negro:
            self.lbl_bean_count.setText("—")

    # ── LÓGICA ────────────────────────────────────────────────────────────────
    def _select_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen", "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if not path:
            return

        self._selected_path = path
        self.panel_original.set_image_from_path(path)
        self.panel_result.clear("El resultado\naparecerá aquí")
        self.btn_process.setEnabled(True)
        self.btn_save.setEnabled(False)
        self._result_bytes = None
        self.lbl_bean_count.setText("—")

        # Metadata
        name = os.path.basename(path)
        ext  = os.path.splitext(name)[1].upper().lstrip(".")
        size = os.path.getsize(path)
        size_str = f"{size / 1024:.1f} KB" if size < 1_048_576 else f"{size / 1_048_576:.2f} MB"

        self._meta_fields["Archivo"].setText(name[:22] + ("…" if len(name) > 22 else ""))
        self._meta_fields["Tipo"].setText(ext or "DESCONOCIDO")
        self._meta_fields["Tamaño"].setText(size_str)
        self._meta_fields["Estado"].setText("Lista para procesar")
        self.status_bar.showMessage(f"Imagen seleccionada: {name}")

    def _process_image(self):
        if not self._selected_path:
            return

        self.btn_process.setEnabled(False)
        self.btn_upload.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._meta_fields["Estado"].setText("Procesando…")
        self.status_bar.showMessage("Enviando imagen a la API…")

        self._worker = ImageWorker(self._selected_path, ROUTERS[self._active_router])
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, value: int):
        self.progress_bar.setValue(value)

    def _on_finished(self, data: bytes, content_type: str, count: int):
        self._result_bytes = data
        self.progress_bar.setValue(100)
        self.panel_result.set_image_from_bytes(data)
        self._meta_fields["Estado"].setText("✓ Completado")
        self.status_bar.showMessage(f"Proceso completado · {len(data) / 1024:.1f} KB recibidos.")
        self.btn_save.setEnabled(True)
        
        # MODIFICADO: Desplegamos el total de piedras devuelto en la cabecera
        if self._active_router == "Frijol Negro":
            self.lbl_bean_count.setText(str(count) if count >= 0 else "N/D")
            
        self._reset_buttons()

    def _on_error(self, msg: str):
        self.panel_result.clear(f"⚠ Error:\n{msg}")
        self._meta_fields["Estado"].setText("Error")
        self.status_bar.showMessage(f"Error: {msg[:80]}")
        self.progress_bar.setValue(0)
        self._reset_buttons()

    def _reset_buttons(self):
        self.btn_process.setEnabled(True)
        self.btn_upload.setEnabled(True)
        self.progress_bar.setVisible(False)

    def _save_result(self):
        if not self._result_bytes:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar imagen resultado", "resultado.png",
            "PNG (*.png);;JPEG (*.jpg);;Todos los archivos (*)"
        )
        if path:
            try:
                with open(path, "wb") as f:
                    f.write(self._result_bytes)
                self.status_bar.showMessage(f"Guardado en: {path}")
            except Exception as e:
                self.status_bar.showMessage(f"No se pudo guardar: {e}")


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())