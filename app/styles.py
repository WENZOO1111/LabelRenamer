DARK_THEME = """
/* 主色调: 3A6E8E 6E9EAE B4C8D8 E0C8D4 F2C8D0 */

QMainWindow {
    background-color: #B4C8D8;
}

QWidget {
    background-color: #B4C8D8;
    color: #2A3A4A;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* 文件列表 */
QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #6E9EAE;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}

QListWidget::item {
    padding: 6px 10px;
    border-radius: 4px;
    margin: 1px 2px;
}

QListWidget::item:selected {
    background-color: #3A6E8E;
    color: #FFFFFF;
}

QListWidget::item:hover {
    background-color: #E0C8D4;
}

/* 图片显示区域 */
QLabel#imageLabel {
    background-color: #FFFFFF;
    border: 1px solid #6E9EAE;
    border-radius: 8px;
    color: #6E9EAE;
}

/* 输入框 */
QLineEdit {
    background-color: #FFFFFF;
    border: 2px solid #6E9EAE;
    border-radius: 6px;
    padding: 8px 12px;
    color: #2A3A4A;
    font-size: 14px;
    selection-background-color: #3A6E8E;
    selection-color: #FFFFFF;
}

QLineEdit:focus {
    border: 2px solid #3A6E8E;
}

/* 按钮通用样式 */
QPushButton {
    background-color: #6E9EAE;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #3A6E8E;
}

QPushButton:pressed {
    background-color: #2A5A7A;
}

/* 主要操作按钮（重命名确认） */
QPushButton#confirmBtn {
    background-color: #3A6E8E;
    color: #FFFFFF;
    font-weight: 600;
}

QPushButton#confirmBtn:hover {
    background-color: #2A5A7A;
}

/* 导航按钮 */
QPushButton#navBtn {
    background-color: #FFFFFF;
    border: 1px solid #6E9EAE;
    color: #3A6E8E;
    font-size: 18px;
    padding: 8px 20px;
    min-width: 60px;
}

QPushButton#navBtn:hover {
    background-color: #E0C8D4;
    border-color: #3A6E8E;
}

/* 旋转按钮 */
QPushButton#rotateBtn {
    background-color: #FFFFFF;
    border: 1px solid #6E9EAE;
    color: #3A6E8E;
    font-size: 16px;
    padding: 8px 14px;
}

QPushButton#rotateBtn:hover {
    background-color: #F2C8D0;
    border-color: #3A6E8E;
}

/* 标签 */
QLabel#titleLabel {
    color: #3A6E8E;
    font-size: 12px;
    font-weight: 600;
}

QLabel#fileNameLabel {
    color: #3A6E8E;
    font-size: 14px;
    font-weight: 600;
}

QLabel#infoLabel {
    color: #6E9EAE;
    font-size: 12px;
}

/* 分隔线 */
QFrame#separator {
    background-color: #6E9EAE;
    max-height: 1px;
}

/* 状态栏 */
QStatusBar {
    background-color: #FFFFFF;
    color: #6E9EAE;
    border-top: 1px solid #6E9EAE;
}

/* 滚动条 */
QScrollBar:vertical {
    background-color: #FFFFFF;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #B4C8D8;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #6E9EAE;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #FFFFFF;
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background-color: #B4C8D8;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #6E9EAE;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""


# ── 默认主题色板 ──────────────────────────────────────────────

LIGHT_COLORS = {
    "bg": "#B4C8D8", "text": "#2A3A4A", "card": "#FFFFFF",
    "input_bg": "#FFFFFF", "input_border": "#6E9EAE",
    "btn_bg": "#6E9EAE", "btn_text": "#FFFFFF",
    "accent": "#3A6E8E", "accent_text": "#FFFFFF",
    "nav_bg": "#FFFFFF", "nav_border": "#6E9EAE", "nav_text": "#3A6E8E",
    "hover": "#E0C8D0", "status_bg": "#FFFFFF", "status_text": "#6E9EAE",
}

DARK_COLORS = {
    "bg": "#1e1e2e", "text": "#cdd6f4", "card": "#181825",
    "input_bg": "#181825", "input_border": "#313244",
    "btn_bg": "#313244", "btn_text": "#cdd6f4",
    "accent": "#cba6f7", "accent_text": "#1e1e2e",
    "nav_bg": "#181825", "nav_border": "#313244", "nav_text": "#cba6f7",
    "hover": "#45475a", "status_bg": "#181825", "status_text": "#6c7086",
}


def generate_qss(settings) -> str:
    """从 QSettings 读取颜色，生成 QSS 样式表"""
    mode = settings.value("theme_mode", "light", type=str)
    defaults = LIGHT_COLORS if mode == "light" else DARK_COLORS
    c = {}
    for key, default in defaults.items():
        c[key] = settings.value(f"color_{key}", default, type=str)

    return f"""
