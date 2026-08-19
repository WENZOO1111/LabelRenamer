from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QPushButton, QGroupBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QWidget, QColorDialog, QMessageBox,
)
from PyQt6.QtCore import Qt, QSettings, QEvent
from PyQt6.QtGui import QKeyEvent, QColor


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

# ── 颜色元素定义 ──────────────────────────────────────────────

COLOR_ELEMENTS = [
    ("bg",         "背景颜色"),
    ("text",       "文字颜色"),
    ("card",       "卡片/列表背景"),
    ("input_bg",   "输入框背景"),
    ("input_border", "输入框边框"),
    ("btn_bg",     "按钮背景"),
    ("btn_text",   "按钮文字"),
    ("accent",     "强调色/主题色"),
    ("accent_text", "强调色上的文字"),
    ("nav_bg",     "导航按钮背景"),
    ("nav_border", "导航按钮边框"),
    ("nav_text",   "导航按钮文字"),
    ("hover",      "悬停高亮"),
    ("status_bg",  "状态栏背景"),
    ("status_text", "状态栏文字"),
]


def get_shortcuts(settings: QSettings) -> dict:
    result = {}
    for key, default in DEFAULT_SHORTCUTS.items():
        result[key] = settings.value(f"shortcut_{key}", default, type=str)
    return result


def event_to_str(event: QKeyEvent) -> str:
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


# ── 颜色选择按钮 ────────────────────────────────────────────

class ColorButton(QPushButton):
    """显示当前颜色的可点击按钮"""
    def __init__(self, color: str = "#FFFFFF", parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(40, 28)
        self._update_style()
        self.clicked.connect(self._pick_color)

    def _update_style(self):
        self.setStyleSheet(
            f"background-color: {self._color}; border: 2px solid #888; border-radius: 4px;")

    def get_color(self) -> str:
        return self._color

    def set_color(self, color: str):
        self._color = color
        self._update_style()

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._color), self, "选择颜色")
        if c.isValid():
            self._color = c.name()
            self._update_style()


# ── 颜色预览面板 ────────────────────────────────────────────

