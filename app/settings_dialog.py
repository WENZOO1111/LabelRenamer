from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QPushButton, QGroupBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QWidget, QColorDialog, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, QSettings, QRect, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QColor, QPainter, QPen, QFont, QBrush


# ── 默认快捷键 ──────────────────────────────────────────────

DEFAULT_SHORTCUTS = {
    "apply_prefix": "Ctrl+A", "rename": "Ctrl+S",
    "prev_image": "Ctrl+Left", "next_image": "Ctrl+Right",
    "prev_prefix": "Up", "next_prefix": "Down",
    "rotate_left": "Ctrl+Q", "rotate_right": "Ctrl+E",
    "open_settings": "Ctrl+,",
}

ACTION_NAMES = {
    "apply_prefix": "应用惯用前缀", "rename": "确认重命名",
    "prev_image": "上一张图片", "next_image": "下一张图片",
    "prev_prefix": "上一个前缀", "next_prefix": "下一个前缀",
    "rotate_left": "向左旋转 90°", "rotate_right": "向右旋转 90°",
    "open_settings": "打开设置",
}

COLOR_ELEMENTS = [
    ("bg", "背景"), ("text", "文字"), ("card", "卡片/列表"),
    ("input_bg", "输入框背景"), ("input_border", "输入框边框"),
    ("btn_bg", "按钮背景"), ("btn_text", "按钮文字"),
    ("accent", "强调色"), ("accent_text", "强调色文字"),
    ("nav_bg", "导航按钮背景"), ("nav_border", "导航按钮边框"),
    ("nav_text", "导航按钮文字"), ("hover", "悬停高亮"),
    ("status_bg", "状态栏背景"), ("status_text", "状态栏文字"),
]


def get_shortcuts(settings: QSettings) -> dict:
    return {k: settings.value(f"shortcut_{k}", v, type=str)
            for k, v in DEFAULT_SHORTCUTS.items()}


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
    if key in (Qt.Key.Key_Control, Qt.Key.Key_Alt,
               Qt.Key.Key_Shift, Qt.Key.Key_Meta):
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
    m = {
        Qt.Key.Key_Left: "Left", Qt.Key.Key_Right: "Right",
        Qt.Key.Key_Up: "Up", Qt.Key.Key_Down: "Down",
        Qt.Key.Key_Return: "Return", Qt.Key.Key_Enter: "Return",
        Qt.Key.Key_Space: "Space", Qt.Key.Key_Tab: "Tab",
        Qt.Key.Key_Escape: "Escape", Qt.Key.Key_Delete: "Delete",
        Qt.Key.Key_Backspace: "Backspace",
    }
    return m.get(key, chr(key) if 32 <= key < 127 else "")


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


# ── 交互式颜色预览面板 ──────────────────────────────────────

