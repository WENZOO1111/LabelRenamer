"""
图片查看器 - 启动入口
用法: python main.py [图片目录路径]
"""
import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.main_window import MainWindow
from app.styles import DARK_THEME


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)

    # 设置默认字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    # 如果命令行传了目录参数，则打开该目录
    start_dir = sys.argv[1] if len(sys.argv) > 1 else None
    if start_dir and not os.path.isdir(start_dir):
        print(f"目录不存在: {start_dir}")
        start_dir = None

    window = MainWindow(start_dir=start_dir)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