class ColorPreview(QWidget):
    """模拟界面布局的颜色预览，点击元素可编辑对应颜色"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(260)
        self._elements = {}  # key -> (rect_label, color_btn)
        self._selected = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("点击下方色块编辑对应区域颜色")
        title.setObjectName("infoLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 预览区
        self._preview = QLabel()
        self._preview.setMinimumHeight(120)
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._preview)

        # 色块网格
        grid = QHBoxLayout()
        grid.setSpacing(6)
        for key, name in COLOR_ELEMENTS:
            col = QVBoxLayout()
            col.setSpacing(2)
            btn = ColorButton()
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 10px;")
            col.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            col.addWidget(lbl)
            grid.addLayout(col)
            self._elements[key] = (lbl, btn)
        layout.addLayout(grid)

    def load_colors(self, colors: dict):
        for key, (_, btn) in self._elements.items():
            btn.set_color(colors.get(key, "#FFFFFF"))
        self._update_preview()

    def get_colors(self) -> dict:
        return {key: btn.get_color() for key, (_, btn) in self._elements.items()}

    def _update_preview(self):
        c = self.get_colors()
        self._preview.setStyleSheet(
            f"background-color: {c.get('bg', '#B4C8D8')}; "
            f"border: 2px solid {c.get('input_border', '#6E9EAE')}; "
            f"border-radius: 8px;")
        self._preview.setText(
            f"<span style='color:{c.get('text', '#000')};font-size:13px;'>"
            f"预览区域 — 背景: {c.get('bg','')}  文字: {c.get('text','')}</span>")


# ── 主设置对话框 ────────────────────────────────────────────

class SettingsDialog(QDialog):

    SUFFIX_OPTIONS = {
        "-x": "-{x}", ".x": ".{x}", "_x": "_{x}",
        " (x)": " ({x})", "无后缀": None,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(520, 560)
        self._settings = QSettings("ImageTool", "ImageViewer")
        self._shortcut_buttons: dict[str, ShortcutCaptureButton] = {}
        self._setup_ui()
        self._load_all()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        tabs = QTabWidget()
        tabs.addTab(self._build_duplicate_tab(), "重名文件处理")
        tabs.addTab(self._build_shortcut_tab(), "快捷键设置")
        tabs.addTab(self._build_color_tab(), "颜色设计")
        layout.addWidget(tabs, 1)

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

    # ═══════════════════════════════════════════════════════
    # 标签页1：重名文件处理
    # ═══════════════════════════════════════════════════════

    def _build_duplicate_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        self._enable_check = QCheckBox("启用自动补全后缀")
        self._enable_check.setChecked(True)
        self._enable_check.stateChanged.connect(self._update_suffix_ui)
        layout.addWidget(self._enable_check)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("后缀格式："))
        self._suffix_combo = QComboBox()
        self._suffix_combo.addItems(list(self.SUFFIX_OPTIONS.keys()))
        row1.addWidget(self._suffix_combo, 1)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("起始编号："))
        self._start_spin = QSpinBox()
        self._start_spin.setRange(0, 9999)
        self._start_spin.setValue(2)
        row2.addWidget(self._start_spin)
        row2.addStretch()
        layout.addLayout(row2)

        self._preview_label = QLabel("")
        self._preview_label.setObjectName("infoLabel")
        layout.addWidget(self._preview_label)

        self._suffix_combo.currentTextChanged.connect(self._update_preview)
        self._start_spin.valueChanged.connect(self._update_preview)

        layout.addStretch()
        return w

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

    # ═══════════════════════════════════════════════════════
    # 标签页2：快捷键设置
    # ═══════════════════════════════════════════════════════

    def _build_shortcut_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        self._shortcut_table = QTableWidget(0, 2)
        self._shortcut_table.setHorizontalHeaderLabels(["功能", "快捷键"])
        self._shortcut_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        self._shortcut_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed)
        self._shortcut_table.setColumnWidth(1, 150)
        self._shortcut_table.verticalHeader().setVisible(False)
        self._shortcut_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._shortcut_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._shortcut_table, 1)

        reset_row = QHBoxLayout()
        reset_row.addStretch()
        reset_btn = QPushButton("  恢复默认快捷键  ")
        reset_btn.setObjectName("rotateBtn")
        reset_btn.clicked.connect(self._reset_shortcuts)
        reset_row.addWidget(reset_btn)
        layout.addLayout(reset_row)

        return w

    def _build_shortcut_table(self, shortcuts: dict):
        self._shortcut_table.setRowCount(len(ACTION_NAMES))
        self._shortcut_buttons.clear()
        for row, (key, name) in enumerate(ACTION_NAMES.items()):
            item = QTableWidgetItem(name)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self._shortcut_table.setItem(row, 0, item)
            btn = ShortcutCaptureButton(shortcuts.get(key, ""))
            self._shortcut_table.setCellWidget(row, 1, btn)
            self._shortcut_buttons[key] = btn

    def _reset_shortcuts(self):
        for key, btn in self._shortcut_buttons.items():
            btn._key_sequence = DEFAULT_SHORTCUTS[key]
            btn._update_text()

    # ═══════════════════════════════════════════════════════
    # 标签页3：颜色设计
    # ═══════════════════════════════════════════════════════

    def _build_color_tab(self) -> QWidget:
        from app.styles import LIGHT_COLORS, DARK_COLORS

        w = QWidget()
        layout = QVBoxLayout(w)

        # 模式切换
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("主题模式："))
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["明亮模式", "暗黑模式"])
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self._mode_combo)
        mode_row.addStretch()

        reset_color_btn = QPushButton("  恢复默认颜色  ")
        reset_color_btn.setObjectName("rotateBtn")
        reset_color_btn.clicked.connect(self._reset_colors)
        mode_row.addWidget(reset_color_btn)
        layout.addLayout(mode_row)

        # 预览面板
        self._color_preview = ColorPreview()
        layout.addWidget(self._color_preview, 1)

        return w

    def _on_mode_changed(self, index: int):
        from app.styles import LIGHT_COLORS, DARK_COLORS
        mode = "light" if index == 0 else "dark"
        defaults = LIGHT_COLORS if mode == "light" else DARK_COLORS
        self._color_preview.load_colors(defaults)

    def _reset_colors(self):
        from app.styles import LIGHT_COLORS, DARK_COLORS
        mode = "light" if self._mode_combo.currentIndex() == 0 else "dark"
        defaults = LIGHT_COLORS if mode == "light" else DARK_COLORS
        self._color_preview.load_colors(defaults)

    # ═══════════════════════════════════════════════════════
    # 加载 / 保存
    # ═══════════════════════════════════════════════════════

    def _load_all(self):
        # 重名
        self._enable_check.setChecked(
            self._settings.value("auto_suffix_enabled", True, type=bool))
        suffix_key = self._settings.value("suffix_key", "-x", type=str)
        idx = list(self.SUFFIX_OPTIONS.keys()).index(
            suffix_key) if suffix_key in self.SUFFIX_OPTIONS else 0
        self._suffix_combo.setCurrentIndex(idx)
        self._start_spin.setValue(
            self._settings.value("start_num", 2, type=int))
        self._update_suffix_ui()

        # 快捷键
        self._build_shortcut_table(get_shortcuts(self._settings))

        # 颜色
        from app.styles import LIGHT_COLORS, DARK_COLORS
        mode = self._settings.value("theme_mode", "light", type=str)
        self._mode_combo.setCurrentIndex(0 if mode == "light" else 1)
        colors = {}
        defaults = LIGHT_COLORS if mode == "light" else DARK_COLORS
        for key in defaults:
            colors[key] = self._settings.value(
                f"color_{key}", defaults[key], type=str)
        self._color_preview.load_colors(colors)

    def _save_and_close(self):
        # 重名
        self._settings.setValue("auto_suffix_enabled",
                                self._enable_check.isChecked())
        self._settings.setValue("suffix_key",
                                self._suffix_combo.currentText())
        self._settings.setValue("start_num", self._start_spin.value())
        # 快捷键
        for key, btn in self._shortcut_buttons.items():
            self._settings.setValue(f"shortcut_{key}",
                                    btn.get_key_sequence())
        # 颜色
        mode = "light" if self._mode_combo.currentIndex() == 0 else "dark"
        self._settings.setValue("theme_mode", mode)
        for key, color in self._color_preview.get_colors().items():
            self._settings.setValue(f"color_{key}", color)
        self.accept()
