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
