# LabelRenamer — 图片标签批量重命名工具

> 告别逐张重命名，让标签上的名字自动成为文件名。

---

## 简介 / Introduction

### 中文

在科研、农业、生物等领域，拍摄的样本照片往往带有标签（如品种编号 `GY2023DBN-138`），但文件名却是相机自动生成的哈希值（如 `0b624c0c.jpg`）。传统做法是逐张打开图片、手动输入文件名，效率极低。

**LabelRenamer** 专为解决这一问题而设计：打开包含图片的文件夹，浏览图片并查看标签内容，一键将文件名改为标签上的品种名。支持惯用前缀快速填入、重名自动编号、快捷键操作，让批量重命名从数小时缩短到几分钟。

### English

In research, agriculture, and biology, sample photos often carry labels with variety IDs (e.g. `GY2023DBN-138`), but filenames are auto-generated hashes (e.g. `0b624c0c.jpg`). The traditional approach — opening each image and manually typing the filename — is extremely tedious.

**LabelRenamer** solves this: open a folder of images, browse them with a built-in viewer, and rename files to match their label names with a single keystroke. With custom prefix shortcuts, auto-incrementing duplicate handling, and full keyboard support, batch renaming goes from hours to minutes.

---

## 功能特性 / Features

| 功能 | 说明 |
|------|------|
| 📂 图片浏览 | 内置图片查看器，支持缩放、左右导航 |
| 🔄 旋转保存 | 左旋/右旋 90°，后台线程保存，不阻塞界面 |
| ✏️ 快速重命名 | 输入框直接编辑文件名，Ctrl+S 一键确认 |
| 🏷️ 惯用前缀 | 保存常用前缀（如 `GY2023DBN-`），Ctrl+A 快速填入 |
| 🔢 重名自动编号 | 重名文件自动添加后缀（`-2`, `-3`...），可自定义格式 |
| ⌨️ 自定义快捷键 | 所有操作均可自定义快捷键 |
| 🎨 主题配色 | 明亮/暗黑模式，15 个颜色元素可自定义 |
| ✔️ 操作反馈 | 重命名/旋转成功后右上角显示文件名 + 已保存 |

| Feature | Description |
|---------|-------------|
| 📂 Image Viewer | Built-in viewer with zoom and left/right navigation |
| 🔄 Rotate & Save | Rotate 90° CW/CCW, saved in background thread |
| ✏️ Quick Rename | Edit filename directly, Ctrl+S to confirm |
| 🏷️ Custom Prefix | Save frequent prefixes (e.g. `GY2023DBN-`), Ctrl+A to apply |
| 🔢 Auto-numbering | Duplicates auto-suffixed (`-2`, `-3`...), customizable format |
| ⌨️ Custom Shortcuts | All actions fully customizable |
| 🎨 Theme Colors | Light/Dark mode, 15 customizable color elements |
| ✔️ Visual Feedback | Checkmark with filename appears after rename/rotate |

---

## 快捷键 / Keyboard Shortcuts

| 操作 | 默认快捷键 | Action | Default Shortcut |
|------|-----------|--------|-----------------|
| 应用惯用前缀 | Ctrl+A | Apply prefix | Ctrl+A |
| 确认重命名 | Ctrl+S | Rename file | Ctrl+S |
| 上一张图片 | Ctrl+← | Previous image | Ctrl+← |
| 下一张图片 | Ctrl+→ | Next image | Ctrl+→ |
| 上一个前缀 | ↑ | Previous prefix | ↑ |
| 下一个前缀 | ↓ | Next prefix | ↓ |
| 向左旋转 90° | Ctrl+Q | Rotate left | Ctrl+Q |
| 向右旋转 90° | Ctrl+E | Rotate right | Ctrl+E |
| 打开设置 | Ctrl+, | Open settings | Ctrl+, |

所有快捷键均可在 **设置 → 快捷键设置** 中自定义。

All shortcuts are customizable under **Settings → Shortcuts**.

---

## 安装与使用 / Installation

### 环境要求 / Requirements

- Python 3.11+
- conda（推荐）或 pip

### 快速开始 / Quick Start

```bash
# 1. 创建 conda 环境
conda create -n label_renamer python=3.11 -y
conda activate label_renamer

# 2. 安装依赖
conda install pyqt pillow -y

# 3. 启动应用
cd image_tool
python main.py

# 或指定图片目录
python main.py "C:\path\to\images"
```

### Windows 启动 / Windows Launch

双击 `启动.bat`（需先在 CMD/PowerShell 中执行 `conda activate label_renamer`）。

Double-click `启动.bat` (requires `conda activate label_renamer` in CMD/PowerShell first).

---

## 使用场景 / Use Cases

### 科研样本照片管理

拍摄的种子、植株、组织培养等样本照片，标签上标注了品种编号。使用 LabelRenamer 可以：

1. 打开照片文件夹
2. 浏览图片确认标签内容
3. 设置惯用前缀（如 `GY2023DBN-`）
4. 在输入框中输入编号（如 `138`），Ctrl+S 确认
5. Ctrl+→ 切换下一张，重复操作

### 实验室图片整理

批量整理实验数据图片，将无意义的文件名改为有意义的样本编号。

---

## 项目结构 / Project Structure

```
image_tool/
├── main.py                 # 应用入口
├── app/
│   ├── main_window.py      # 主窗口 + 自定义输入框
│   ├── image_viewer.py     # 图片查看器 + 后台旋转线程
│   ├── settings_dialog.py  # 设置面板（三标签页）
│   └── styles.py           # 主题样式 + 动态 QSS 生成
├── requirements.txt        # Python 依赖
├── 启动.bat                # Windows 启动脚本
└── README.md
```

---

## 许可证 / License

MIT License
