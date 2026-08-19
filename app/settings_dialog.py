from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QPushButton, QGroupBox,
)
from PyQt6.QtCore import QSettings


class SettingsDialog(QDialog):
    """重名文件处理设置"""

    SUFFIX_OPTIONS = {
        "-x": "-{x}",
        ".x": ".{x}",
        "_x": "_{x}",
        " (x)": " ({x})",
        "无后缀": None,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置 — 重名文件处理")
        self.setMinimumWidth(380)
        self._settings = QSettings("ImageTool", "ImageViewer")
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        group = QGroupBox("重名文件自动处理")
        group_layout = QVBoxLayout(group)

        # 后缀格式
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("重名后缀格式："))
        self._suffix_combo = QComboBox()
        self._suffix_combo.addItems(list(self.SUFFIX_OPTIONS.keys()))
        row1.addWidget(self._suffix_combo, 1)
        group_layout.addLayout(row1)

        # 起始编号
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("起始编号："))
        self._start_spin = QSpinBox()
        self._start_spin.setRange(0, 9999)
        self._start_spin.setValue(2)
        row2.addWidget(self._start_spin)
        row2.addStretch()
        group_layout.addLayout(row2)

        # 预览
        self._preview_label = QLabel("")
        self._preview_label.setObjectName("infoLabel")
        group_layout.addWidget(self._preview_label)

        self._suffix_combo.currentTextChanged.connect(self._update_preview)
        self._start_spin.valueChanged.connect(self._update_preview)

        layout.addWidget(group)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("  取消  ")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("  保存  ")
        save_btn.setObjectName("confirmBtn")
        save_btn.clicked.connect(self._save_and_close)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        self._update_preview()

    def _update_preview(self):
        fmt_key = self._suffix_combo.currentText()
        start = self._start_spin.value()
        fmt = self.SUFFIX_OPTIONS[fmt_key]
        if fmt is None:
            self._preview_label.setText("示例：a1（不添加后缀，直接覆盖）")
        else:
            s2 = fmt.replace("{x}", str(start))
            s3 = fmt.replace("{x}", str(start + 1))
            self._preview_label.setText(f"示例：a1 → a1{s2} → a1{s3}")

    def _load_settings(self):
        suffix_key = self._settings.value("suffix_key", "-x", type=str)
        start_num = self._settings.value("start_num", 2, type=int)
        idx = list(self.SUFFIX_OPTIONS.keys()).index(suffix_key) if suffix_key in self.SUFFIX_OPTIONS else 0
        self._suffix_combo.setCurrentIndex(idx)
        self._start_spin.setValue(start_num)

    def _save_and_close(self):
        self._settings.setValue("suffix_key", self._suffix_combo.currentText())
        self._settings.setValue("start_num", self._start_spin.value())
        self.accept()

    def get_suffix_format(self) -> str | None:
        """返回后缀格式字符串，如 '-{x}'，或 None 表示不添加后缀"""
        key = self._suffix_combo.currentText()
        return self.SUFFIX_OPTIONS[key]

    def get_start_number(self) -> int:
        return self._start_spin.value()
