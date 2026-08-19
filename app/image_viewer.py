from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QPainter
from PIL import Image
from io import BytesIO
import os


class ImageViewer(QWidget):
    """图片显示组件，支持缩放和旋转"""

    image_rotated = pyqtSignal(str)  # 旋转后发出信号，传递新文件路径

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path = None
        self._pil_image = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel("选择图片开始浏览")
        self._label.setObjectName("imageLabel")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setMinimumSize(400, 300)

        layout.addWidget(self._label)

    def load_image(self, path: str):
        """加载并显示图片"""
        if not path or not os.path.exists(path):
            return

        self._current_path = path
        try:
            with Image.open(path) as img:
                buf = BytesIO()
                img.save(buf, format=img.format or "JPEG")
                buf.seek(0)
                self._pil_image = Image.open(buf)
                self._pil_image.load()
            self._update_display()
        except Exception as e:
            self._label.setText(f"无法加载图片:\n{e}")

    def _update_display(self):
        """根据当前PIL图片更新显示"""
        if self._pil_image is None:
            return

        # PIL -> QPixmap
        if self._pil_image.mode == "RGBA":
            data = self._pil_image.tobytes("raw", "RGBA")
            qimage = QImage(
                data,
                self._pil_image.width,
                self._pil_image.height,
                QImage.Format.Format_RGBA8888,
            )
        else:
            rgb = self._pil_image.convert("RGB")
            data = rgb.tobytes("raw", "RGB")
            qimage = QImage(
                data,
                rgb.width,
                rgb.height,
                QImage.Format.Format_RGB888,
            )

        pixmap = QPixmap.fromImage(qimage)

        # 缩放以适应显示区域
        label_size = self._label.size()
        scaled = pixmap.scaled(
            label_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._label.setPixmap(scaled)

    def rotate_left(self):
        """向左旋转90度并保存"""
        if self._pil_image is None:
            return
        self._pil_image = self._pil_image.rotate(90, expand=True)
        self._save_and_update()

    def rotate_right(self):
        """向右旋转90度并保存"""
        if self._pil_image is None:
            return
        self._pil_image = self._pil_image.rotate(-90, expand=True)
        self._save_and_update()

    def _save_and_update(self):
        """保存当前图片到文件并刷新显示"""
        if self._current_path and self._pil_image:
            self._pil_image.save(self._current_path)
            self._update_display()
            self.image_rotated.emit(self._current_path)

    def resizeEvent(self, event):
        """窗口大小改变时重新缩放图片"""
        super().resizeEvent(event)
        if self._pil_image:
            self._update_display()
