from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QPushButton, QGroupBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget,
)
from PyQt6.QtCore import Qt, QSettings, QEvent
from PyQt6.QtGui import QKeyEvent


# ── 默认快捷键 ──────────────────────────────────────────────

DEFAULT_SHORTCUTS = {
    "apply_prefix": "Ctrl+A",
    "rename": "Ctrl+S",
    "prev_image": "Ctrl+Left",
    "next_image": "Ctrl+Right",
    "prev_prefix": "Up",
    "next_prefix": "Down",
    "rotate_left": "Ctrl+Q",
    "rotate_right": "Ctrl+E",
    "open_settings": "Ctrl+,",
}

ACTION_NAMES = {
    "apply_prefix": "应用惯用前缀",
    "rename": "确认重命名",
    "prev_image": "上一张图片",
    "next_image": "下一张图片",
    "prev_prefix": "上一个前缀",
    "next_prefix": "下一个前缀",
    "rotate_left": "向左旋转 90°",
    "rotate_right": "向右旋转 90°",
    "open_settings": "打开设置",
}


def get_shortcuts(settings: QSettings) -> dict:
    """从 QSettings 读取快捷键，未设置的用默认值"""
    result = {}
    for key, default in DEFAULT_SHORTCUTS.items():
        result[key] = settings.value(f"shortcut_{key}", default, type=str)
    return result


def event_to_str(event: QKeyEvent) -> str:
    """将 QKeyEvent 转为快捷键字符串，如 'Ctrl+A'"""
    parts = []
    mod = event.modifiers()
    if mod & Qt.KeyboardModifier.ControlModifier:
        parts.append("Ctrl")
    if mod & Qt.KeyboardModifier.AltModifier:
        parts.append("Alt")
    if mod & Qt.KeyboardModifier.ShiftModifier:
        parts.append("Shift")
    if mod & Qt.KeyboardModifier.MetaModifier:
        parts.append("Meta")

    key = event.key()
    # 跳过单独的修饰键
    if key in (Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Shift, Qt.Key.Key_Meta):
        return ""

    name = event.text().upper() if event.text() else ""
    if not name or not name.isprintable():
        name = _key_name(key)
    if name == "+":
        name = "Plus"
    elif name == "-":
        name = "Minus"
    parts.append(name)
    return "+".join(parts)


def _key_name(key: int) -> str:
    """Qt Key 枚举转可读名称"""
    mapping = {
        Qt.Key.Key_Left: "Left", Qt.Key.Key_Right: "Right",
        Qt.Key.Key_Up: "Up", Qt.Key.Key_Down: "Down",
        Qt.Key.Key_Return: "Return", Qt.Key.Key_Enter: "Return",
        Qt.Key.Key_Space: "Space", Qt.Key.Key_Tab: "Tab",
        Qt.Key.Key_Escape: "Escape", Qt.Key.Key_Delete: "Delete",
        Qt.Key.Key_Backspace: "Backspace",
    }
    return mapping.get(key, chr(key) if 32 <= key < 127 else "")


# ── 快捷键捕获按钮 ──────────────────────────────────────────

class ShortcutCaptureButton(QPushButton):
    """点击后进入捕获模式，等待用户按下新快捷键"""

    def __init__(self, key_sequence: str = "", parent=None):
        super().__init__(parent)
        self._key_sequence = key_sequence
        self._capturing = False
        self._update_text()
        self.clicked.connect(self._start_capture)

    def _update_text(self):
        self.setText(self._key_sequence if self._key_sequence else "未设置")

    def get_key_sequence(self) -> str:
        return self._key_sequence

    def _start_capture(self):
        self._capturing = True
        self.setText("请按下快捷键…")
        self.grabKeyboard()

    def keyPressEvent(self, event: QKeyEvent):
        if self._capturing:
            seq = event_to_str(event)
            if seq:
                self._key_sequence = seq
                self._capturing = False
                self.releaseKeyboard()
                self._update_text()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if not self._capturing:
            super().keyReleaseEvent(event)


# ── 设置对话框 ──────────────────────────────────────────────

