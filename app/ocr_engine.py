"""EasyOCR 封装，提供单例 OCR 引擎和后台线程"""

from PyQt6.QtCore import QThread, pyqtSignal


class OCREngine:
    """EasyOCR 单例封装，惰性加载识别模型"""

    _instance = None

    def __new__(cls, languages=None):
        if cls._instance is None:
            obj = super().__new__(cls)
            obj._reader = None
            obj._languages = languages or ["ch_sim", "en"]
            cls._instance = obj
        return cls._instance

    def _ensure_reader(self):
        if self._reader is None:
            import easyocr
            self._reader = easyocr.Reader(self._languages, gpu=False)

    def recognize(self, pil_image) -> str:
        """识别整张图片中的文字"""
        self._ensure_reader()
        import numpy as np
        img_array = np.array(pil_image.convert("RGB"))
        results = self._reader.readtext(img_array)
        texts = [text for _, text, conf in results if conf > 0.3]
        return " ".join(texts).strip()

    def recognize_region(self, pil_image, x1, y1, x2, y2) -> str:
        """识别指定区域的文字"""
        self._ensure_reader()
        import numpy as np
        # 裁剪区域
        w, h = pil_image.size
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            return ""
        region = pil_image.crop((x1, y1, x2, y2))
        img_array = np.array(region.convert("RGB"))
        results = self._reader.readtext(img_array)
        texts = [text for _, text, conf in results if conf > 0.3]
        return "".join(texts).strip()


class OCRWorker(QThread):
    """后台线程执行 OCR，避免阻塞 UI"""
    done = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, pil_image, x1=None, y1=None, x2=None, y2=None, parent=None):
        super().__init__(parent)
        self._pil_image = pil_image
        self._x1 = x1
        self._y1 = y1
        self._x2 = x2
        self._y2 = y2

    def run(self):
        try:
            engine = OCREngine()
            if self._x1 is not None:
                text = engine.recognize_region(
                    self._pil_image, self._x1, self._y1, self._x2, self._y2)
            else:
                text = engine.recognize(self._pil_image)
            self.done.emit(text)
        except Exception as e:
            self.error.emit(str(e))
