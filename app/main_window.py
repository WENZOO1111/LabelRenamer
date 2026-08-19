from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QLineEdit, QPushButton, QLabel,
    QFrame, QStatusBar, QListWidgetItem, QSplitter,
    QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt, QSize, QSettings, QTimer
from PyQt6.QtGui import QKeySequence, QIcon, QFont, QShortcut, QKeyEvent
import os

from app.image_viewer import ImageViewer
from app.settings_dialog import SettingsDialog, get_shortcuts, event_to_str
from app.styles import generate_qss


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


class RenameInput(QLineEdit):
    """自定义输入框，根据用户设置的快捷键处理按键"""

    def __init__(self, main_window: "MainWindow", parent=None):
        super().__init__(parent)
        self._mw = main_window
        self._actions = {}  # 快捷键字符串 -> 回调函数

    def set_shortcuts(self, shortcuts: dict):
        """根据设置重建快捷键映射"""
        self._actions = {
            shortcuts["apply_prefix"]: self._mw._apply_prefix,
            shortcuts["rename"]: self._mw._rename_file,
            shortcuts["prev_image"]: self._mw._prev_image,
            shortcuts["next_image"]: self._mw._next_image,
            shortcuts["prev_prefix"]: self._mw._prev_prefix,
            shortcuts["next_prefix"]: self._mw._next_prefix,
            shortcuts["rotate_left"]: self._mw._rotate_left,
            shortcuts["rotate_right"]: self._mw._rotate_right,
        }

    def keyPressEvent(self, event: QKeyEvent):
        seq = event_to_str(event)
        if seq in self._actions:
            self._actions[seq]()
            return
        super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, start_dir: str = None):
        super().__init__()
        self.setWindowTitle("图片查看器")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 800)

        self._current_dir = start_dir or os.getcwd()
        self._image_files = []
        self._current_index = -1

        self._settings = QSettings("ImageTool", "ImageViewer")
        self._prefixes = self._settings.value("prefixes", [], type=list)
        self._active_prefix = self._settings.value("active_prefix", "", type=str)
        self._shortcuts: list[QShortcut] = []  # 跟踪全局快捷键

        self._setup_ui()
        self._apply_theme()
        self._setup_shortcuts()

        if start_dir:
            self._load_directory(start_dir)

    # ── UI 布局 ──────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # --- 左侧：文件列表 + 惯用前缀 ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # 目录选择按钮
        dir_row = QHBoxLayout()
        self._dir_label = QLabel("未选择目录")
        self._dir_label.setObjectName("infoLabel")
        self._dir_label.setWordWrap(True)
        dir_btn = QPushButton("  选择目录  ")
        dir_btn.clicked.connect(self._choose_directory)
        self._settings_btn = QPushButton("  设置  ")
        self._settings_btn.setObjectName("navBtn")
        self._settings_btn.clicked.connect(self._open_settings)
        dir_row.addWidget(self._dir_label, 1)
        dir_row.addWidget(dir_btn)
        dir_row.addWidget(self._settings_btn)
        left_layout.addLayout(dir_row)

        # 文件列表
        self._file_list = QListWidget()
        self._file_list.currentRowChanged.connect(self._on_list_select)
        left_layout.addWidget(self._file_list, 1)

        # 文件计数
        self._count_label = QLabel("0 张图片")
        self._count_label.setObjectName("infoLabel")
        left_layout.addWidget(self._count_label)

        # 分隔线
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        left_layout.addWidget(sep)

        # --- 惯用前缀区域 ---
        prefix_title = QLabel("惯用前缀（选中后 Ctrl+A 应用）")
        prefix_title.setObjectName("infoLabel")
        left_layout.addWidget(prefix_title)

        # 添加前缀输入行
        add_row = QHBoxLayout()
        add_row.setSpacing(4)
        self._prefix_input = QLineEdit()
        self._prefix_input.setPlaceholderText("输入新前缀，如 GY2023DBN-")
        self._prefix_input.returnPressed.connect(self._add_prefix)

        add_btn = QPushButton("+")
        add_btn.setFixedWidth(32)
        add_btn.setObjectName("confirmBtn")
        add_btn.clicked.connect(self._add_prefix)

        add_row.addWidget(self._prefix_input, 1)
        add_row.addWidget(add_btn)
        left_layout.addLayout(add_row)

        # 前缀列表
        self._prefix_list = QListWidget()
        self._prefix_list.setMaximumHeight(120)
        self._prefix_list.currentRowChanged.connect(self._on_prefix_select)
        left_layout.addWidget(self._prefix_list)

        # 删除前缀按钮
        del_row = QHBoxLayout()
        del_row.setSpacing(4)
        self._del_prefix_btn = QPushButton("  删除选中前缀  ")
        self._del_prefix_btn.setObjectName("rotateBtn")
        self._del_prefix_btn.clicked.connect(self._delete_prefix)
        del_row.addStretch()
        del_row.addWidget(self._del_prefix_btn)
        left_layout.addLayout(del_row)

        # --- 右侧：图片显示 + 控制栏 ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # 当前文件名 + 成功对勾
        name_row = QHBoxLayout()
        self._file_name_label = QLabel("")
        self._file_name_label.setObjectName("fileNameLabel")
        name_row.addWidget(self._file_name_label, 1)

        self._check_label = QLabel("")
        self._check_label.setObjectName("checkLabel")
        self._check_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._check_label.setStyleSheet("color: #4CAF50; font-size: 14px; font-weight: bold; background: transparent;")
        self._check_label.hide()
        name_row.addWidget(self._check_label)
        right_layout.addLayout(name_row)

        # 图片查看器
        self._viewer = ImageViewer()
        self._viewer.setMinimumHeight(400)
        self._viewer.image_rotated.connect(self._on_image_rotated)
        right_layout.addWidget(self._viewer, 1)

        # --- 旋转控制行 ---
        rotate_row = QHBoxLayout()
        rotate_row.setSpacing(8)

        rotate_left_btn = QPushButton("  ↩  向左旋转 90°")
        rotate_left_btn.setObjectName("rotateBtn")
        rotate_left_btn.clicked.connect(self._rotate_left)
        self._rotate_left_btn = rotate_left_btn

        rotate_right_btn = QPushButton("  向右旋转 90°  ↪ ")
        rotate_right_btn.setObjectName("rotateBtn")
        rotate_right_btn.clicked.connect(self._rotate_right)
        self._rotate_right_btn = rotate_right_btn

        rotate_row.addStretch()
        rotate_row.addWidget(rotate_left_btn)
        rotate_row.addWidget(rotate_right_btn)
        rotate_row.addStretch()
        right_layout.addLayout(rotate_row)

        # --- 重命名行 ---
        rename_row = QHBoxLayout()
        rename_row.setSpacing(8)

        rename_hint = QLabel("新文件名：")
        rename_hint.setObjectName("titleLabel")
        self._rename_input = RenameInput(self)
        self._rename_input.setPlaceholderText("输入新文件名（不含扩展名）")

        confirm_btn = QPushButton("  确认重命名  ")
        confirm_btn.setObjectName("confirmBtn")
        confirm_btn.clicked.connect(self._rename_file)

        rename_row.addWidget(rename_hint)
        rename_row.addWidget(self._rename_input, 1)
        rename_row.addWidget(confirm_btn)
        right_layout.addLayout(rename_row)

        # --- 导航行 ---
        nav_row = QHBoxLayout()
        nav_row.setSpacing(8)

        prev_btn = QPushButton("◀  上一张")
        prev_btn.setObjectName("navBtn")
        prev_btn.clicked.connect(self._prev_image)

        self._nav_info = QLabel("0 / 0")
        self._nav_info.setObjectName("infoLabel")
        self._nav_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._nav_info.setMinimumWidth(100)

        next_btn = QPushButton("下一张  ▶")
        next_btn.setObjectName("navBtn")
        next_btn.clicked.connect(self._next_image)

        nav_row.addStretch()
        nav_row.addWidget(prev_btn)
        nav_row.addWidget(self._nav_info)
        nav_row.addWidget(next_btn)
        nav_row.addStretch()
        right_layout.addLayout(nav_row)

        # --- 组装左右面板 ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_panel.setMinimumWidth(220)
        left_panel.setMaximumWidth(340)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # 状态栏
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        # 加载已保存的前缀列表
        self._refresh_prefix_list()

    # ── 快捷键 ──────────────────────────────────────────────

    def _setup_shortcuts(self):
        # 清理旧的全局快捷键
        for sc in self._shortcuts:
            sc.setEnabled(False)
            sc.deleteLater()
        self._shortcuts.clear()

        shortcuts = get_shortcuts(self._settings)

        # 全局快捷键（输入框无焦点时生效）
        for action, callback in [
            ("rename", self._rename_file),
            ("prev_image", self._prev_image),
            ("next_image", self._next_image),
            ("rotate_left", self._rotate_left),
            ("rotate_right", self._rotate_right),
            ("open_settings", self._open_settings),
        ]:
            seq = shortcuts.get(action, "")
            if seq:
                sc = QShortcut(QKeySequence(seq), self)
                sc.activated.connect(callback)
                self._shortcuts.append(sc)

        # 通知 RenameInput 更新快捷键映射
        self._rename_input.set_shortcuts(shortcuts)

    # ── 目录操作 ─────────────────────────────────────────────

    def _choose_directory(self):
        d = QFileDialog.getExistingDirectory(self, "选择图片目录", self._current_dir)
        if d:
            self._load_directory(d)

    def _load_directory(self, path: str):
        self._current_dir = path
        self._dir_label.setText(path)

        self._image_files = sorted(
            f for f in os.listdir(path)
            if os.path.isfile(os.path.join(path, f))
            and os.path.splitext(f)[1].lower() in IMAGE_EXTS
        )
        self._count_label.setText(f"{len(self._image_files)} 张图片")

        self._file_list.blockSignals(True)
        self._file_list.clear()
        for f in self._image_files:
            item = QListWidgetItem(f)
            self._file_list.addItem(item)
        self._file_list.blockSignals(False)

        if self._image_files:
            self._file_list.setCurrentRow(0)
        else:
            self._current_index = -1
            self._file_name_label.setText("")
            self._nav_info.setText("0 / 0")
            self._rename_input.clear()
            self._viewer._label.setText("目录中没有图片")

        self._status_bar.showMessage(f"已加载目录: {path}")

    # ── 列表选择 ─────────────────────────────────────────────

    def _on_list_select(self, row: int):
        if row < 0 or row >= len(self._image_files):
            return
        self._current_index = row
        self._show_current_image()

    def _show_current_image(self):
        if self._current_index < 0 or self._current_index >= len(self._image_files):
            return

        fname = self._image_files[self._current_index]
        fpath = os.path.join(self._current_dir, fname)

        self._file_name_label.setText(fname)
        name_no_ext = os.path.splitext(fname)[0]
        # 自动去掉当前选中的惯用前缀，方便输入后缀编号
        if self._active_prefix and name_no_ext.startswith(self._active_prefix):
            self._rename_input.setText(name_no_ext[len(self._active_prefix):])
        else:
            self._rename_input.setText(name_no_ext)
        self._nav_info.setText(f"{self._current_index + 1} / {len(self._image_files)}")

        self._viewer.load_image(fpath)

    # ── 导航 ────────────────────────────────────────────────

    def _prev_image(self):
        if not self._image_files:
            return
        new_idx = self._current_index - 1
        if new_idx < 0:
            new_idx = len(self._image_files) - 1
        self._file_list.setCurrentRow(new_idx)

    def _next_image(self):
        if not self._image_files:
            return
        new_idx = self._current_index + 1
        if new_idx >= len(self._image_files):
            new_idx = 0
        self._file_list.setCurrentRow(new_idx)

    # ── 旋转 ────────────────────────────────────────────────

    def _rotate_left(self):
        self._rotate_left_btn.setEnabled(False)
        self._rotate_right_btn.setEnabled(False)
        self._status_bar.showMessage("旋转中…")
        self._viewer.rotate_left()

    def _rotate_right(self):
        self._rotate_left_btn.setEnabled(False)
        self._rotate_right_btn.setEnabled(False)
        self._status_bar.showMessage("旋转中…")
        self._viewer.rotate_right()

    def _on_image_rotated(self, path: str):
        """旋转后台线程完成后的回调"""
        self._rotate_left_btn.setEnabled(True)
        self._rotate_right_btn.setEnabled(True)
        fname = os.path.basename(path)
        name_no_ext = os.path.splitext(fname)[0]
        self._check_label.setText(f"{name_no_ext} 已保存 ✔")
        self._check_label.show()
        QTimer.singleShot(2000, self._check_label.hide)
        self._status_bar.showMessage("旋转并保存完成", 3000)

    # ── 惯用前缀 ─────────────────────────────────────────────

    def _refresh_prefix_list(self):
        """刷新前缀列表控件，高亮当前选中的前缀"""
        self._prefix_list.blockSignals(True)
        self._prefix_list.clear()
        for p in self._prefixes:
            self._prefix_list.addItem(p)
        # 高亮当前选中的前缀
        if self._active_prefix in self._prefixes:
            idx = self._prefixes.index(self._active_prefix)
            self._prefix_list.setCurrentRow(idx)
        self._prefix_list.blockSignals(False)

    def _on_prefix_select(self, row: int):
        """点击前缀列表项，设为当前选中的前缀"""
        if row < 0 or row >= len(self._prefixes):
            return
        self._active_prefix = self._prefixes[row]
        self._settings.setValue("active_prefix", self._active_prefix)
        self._status_bar.showMessage(f"当前前缀: {self._active_prefix}", 3000)

    def _add_prefix(self):
        """添加新前缀到列表"""
        text = self._prefix_input.text().strip()
        if not text:
            return
        if text in self._prefixes:
            self._status_bar.showMessage("该前缀已存在", 3000)
            return
        self._prefixes.append(text)
        self._settings.setValue("prefixes", self._prefixes)
        self._prefix_input.clear()
        self._refresh_prefix_list()
        self._status_bar.showMessage(f"已添加前缀: {text}", 3000)

    def _delete_prefix(self):
        """删除选中的前缀"""
        row = self._prefix_list.currentRow()
        if row < 0 or row >= len(self._prefixes):
            self._status_bar.showMessage("请先选中要删除的前缀", 3000)
            return
        removed = self._prefixes.pop(row)
        if self._active_prefix == removed:
            self._active_prefix = ""
            self._settings.setValue("active_prefix", "")
        self._settings.setValue("prefixes", self._prefixes)
        self._refresh_prefix_list()
        self._status_bar.showMessage(f"已删除前缀: {removed}", 3000)

    def _apply_prefix(self):
        """Ctrl+A: 将选中的惯用前缀插入重命名输入框（覆盖当前内容）"""
        if not self._active_prefix:
            self._status_bar.showMessage("请先在左侧选中一个惯用前缀", 3000)
            return
        self._rename_input.setText(self._active_prefix)
        self._rename_input.setFocus()
        self._status_bar.showMessage(f"已应用前缀: {self._active_prefix}", 2000)

    def _prev_prefix(self):
        """Up: 切换到上一个惯用前缀"""
        if not self._prefixes:
            return
        row = self._prefix_list.currentRow()
        new_row = row - 1 if row > 0 else len(self._prefixes) - 1
        self._prefix_list.setCurrentRow(new_row)

    def _next_prefix(self):
        """Down: 切换到下一个惯用前缀"""
        if not self._prefixes:
            return
        row = self._prefix_list.currentRow()
        new_row = row + 1 if row < len(self._prefixes) - 1 else 0
        self._prefix_list.setCurrentRow(new_row)

    def _show_checkmark(self, filename: str):
        """显示成功对勾：文件名 + 已保存 + √"""
        name_no_ext = os.path.splitext(filename)[0]
        self._check_label.setText(f"{name_no_ext} 已保存 ✔")
        self._check_label.show()
        QTimer.singleShot(2000, self._check_label.hide)

    def closeEvent(self, event):
        """关闭窗口时清理后台线程"""
        self._viewer.cleanup()
        super().closeEvent(event)

    # ── 设置 ────────────────────────────────────────────────

    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self._apply_theme()
            self._setup_shortcuts()

    def _apply_theme(self):
        """从 QSettings 读取颜色并应用 QSS"""
        qss = generate_qss(self._settings)
        self.setStyleSheet(qss)

    # ── 重命名 ──────────────────────────────────────────────

    def _find_unique_name(self, base: str, ext: str) -> str:
        """根据设置的后缀格式，自动处理重名文件"""
        suffix_fmt = self._settings.value("suffix_key", "-x", type=str)
        start_num = self._settings.value("start_num", 2, type=int)

        fmt_map = {
            "-x": "-{x}",
            ".x": ".{x}",
            "_x": "_{x}",
            " (x)": " ({x})",
            "无后缀": None,
        }
        fmt = fmt_map.get(suffix_fmt)

        # 无后缀模式：直接返回原名（由调用方决定是否覆盖）
        if fmt is None:
            return base + ext

        candidate = base + ext
        num = start_num
        while os.path.exists(os.path.join(self._current_dir, candidate)):
            candidate = base + fmt.replace("{x}", str(num)) + ext
            num += 1
        return candidate

    def _rename_file(self):
        if self._current_index < 0 or self._current_index >= len(self._image_files):
            return

        old_name = self._image_files[self._current_index]
        new_base = self._rename_input.text().strip()

        if not new_base:
            self._status_bar.showMessage("文件名不能为空", 3000)
            return

        ext = os.path.splitext(old_name)[1]

        # 根据开关决定重名处理方式
        auto_enabled = self._settings.value("auto_suffix_enabled", True, type=bool)
        if auto_enabled:
            new_name = self._find_unique_name(new_base, ext)
        else:
            new_name = new_base + ext
            if os.path.exists(os.path.join(self._current_dir, new_name)):
                box = QMessageBox(self)
                box.setWindowTitle("确认覆盖")
                box.setText(f"文件 {new_name} 已存在，是否覆盖？")
                box.setIcon(QMessageBox.Icon.Warning)
                yes_btn = box.addButton("覆盖", QMessageBox.ButtonRole.AcceptRole)
                box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
                box.setDefaultButton(yes_btn)
                box.exec()
                if box.clickedButton() != yes_btn:
                    return

        if new_name == old_name:
            self._status_bar.showMessage("文件名未改变", 3000)
            return

        old_path = os.path.join(self._current_dir, old_name)
        new_path = os.path.join(self._current_dir, new_name)

        try:
            os.rename(old_path, new_path)
        except Exception as e:
            QMessageBox.critical(self, "重命名失败", str(e))
            return

        # 更新列表
        self._image_files[self._current_index] = new_name
        self._file_list.item(self._current_index).setText(new_name)
        self._file_name_label.setText(new_name)

        self._show_checkmark(new_name)
        self._status_bar.showMessage(f"已重命名: {old_name} → {new_name}", 3000)
