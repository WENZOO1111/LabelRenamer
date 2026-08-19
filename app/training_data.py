"""训练数据管理 — 保存 OCR 识别结果与用户修正的对比数据"""

import json
import os
import csv
from datetime import datetime


class TrainingData:
    """管理 OCR 训练数据的存储和导出"""

    def __init__(self, app_dir: str | None = None):
        if app_dir is None:
            app_dir = os.path.join(os.path.expanduser("~"), ".label_renamer")
        self._dir = os.path.join(app_dir, "training_data")
        os.makedirs(self._dir, exist_ok=True)
        self._file = os.path.join(self._dir, "samples.jsonl")

    def save_sample(self, image_path: str, bbox: list[int],
                    ocr_result: str, user_text: str):
        """保存一条训练样本

        Args:
            image_path: 原始图片路径
            bbox: 选区坐标 [x1, y1, x2, y2]
            ocr_result: OCR 识别结果
            user_text: 用户最终输入的文本（修正后的结果）
        """
        sample = {
            "image": os.path.basename(image_path),
            "image_path": image_path,
            "bbox": bbox,
            "ocr": ocr_result,
            "user": user_text,
            "timestamp": datetime.now().isoformat(),
        }
        with open(self._file, "a", encoding="utf-8") as f:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    def count(self) -> int:
        """返回已收集的样本数量"""
        if not os.path.exists(self._file):
            return 0
        with open(self._file, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)

    def export_csv(self, path: str):
        """导出为 CSV 文件"""
        if not os.path.exists(self._file):
            return
        with open(self._file, "r", encoding="utf-8") as fin, \
             open(path, "w", encoding="utf-8-sig", newline="") as fout:
            writer = csv.writer(fout)
            writer.writerow(["图片", "选区", "OCR结果", "用户修正", "时间"])
            for line in fin:
                line = line.strip()
                if not line:
                    continue
                s = json.loads(line)
                writer.writerow([
                    s.get("image", ""),
                    str(s.get("bbox", [])),
                    s.get("ocr", ""),
                    s.get("user", ""),
                    s.get("timestamp", ""),
                ])