QMainWindow {{ background-color: {c['bg']}; }}
QWidget {{ background-color: {c['bg']}; color: {c['text']};
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif; font-size: 13px; }}

QListWidget {{ background-color: {c['card']}; border: 1px solid {c['input_border']};
    border-radius: 8px; padding: 4px; outline: none; }}
QListWidget::item {{ padding: 6px 10px; border-radius: 4px; margin: 1px 2px; }}
QListWidget::item:selected {{ background-color: {c['accent']}; color: {c['accent_text']}; }}
QListWidget::item:hover {{ background-color: {c['hover']}; }}

QLabel#imageLabel {{ background-color: {c['card']}; border: 1px solid {c['input_border']};
    border-radius: 8px; color: {c['input_border']}; }}

QLineEdit {{ background-color: {c['input_bg']}; border: 2px solid {c['input_border']};
    border-radius: 6px; padding: 8px 12px; color: {c['text']};
    font-size: 14px; selection-background-color: {c['accent']}; selection-color: {c['accent_text']}; }}
QLineEdit:focus {{ border: 2px solid {c['accent']}; }}

QPushButton {{ background-color: {c['btn_bg']}; color: {c['btn_text']}; border: none;
    border-radius: 6px; padding: 8px 16px; font-size: 13px; font-weight: 500; }}
QPushButton:hover {{ background-color: {c['accent']}; }}
QPushButton:pressed {{ background-color: {c['hover']}; }}

QPushButton#confirmBtn {{ background-color: {c['accent']}; color: {c['accent_text']}; font-weight: 600; }}
QPushButton#confirmBtn:hover {{ background-color: {c['hover']}; }}

QPushButton#navBtn {{ background-color: {c['nav_bg']}; border: 1px solid {c['nav_border']};
    color: {c['nav_text']}; font-size: 18px; padding: 8px 20px; min-width: 60px; }}
QPushButton#navBtn:hover {{ background-color: {c['hover']}; border-color: {c['accent']}; }}

QPushButton#rotateBtn {{ background-color: {c['nav_bg']}; border: 1px solid {c['nav_border']};
    color: {c['nav_text']}; font-size: 16px; padding: 8px 14px; }}
QPushButton#rotateBtn:hover {{ background-color: {c['hover']}; border-color: {c['accent']}; }}

QLabel#titleLabel {{ color: {c['accent']}; font-size: 12px; font-weight: 600; }}
QLabel#fileNameLabel {{ color: {c['accent']}; font-size: 14px; font-weight: 600; }}
QLabel#infoLabel {{ color: {c['status_text']}; font-size: 12px; }}

QFrame#separator {{ background-color: {c['input_border']}; max-height: 1px; }}

QStatusBar {{ background-color: {c['status_bg']}; color: {c['status_text']};
    border-top: 1px solid {c['input_border']}; }}

QScrollBar:vertical {{ background-color: {c['card']}; width: 8px; border-radius: 4px; }}
QScrollBar::handle:vertical {{ background-color: {c['hover']}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background-color: {c['btn_bg']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

QScrollBar:horizontal {{ background-color: {c['card']}; height: 8px; border-radius: 4px; }}
QScrollBar::handle:horizontal {{ background-color: {c['hover']}; border-radius: 4px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background-color: {c['btn_bg']}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
"""
