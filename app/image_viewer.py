"""图片查看器 — 支持缩放、旋转、开发者模式选区 OCR"""

from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QRect, QPoint, QEvent
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QBrush
from PIL import Image
import os


class RotateWorker(QThread):
    """后台线程：执行图片旋转和保存"""
    done = pyqtSignal(object, str)
    error = pyqtSignal(str)

    def __init__(self, pil_image: Image.Image, path: str, degrees: int):
        super().__init__()
        self._image = pil_image.copy()
        self._path = path
        self._degrees = degrees

    def run(self):
        try:
            if self._degrees == 90:
                rotated = self._image.transpose(Image.Transpose.ROTATE_90)
            elif self._degrees == -90:
                rotated = self._image.transpose(Image.Transpose.ROTATE_270)
            else:
                rotated = self._image.rotate(self._degrees, expand=True)
            rotated.save(self._path)
            self.done.emit(rotated, self._path)
        except Exception as e:
            self.error.emit(str(e))


class ImageViewer(QWidget):
    """图片显示组件，支持缩放、旋转、开发者模式选区 OCR"""

    image_rotated = pyqtSignal(str)
    region_ocr_result = pyqtSignal(str)  # OCR 识别结果

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path = None
        self._pil_image = None
        self._rotate_worker = None
        self._ocr_worker = None

        # 开发者模式选区状态
        self._developer_mode = False
        self._selecting = False
        self._sel_start = QPoint()
        self._sel_end = QPoint()
        self._sel_rect = QRect()  # widget 坐标的选区矩形
        self._display_rect = QRect()  # 图片在 label 中的实际显示区域
        self._scale = 1.0

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel("选择图片开始浏览")
        self._label.setObjectName("imageLabel")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setMinimumSize(400, 300)
        # 启用鼠标追踪以支持选区
        self._label.setMouseTracking(True)
        self._label.installEventFilter(self)

        layout.addWidget(self._label)

    # ── 开发者模式 ──────────────────────────────────────────

    def set_developer_mode(self, enabled: bool):
        self._developer_mode = enabled
        if not enabled:
            self._sel_rect = QRect()
            self._selecting = False
            self._label.update()

    # ── 图片加载 ────────────────────────────────────────────

    def load_image(self, path: str):
        if not path or not os.path.exists(path):
            return
        self._current_path = path
        try:
            self._pil_image = Image.open(path)
            self._pil_image.load()
            self._sel_rect = QRect()
            self._update_display()
        except Exception as e:
            self._label.setText(f"无法加载图片:\n{e}")

    def _update_display(self):
        if self._pil_image is None:
            return

        img = self._pil_image
        label_w, label_h = self._label.width(), self._label.height()

        # 预缩放
        if label_w > 50 and label_h > 50:
            max_w, max_h = label_w * 2, label_h * 2
            if img.width > max_w or img.height > max_h:
                thumb = img.copy()
                thumb.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                img = thumb

        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        if img.mode == "RGBA":
            data = img.tobytes("raw", "RGBA")
            fmt = QImage.Format.Format_RGBA8888
        else:
            data = img.tobytes("raw", "RGB")
            fmt = QImage.Format.Format_RGB888

        qimage = QImage(data, img.width, img.height, fmt)
        pixmap = QPixmap.fromImage(qimage)

        label_size = self._label.size()
        scaled = pixmap.scaled(
            label_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        self._label.setPixmap(scaled)

        # 计算图片在 label 中的实际显示区域（用于坐标映射）
        sw, sh = scaled.width(), scaled.height()
        ox = (label_w - sw) // 2
        oy = (label_h - sh) // 2
        self._display_rect = QRect(ox, oy, sw, sh)
        if sw > 0 and self._pil_image.width > 0:
            self._scale = self._pil_image.width / sw
        else:
            self._scale = 1.0

    # ── 鼠标事件（事件过滤器）─────────────────────────────

    def eventFilter(self, obj, event):
        if obj is not self._label or not self._developer_mode:
            return False

        etype = event.type()

        if etype == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            self._selecting = True
            self._sel_start = event.position().toPoint()
            self._sel_end = self._sel_start
            self._sel_rect = QRect(self._sel_start, self._sel_end)
            self._label.update()
            return True

        if etype == QEvent.Type.MouseMove and self._selecting:
            self._sel_end = event.position().toPoint()
            self._sel_rect = QRect(self._sel_start, self._sel_end).normalized()
            self._label.update()
            return True

        if etype == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            if self._selecting:
                self._selecting = False
                self._sel_end = event.position().toPoint()
                self._sel_rect = QRect(self._sel_start, self._sel_end).normalized()
                self._label.update()

                # 选区太小则忽略
                if self._sel_rect.width() > 5 and self._sel_rect.height() > 5:
                    self._start_ocr()
                return True

        return False

    # ── 选区绘制 ────────────────────────────────────────────

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._sel_rect.isNull() or not self._developer_mode:
            return

        painter = QPainter(self._label)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 半透明遮罩（选区外）
        painter.setBrush(QBrush(QColor(0, 0, 0, 80)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self._label.rect())

        # 清除选区内的遮罩（显示原始图片）
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.drawRect(self._sel_rect)

        # 选区边框
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setPen(QPen(QColor("#FF4081"), 2, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self._sel_rect)

        painter.end()

    # ── OCR 识别 ────────────────────────────────────────────

    def _start_ocr(self):
        """将 widget 选区映射到原图坐标，启动 OCR"""
        if self._pil_image is None:
            return
        if self._ocr_worker and self._ocr_worker.isRunning():
            return

        # widget 坐标 → 原图坐标
        img_x1 = int((self._sel_rect.left() - self._display_rect.x()) * self._scale)
        img_y1 = int((self._sel_rect.top() - self._display_rect.y()) * self._scale)
        img_x2 = int((self._sel_rect.right() - self._display_rect.x()) * self._scale)
        img_y2 = int((self._sel_rect.bottom() - self._display_rect.y()) * self._scale)

        from app.ocr_engine import OCRWorker
        self._ocr_worker = OCRWorker(self._pil_image, img_x1, img_y1, img_x2, img_y2)
        self._ocr_worker.done.connect(self._on_ocr_done)
        self._ocr_worker.error.connect(self._on_ocr_error)
        self._ocr_worker.start()

    def _on_ocr_done(self, text: str):
        self.region_ocr_result.emit(text)

    def _on_ocr_error(self, msg: str):
        self.region_ocr_result.emit(f"[识别失败] {msg}")

    # ── 旋转 ────────────────────────────────────────────────

    def rotate_left(self):
        if self._pil_image is None:
            return
        self._start_rotate(90)

    def rotate_right(self):
        if self._pil_image is None:
            return
        self._start_rotate(-90)

    def _start_rotate(self, degrees: int):
        if self._rotate_worker and self._rotate_worker.isRunning():
            return
        self._rotate_worker = RotateWorker(self._pil_image, self._current_path, degrees)
        self._rotate_worker.done.connect(self._on_rotate_done)
        self._rotate_worker.error.connect(self._on_rotate_error)
        self._rotate_worker.start()

    def _on_rotate_done(self, rotated_image, path):
        self._pil_image = rotated_image
        self._sel_rect = QRect()
        self._update_display()
        self.image_rotated.emit(path)

    def _on_rotate_error(self, msg):
        self._label.setText(f"旋转失败:\n{msg}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pil_image:
            self._update_display()

    def cleanup(self):
        if self._rotate_worker and self._rotate_worker.isRunning():
            self._rotate_worker.quit()
            self._rotate_worker.wait(2000)
        if self._ocr_worker and self._ocr_worker.isRunning():
            self._ocr_worker.quit()
            self._ocr_worker.wait(2000)