class SettingsDialog(QDialog):

    SUFFIX_OPTIONS = {
        "-x": "-{x}", ".x": ".{x}", "_x": "_{x}",
        " (x)": " ({x})", "无后缀": None,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(460, 520)
        self._settings = QSettings("ImageTool", "ImageViewer")
        self._shortcut_buttons: dict[str, ShortcutCaptureButton] = {}
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ═══ 重名文件处理 ═══
        group1 = QGroupBox("重名文件自动处理")
        g1 = QVBoxLayout(group1)

        self._enable_check = QCheckBox("启用自动补全后缀")
        self._enable_check.setChecked(True)
        self._enable_check.stateChanged.connect(self._update_suffix_ui)
        g1.addWidget(self._enable_check)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("后缀格式："))
        self._suffix_combo = QComboBox()
        self._suffix_combo.addItems(list(self.SUFFIX_OPTIONS.keys()))
        row1.addWidget(self._suffix_combo, 1)
        g1.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("起始编号："))
        self._start_spin = QSpinBox()
        self._start_spin.setRange(0, 9999)
        self._start_spin.setValue(2)
        row2.addWidget(self._start_spin)
        row2.addStretch()
        g1.addLayout(row2)

        self._preview_label = QLabel("")
        self._preview_label.setObjectName("infoLabel")
        g1.addWidget(self._preview_label)

        self._suffix_combo.currentTextChanged.connect(self._update_preview)
        self._start_spin.valueChanged.connect(self._update_preview)

        layout.addWidget(group1)

        # ═══ 自定义快捷键 ═══
        group2 = QGroupBox("自定义快捷键")
        g2 = QVBoxLayout(group2)

        self._shortcut_table = QTableWidget(0, 2)
        self._shortcut_table.setHorizontalHeaderLabels(["功能", "快捷键"])
        self._shortcut_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._shortcut_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._shortcut_table.setColumnWidth(1, 140)
        self._shortcut_table.verticalHeader().setVisible(False)
        self._shortcut_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._shortcut_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._shortcut_table.setFixedHeight(len(ACTION_NAMES) * 34 + 30)
        g2.addWidget(self._shortcut_table)

        reset_row = QHBoxLayout()
        reset_row.addStretch()
        reset_btn = QPushButton("  恢复默认快捷键  ")
        reset_btn.setObjectName("rotateBtn")
        reset_btn.clicked.connect(self._reset_shortcuts)
        reset_row.addWidget(reset_btn)
        g2.addLayout(reset_row)

        layout.addWidget(group2, 1)

        # ═══ 按钮 ═══
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

    # ── 快捷键表格 ─────────────────────────────────────────

    def _build_shortcut_table(self, shortcuts: dict):
        self._shortcut_table.setRowCount(len(ACTION_NAMES))
        self._shortcut_buttons.clear()
        for row, (key, name) in enumerate(ACTION_NAMES.items()):
            # 功能名
            item = QTableWidgetItem(name)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self._shortcut_table.setItem(row, 0, item)
            # 快捷键捕获按钮
            btn = ShortcutCaptureButton(shortcuts.get(key, ""))
            self._shortcut_table.setCellWidget(row, 1, btn)
            self._shortcut_buttons[key] = btn

    def _reset_shortcuts(self):
        for key, btn in self._shortcut_buttons.items():
            btn._key_sequence = DEFAULT_SHORTCUTS[key]
            btn._update_text()

    # ── 重名设置 ────────────────────────────────────────────

    def _update_suffix_ui(self):
        enabled = self._enable_check.isChecked()
        self._suffix_combo.setEnabled(enabled)
        self._start_spin.setEnabled(enabled)
        self._update_preview()

    def _update_preview(self):
        if not self._enable_check.isChecked():
            self._preview_label.setText("未启用：重名时弹窗确认覆盖")
            return
        fmt = self.SUFFIX_OPTIONS[self._suffix_combo.currentText()]
        start = self._start_spin.value()
        if fmt is None:
            self._preview_label.setText("示例：a1（不添加后缀，直接覆盖）")
        else:
            s2 = fmt.replace("{x}", str(start))
            s3 = fmt.replace("{x}", str(start + 1))
            self._preview_label.setText(f"示例：a1 → a1{s2} → a1{s3}")

    # ── 加载 / 保存 ─────────────────────────────────────────

    def _load_settings(self):
        # 重名
        self._enable_check.setChecked(
            self._settings.value("auto_suffix_enabled", True, type=bool))
        suffix_key = self._settings.value("suffix_key", "-x", type=str)
        idx = list(self.SUFFIX_OPTIONS.keys()).index(suffix_key) if suffix_key in self.SUFFIX_OPTIONS else 0
        self._suffix_combo.setCurrentIndex(idx)
        self._start_spin.setValue(
            self._settings.value("start_num", 2, type=int))
        self._update_suffix_ui()

        # 快捷键
        shortcuts = get_shortcuts(self._settings)
        self._build_shortcut_table(shortcuts)

    def _save_and_close(self):
        # 重名
        self._settings.setValue("auto_suffix_enabled", self._enable_check.isChecked())
        self._settings.setValue("suffix_key", self._suffix_combo.currentText())
        self._settings.setValue("start_num", self._start_spin.value())
        # 快捷键
        for key, btn in self._shortcut_buttons.items():
            self._settings.setValue(f"shortcut_{key}", btn.get_key_sequence())
        self.accept()
