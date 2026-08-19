from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image
from io import BytesIO
import os


class RotateWorker(QThread):
    """后台线程：执行图片旋转和保存"""
    done = pyqtSignal(object, str)  # (旋转后的PIL.Image, 文件路径)
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
    """图片显示组件，支持缩放和旋转"""

    image_rotated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path = None
        self._pil_image = None
        self._rotate_worker = None
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

        # 直接从 PIL 原始像素构建 QImage，跳过额外的 convert 步骤
        img = self._pil_image
        if img.mode == "RGBA":
            data = img.tobytes("raw", "RGBA")
            fmt = QImage.Format.Format_RGBA8888
        else:
            if img.mode != "RGB":
                img = img.convert("RGB")
            data = img.tobytes("raw", "RGB")
            fmt = QImage.Format.Format_RGB888

        qimage = QImage(data, img.width, img.height, fmt)
        pixmap = QPixmap.fromImage(qimage)

        label_size = self._label.size()
        scaled = pixmap.scaled(
            label_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._label.setPixmap(scaled)

    def rotate_left(self):
        """向左旋转90度（后台线程执行）"""
        if self._pil_image is None:
            return
        self._start_rotate(90)

    def rotate_right(self):
        """向右旋转90度（后台线程执行）"""
        if self._pil_image is None:
            return
        self._start_rotate(-90)

    def _start_rotate(self, degrees: int):
        """启动后台旋转线程"""
        # 如果上一次旋转还没完成，忽略本次请求
        if self._rotate_worker and self._rotate_worker.isRunning():
            return
        self._rotate_worker = RotateWorker(self._pil_image, self._current_path, degrees)
        self._rotate_worker.done.connect(self._on_rotate_done)
        self._rotate_worker.error.connect(self._on_rotate_error)
        self._rotate_worker.start()

    def _on_rotate_done(self, rotated_image, path):
        """旋转完成后更新显示"""
        self._pil_image = rotated_image
        self._update_display()
        self.image_rotated.emit(path)

    def _on_rotate_error(self, msg):
        """旋转失败"""
        self._label.setText(f"旋转失败:\n{msg}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pil_image:
            self._update_display()

    def cleanup(self):
        """清理后台线程"""
        if self._rotate_worker and self._rotate_worker.isRunning():
            self._rotate_worker.quit()
            self._rotate_worker.wait(2000)