class ColorPreview(QWidget):
    """模拟应用界面的缩略预览，点击组件选中后可修改颜色。
    支持 Shift+点击 多选。"""

    selection_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(480, 300)
        self.setMouseTracking(True)
        self._colors: dict[str, str] = {}
        self._selected: set[str] = set()
        self._hover: str = ""
        self._rects: dict[str, QRect] = {}
        self._labels = dict(COLOR_ELEMENTS)

    def load_colors(self, colors: dict):
        self._colors = dict(colors)
        self._selected.clear()
        self._hover = ""
        self.update()

    def get_colors(self) -> dict:
        return dict(self._colors)

    def get_selected(self) -> set:
        return set(self._selected)

    # ── 布局计算 ────────────────────────────────────────────

    def _calc_rects(self):
        w, h = self.width(), self.height()
        m = 6  # 外边距
        lp_w = int(w * 0.24)  # 左面板宽度
        gap = 5

        self._rects["bg"] = QRect(0, 0, w, h)

        # 左面板
        lx = m
        ly = m
        lw = lp_w - m
        lh = h - 2 * m
        self._rects["card"] = QRect(lx, ly, lw, lh)

        # 目录行
        drh = 26
        self._rects["input_bg"] = QRect(lx + 3, ly + 3, lw - 6, drh)
        # 目录按钮（nav样式）
        btn_w = 52
        self._rects["nav_bg"] = QRect(
            lx + lw - btn_w - 3, ly + 3, btn_w, drh)

        # 文件列表
        fl_top = ly + drh + gap + 20
        fl_h = max(30, lh - drh - 60 - gap * 2 - 20)
        self._rects["hover"] = QRect(lx + 3, fl_top, lw - 6, fl_h)

        # 前缀标题
        pt_top = fl_top + fl_h + gap
        # 前缀输入行
        pi_top = pt_top + 16
        self._rects["btn_bg"] = QRect(lx + 3, pi_top, lw - 6, 22)
        # +按钮
        self._rects["accent"] = QRect(lx + lw - 18, pi_top, 15, 22)

        # 右面板
        rx = lp_w + gap
        rw = w - lp_w - gap - m

        # 文件名标签
        self._rects["status_bg"] = QRect(rx, m, rw, 22)

        # 图片区域
        iv_top = m + 22 + gap
        iv_h = max(40, h - 22 - 26 - 26 - 26 - m * 2 - gap * 4)
        self._rects["text"] = QRect(rx, iv_top, rw, iv_h)

        # 旋转按钮行
        rb_top = iv_top + iv_h + gap
        rb_w = min(90, rw // 2 - gap)
        rb_h = 22
        self._rects["rotate_left"] = QRect(
            rx + rw // 2 - rb_w - gap // 2, rb_top, rb_w, rb_h)
        self._rects["rotate_right"] = QRect(
            rx + rw // 2 + gap // 2, rb_top, rb_w, rb_h)

        # 重命名行
        rn_top = rb_top + rb_h + gap
        self._rects["input_border"] = QRect(rx, rn_top, rw - 60, 22)
        self._rects["btn_text"] = QRect(rx + rw - 56, rn_top, 56, 22)

        # 导航行
        nv_top = rn_top + 22 + gap
        nb_w = min(60, rw // 3 - gap)
        self._rects["nav_border"] = QRect(rx, nv_top, nb_w, 22)
        self._rects["nav_text"] = QRect(
            rx + rw - nb_w, nv_top, nb_w, 22)

    # ── 鼠标事件 ────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._calc_rects()
        key = self._hit_test(event.position().toPoint())
        if not key:
            return
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            if key in self._selected:
                self._selected.discard(key)
            else:
                self._selected.add(key)
        else:
            self._selected = {key}
        self.update()
        self.selection_changed.emit()

    def mouseMoveEvent(self, event):
        self._calc_rects()
        key = self._hit_test(event.position().toPoint())
        if key != self._hover:
            self._hover = key
            self.update()

    def leaveEvent(self, event):
        if self._hover:
            self._hover = ""
            self.update()

    def _hit_test(self, pos) -> str:
        """从最顶层组件向下匹配"""
        order = [
            "rotate_left", "rotate_right",
            "btn_text", "nav_text", "nav_border",
            "accent", "btn_bg", "nav_bg",
            "input_bg", "input_border", "hover",
            "status_bg", "text", "card", "bg",
        ]
        for key in order:
            if key in self._rects and self._rects[key].contains(pos):
                return key
        return ""

    # ── 绘制 ────────────────────────────────────────────────

    def paintEvent(self, event):
        self._calc_rects()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        c = self._colors

        # 背景
        painter.fillRect(0, 0, w, h, QColor(c.get("bg", "#B4C8D8")))

        r = self._rects

        # ── 左面板 ──
        if "card" in r:
            painter.fillRect(r["card"], QColor(c.get("card", "#FFF")))
            painter.setPen(QPen(QColor(c.get("input_border", "#999")), 1))
            painter.drawRoundedRect(r["card"], 5, 5)

        # 目录输入框
        if "input_bg" in r:
            painter.fillRect(r["input_bg"], QColor(c.get("input_bg", "#FFF")))
            painter.setPen(QPen(QColor(c.get("input_border", "#999")), 1))
            painter.drawRoundedRect(r["input_bg"], 3, 3)
            painter.setPen(QColor(c.get("status_text", "#999")))
            painter.setFont(QFont("Microsoft YaHei", 7))
            painter.drawText(r["input_bg"].adjusted(4, 0, -4, 0),
                             Qt.AlignmentFlag.AlignVCenter, "选择目录")

        # 目录按钮
        if "nav_bg" in r:
            painter.fillRect(r["nav_bg"], QColor(c.get("nav_bg", "#FFF")))
            painter.setPen(QPen(QColor(c.get("nav_border", "#999")), 1))
            painter.drawRoundedRect(r["nav_bg"], 3, 3)
            painter.setPen(QColor(c.get("nav_text", "#36A")))
            painter.setFont(QFont("Microsoft YaHei", 7))
            painter.drawText(r["nav_bg"], Qt.AlignmentFlag.AlignCenter,
                             "选择目录")

        # "文件列表"标题
        fl = r.get("hover")
        if fl:
            painter.setPen(QColor(c.get("status_text", "#999")))
            painter.setFont(QFont("Microsoft YaHei", 7))
            painter.drawText(fl.adjusted(0, -16, 0, 0),
                             Qt.AlignmentFlag.AlignLeft, "文件列表")

        # 文件列表区
        if "hover" in r:
            painter.fillRect(r["hover"], QColor(c.get("hover", "#E8E8E8")))
            painter.setPen(QPen(QColor(c.get("input_border", "#999")), 1))
            painter.drawRoundedRect(r["hover"], 3, 3)
            painter.setPen(QColor(c.get("text", "#000")))
            painter.setFont(QFont("Microsoft YaHei", 7))
            for i in range(min(5, r["hover"].height() // 14)):
                y = r["hover"].top() + 4 + i * 14
                painter.drawText(r["hover"].adjusted(6, 0, -6, 0),
                                 Qt.AlignmentFlag.AlignTop,
                                 f"IMG_{4567 + i:04d}.jpg")

        # 前缀标题
        pt = r.get("btn_bg")
        if pt:
            painter.setPen(QColor(c.get("status_text", "#999")))
            painter.setFont(QFont("Microsoft YaHei", 7))
            painter.drawText(pt.adjusted(0, -16, 0, 0),
                             Qt.AlignmentFlag.AlignLeft, "惯用前缀")

        # 前缀输入框
        if "btn_bg" in r:
            painter.fillRect(r["btn_bg"], QColor(c.get("btn_bg", "#6E9EAE")))
            painter.setPen(QPen(QColor(c.get("input_border", "#999")), 1))
            painter.drawRoundedRect(r["btn_bg"], 3, 3)
            painter.setPen(QColor(c.get("btn_text", "#FFF")))
            painter.setFont(QFont("Microsoft YaHei", 7))
            painter.drawText(r["btn_bg"].adjusted(4, 0, -4, 0),
                             Qt.AlignmentFlag.AlignVCenter, "GY2023DBN-")

        # +按钮
        if "accent" in r:
            painter.fillRect(r["accent"], QColor(c.get("accent", "#3A6E8E")))
            painter.setPen(QColor(c.get("accent_text", "#FFF")))
            painter.setFont(QFont("Microsoft YaHei", 8, QFont.Weight.Bold))
            painter.drawText(r["accent"], Qt.AlignmentFlag.AlignCenter, "+")

        # ── 右面板 ──

        # 文件名标签
        if "status_bg" in r:
            painter.fillRect(r["status_bg"],
                             QColor(c.get("status_bg", "#FFF")))
            painter.setPen(QColor(c.get("accent", "#3A6E8E")))
            painter.setFont(QFont("Microsoft YaHei", 8, QFont.Weight.Bold))
            painter.drawText(r["status_bg"].adjusted(4, 0, -4, 0),
                             Qt.AlignmentFlag.AlignVCenter,
                             "GY2023DBN-138.jpg")

        # 图片区域
        if "text" in r:
            painter.fillRect(r["text"], QColor(c.get("card", "#FFF")))
            painter.setPen(QPen(QColor(c.get("input_border", "#999")), 1))
            painter.drawRoundedRect(r["text"], 4, 4)
            painter.setPen(QColor(c.get("status_text", "#BBB")))
            painter.setFont(QFont("Microsoft YaHei", 10))
            painter.drawText(r["text"], Qt.AlignmentFlag.AlignCenter,
                             "📷 图片预览区域")

        # 旋转按钮
        for key in ("rotate_left", "rotate_right"):
            if key in r:
                painter.fillRect(r[key],
                                 QColor(c.get("nav_bg", "#FFF")))
                painter.setPen(QPen(QColor(c.get("nav_border", "#999")), 1))
                painter.drawRoundedRect(r[key], 3, 3)
                painter.setPen(QColor(c.get("nav_text", "#36A")))
                painter.setFont(QFont("Microsoft YaHei", 7))
                txt = "↩ 左旋" if key == "rotate_left" else "右旋 ↪"
                painter.drawText(r[key], Qt.AlignmentFlag.AlignCenter, txt)

        # 重命名行
        if "input_border" in r:
            painter.fillRect(r["input_border"],
                             QColor(c.get("input_bg", "#FFF")))
            painter.setPen(QPen(QColor(c.get("input_border", "#999")), 1))
            painter.drawRoundedRect(r["input_border"], 3, 3)
            painter.setPen(QColor(c.get("text", "#000")))
            painter.setFont(QFont("Microsoft YaHei", 7))
            painter.drawText(r["input_border"].adjusted(4, 0, -4, 0),
                             Qt.AlignmentFlag.AlignVCenter, "GY2023DBN-")

        if "btn_text" in r:
            painter.fillRect(r["btn_text"],
                             QColor(c.get("accent", "#3A6E8E")))
            painter.setPen(QColor(c.get("accent_text", "#FFF")))
            painter.setFont(QFont("Microsoft YaHei", 7, QFont.Weight.Bold))
            painter.drawText(r["btn_text"], Qt.AlignmentFlag.AlignCenter,
                             "确认重命名")

        # 导航按钮
        if "nav_border" in r:
            painter.fillRect(r["nav_border"],
                             QColor(c.get("nav_bg", "#FFF")))
            painter.setPen(QPen(QColor(c.get("nav_border", "#999")), 1))
            painter.drawRoundedRect(r["nav_border"], 3, 3)
            painter.setPen(QColor(c.get("nav_text", "#36A")))
            painter.setFont(QFont("Microsoft YaHei", 7))
            painter.drawText(r["nav_border"], Qt.AlignmentFlag.AlignCenter,
                             "◀ 上一张")

        if "nav_text" in r:
            painter.fillRect(r["nav_text"],
                             QColor(c.get("nav_bg", "#FFF")))
            painter.setPen(QPen(QColor(c.get("nav_border", "#999")), 1))
            painter.drawRoundedRect(r["nav_text"], 3, 3)
            painter.setPen(QColor(c.get("nav_text", "#36A")))
            painter.setFont(QFont("Microsoft YaHei", 7))
            painter.drawText(r["nav_text"], Qt.AlignmentFlag.AlignCenter,
                             "下一张 ▶")

        # 悬停高亮
        if self._hover and self._hover in r and self._hover != "hover":
            painter.setPen(QPen(QColor("#FFD700"), 2,
                                Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(r[self._hover].adjusted(
                -1, -1, 1, 1), 3, 3)

        # 选中高亮
        for key in self._selected:
            if key in r:
                painter.setPen(QPen(QColor("#FF4081"), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(r[key].adjusted(-1, -1, 1, 1), 3, 3)
                painter.setPen(QColor("#FF4081"))
                painter.setFont(QFont("Microsoft YaHei", 7,
                                      QFont.Weight.Bold))
                painter.drawText(r[key].adjusted(2, -12, 0, 0),
                                 Qt.AlignmentFlag.AlignLeft,
                                 self._labels.get(key, key))

        painter.end()

    # ── 工具 ────────────────────────────────────────────────

    def component_name(self, key: str) -> str:
        return self._labels.get(key, key)


# ── 设置对话框 ────────────────────────────────────────────

class SettingsDialog(QDialog):

    SUFFIX_OPTIONS = {
        "-x": "-{x}", ".x": ".{x}", "_x": "_{x}",
        " (x)": " ({x})", "无后缀": None,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(540, 580)
        self._settings = QSettings("ImageTool", "ImageViewer")
        self._shortcut_buttons: dict[str, ShortcutCaptureButton] = {}
        self._setup_ui()
        self._load_all()
        self._apply_dialog_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        tabs = QTabWidget()
        tabs.addTab(self._build_duplicate_tab(), "重名文件处理")
        tabs.addTab(self._build_shortcut_tab(), "快捷键设置")
        tabs.addTab(self._build_color_tab(), "颜色设计")
        layout.addWidget(tabs, 1)

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

    # ── 重名标签页 ──────────────────────────────────────────

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

    # ── 快捷键标签页 ────────────────────────────────────────

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
        self._shortcut_table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection)
        self._shortcut_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
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

    # ── 颜色设计标签页 ──────────────────────────────────────

    def _build_color_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(6)

        # 顶部：模式切换 + 自动对比 + 操作按钮
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("主题模式："))
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["明亮模式", "暗黑模式"])
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        top_row.addWidget(self._mode_combo)

        self._auto_contrast_check = QCheckBox("自动计算文字颜色")
        self._auto_contrast_check.setChecked(True)
        self._auto_contrast_check.setToolTip(
            "根据背景亮度自动选择黑/白文字，无需手动调整文字颜色")
        top_row.addWidget(self._auto_contrast_check)
        top_row.addStretch()

        reset_btn = QPushButton("  恢复默认颜色  ")
        reset_btn.setObjectName("rotateBtn")
        reset_btn.clicked.connect(self._reset_colors)
        top_row.addWidget(reset_btn)
        layout.addLayout(top_row)

        # 可滚动的预览区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        self._color_preview = ColorPreview()
        self._color_preview.selection_changed.connect(self._update_sel_label)
        preview_layout.addWidget(self._color_preview)

        # 选中组件信息 + 修改颜色按钮
        info_row = QHBoxLayout()
        self._sel_label = QLabel("点击上方预览图中的组件以选中，"
                                 "按住 Shift 可多选")
        self._sel_label.setObjectName("infoLabel")
        self._sel_label.setWordWrap(True)
        info_row.addWidget(self._sel_label, 1)

        self._color_btn = QPushButton("  修改选中颜色  ")
        self._color_btn.setObjectName("confirmBtn")
        self._color_btn.setEnabled(False)
        self._color_btn.clicked.connect(self._change_selected_color)
        info_row.addWidget(self._color_btn)
        preview_layout.addLayout(info_row)

        scroll.setWidget(preview_container)
        layout.addWidget(scroll, 1)

        # 颜色列表
        list_label = QLabel("各组件当前颜色：")
        list_label.setObjectName("infoLabel")
        layout.addWidget(list_label)

        self._color_table = QTableWidget(len(COLOR_ELEMENTS), 3)
        self._color_table.setHorizontalHeaderLabels(
            ["组件", "颜色值", "色块"])
        self._color_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        self._color_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed)
        self._color_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed)
        self._color_table.setColumnWidth(1, 80)
        self._color_table.setColumnWidth(2, 40)
        self._color_table.verticalHeader().setVisible(False)
        self._color_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self._color_table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection)
        self._color_table.setMaximumHeight(200)
        layout.addWidget(self._color_table)

        return w

    def _on_mode_changed(self, index: int):
        from app.styles import LIGHT_COLORS, DARK_COLORS
        mode = "light" if index == 0 else "dark"
        defaults = LIGHT_COLORS if mode == "light" else DARK_COLORS
        self._color_preview.load_colors(defaults)
        self._refresh_color_table()
        self._apply_dialog_theme()

    def _reset_colors(self):
        from app.styles import LIGHT_COLORS, DARK_COLORS
        mode = "light" if self._mode_combo.currentIndex() == 0 else "dark"
        defaults = LIGHT_COLORS if mode == "light" else DARK_COLORS
        self._color_preview.load_colors(defaults)
        self._refresh_color_table()

    def _change_selected_color(self):
        sel = self._color_preview.get_selected()
        if not sel:
            return
        key = list(sel)[0]
        current = self._color_preview.get_colors().get(key, "#FFFFFF")
        c = QColorDialog.getColor(QColor(current), self,
                                  f"选择颜色 — {self._color_preview.component_name(key)}")
        if c.isValid():
            colors = self._color_preview.get_colors()
            for k in sel:
                colors[k] = c.name()
            self._color_preview.load_colors(colors)
            self._refresh_color_table()
            self._update_sel_label()

    def _refresh_color_table(self):
        colors = self._color_preview.get_colors()
        for row, (key, name) in enumerate(COLOR_ELEMENTS):
            val = colors.get(key, "#FFFFFF")
            self._color_table.setItem(row, 0, QTableWidgetItem(name))
            self._color_table.setItem(row, 1, QTableWidgetItem(val))
            swatch = QLabel()
            swatch.setStyleSheet(
                f"background-color: {val}; border: 1px solid #888; border-radius: 3px;")
            swatch.setFixedSize(30, 20)
            self._color_table.setCellWidget(row, 2, swatch)

    def _update_sel_label(self):
        sel = self._color_preview.get_selected()
        if not sel:
            self._sel_label.setText(
                "点击上方预览图中的组件以选中，按住 Shift 可多选")
            self._color_btn.setEnabled(False)
        else:
            names = [self._color_preview.component_name(k) for k in sel]
            self._sel_label.setText(f"已选中：{', '.join(names)}")
            self._color_btn.setEnabled(True)

    # ── 对话框暗黑/明亮适配 ─────────────────────────────────

    def _apply_dialog_theme(self):
        mode = "light" if self._mode_combo.currentIndex() == 0 else "dark"
        if mode == "dark":
            self.setStyleSheet("""
                QDialog { background: #1e1e2e; color: #cdd6f4; }
                QLabel { color: #cdd6f4; }
                QGroupBox { color: #cdd6f4; border: 1px solid #45475a;
                            border-radius: 6px; margin-top: 8px; padding-top: 16px; }
                QGroupBox::title { subcontrol-origin: margin;
                                   left: 10px; padding: 0 6px; }
                QTabWidget::pane { border: 1px solid #45475a; background: #1e1e2e; }
                QTabBar::tab { background: #313244; color: #cdd6f4;
                               padding: 8px 16px; border: 1px solid #45475a;
                               border-bottom: none; border-radius: 4px 4px 0 0; }
                QTabBar::tab:selected { background: #1e1e2e; color: #cba6f7; }
                QTabBar::tab:hover { background: #45475a; }
                QComboBox { background: #181825; color: #cdd6f4;
                            border: 1px solid #45475a; border-radius: 4px;
                            padding: 4px 8px; }
                QComboBox::drop-down { border: none; }
                QComboBox QAbstractItemView { background: #181825; color: #cdd6f4;
                                              selection-background-color: #45475a; }
                QSpinBox { background: #181825; color: #cdd6f4;
                           border: 1px solid #45475a; border-radius: 4px;
                           padding: 4px; }
                QCheckBox { color: #cdd6f4; }
                QCheckBox::indicator { width: 16px; height: 16px; }
                QCheckBox::indicator:checked { background: #cba6f7;
                    border: 2px solid #cba6f7; border-radius: 3px; }
                QCheckBox::indicator:unchecked { background: #181825;
                    border: 2px solid #45475a; border-radius: 3px; }
                QTableWidget { background: #181825; color: #cdd6f4;
                               gridline-color: #313244; border: 1px solid #45475a; }
                QHeaderView::section { background: #313244; color: #cdd6f4;
                                       padding: 4px; border: 1px solid #45475a; }
                QPushButton { background: #313244; color: #cdd6f4;
                              border: none; border-radius: 6px;
                              padding: 8px 16px; }
                QPushButton:hover { background: #45475a; }
                QPushButton#confirmBtn { background: #cba6f7; color: #1e1e2e; }
                QPushButton#confirmBtn:hover { background: #b4befe; }
                QPushButton#rotateBtn { background: #181825; border: 1px solid #45475a; }
                QPushButton#rotateBtn:hover { background: #313244; }
                QScrollArea { background: #1e1e2e; border: none; }
                QWidget#qt_scrollarea_viewport { background: #1e1e2e; }
            """)
        else:
            self.setStyleSheet("")

    # ── 加载 / 保存 ─────────────────────────────────────────

    def _load_all(self):
        self._enable_check.setChecked(
            self._settings.value("auto_suffix_enabled", True, type=bool))
        suffix_key = self._settings.value("suffix_key", "-x", type=str)
        idx = list(self.SUFFIX_OPTIONS.keys()).index(
            suffix_key) if suffix_key in self.SUFFIX_OPTIONS else 0
        self._suffix_combo.setCurrentIndex(idx)
        self._start_spin.setValue(
            self._settings.value("start_num", 2, type=int))
        self._update_suffix_ui()

        self._build_shortcut_table(get_shortcuts(self._settings))

        from app.styles import LIGHT_COLORS, DARK_COLORS
        mode = self._settings.value("theme_mode", "light", type=str)
        self._mode_combo.setCurrentIndex(0 if mode == "light" else 1)
        self._auto_contrast_check.setChecked(
            self._settings.value("auto_contrast", True, type=bool))
        defaults = LIGHT_COLORS if mode == "light" else DARK_COLORS
        colors = {k: self._settings.value(f"color_{k}", v, type=str)
                  for k, v in defaults.items()}
        self._color_preview.load_colors(colors)
        self._refresh_color_table()

    def _save_and_close(self):
        self._settings.setValue("auto_suffix_enabled",
                                self._enable_check.isChecked())
        self._settings.setValue("suffix_key",
                                self._suffix_combo.currentText())
        self._settings.setValue("start_num", self._start_spin.value())
        for key, btn in self._shortcut_buttons.items():
            self._settings.setValue(f"shortcut_{key}",
                                    btn.get_key_sequence())
        mode = "light" if self._mode_combo.currentIndex() == 0 else "dark"
        self._settings.setValue("theme_mode", mode)
        self._settings.setValue("auto_contrast",
                                self._auto_contrast_check.isChecked())
        for key, color in self._color_preview.get_colors().items():
            self._settings.setValue(f"color_{key}", color)
        self.accept()
