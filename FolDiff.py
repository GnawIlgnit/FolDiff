import os
import re
import difflib
import customtkinter as ctk
from tkinter import filedialog, messagebox

# 初始化界面风格
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class FolderComparator(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("现代文件夹对比工具 Pro")
        self.geometry("900x800")

        # 配置布局权重
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # 变量定义
        self.path_a = ctk.StringVar()
        self.path_b = ctk.StringVar()
        self.similarity_threshold = ctk.DoubleVar(value=0.8)
        self.ignore_year = ctk.BooleanVar(value=True)  # 默认开启忽略年份

        # --- 1. 顶部标题 ---
        self.label_title = ctk.CTkLabel(self, text="网络文件夹差异与相似度分析",
                                        font=ctk.CTkFont(size=22, weight="bold"))
        self.label_title.grid(row=0, column=0, padx=20, pady=20)

        # --- 2. 文件夹选择区域 ---
        self.frame_selection = ctk.CTkFrame(self)
        self.frame_selection.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.frame_selection.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_selection, text="文件夹 A:").grid(row=0, column=0, padx=10, pady=10)
        self.entry_a = ctk.CTkEntry(self.frame_selection, textvariable=self.path_a, placeholder_text="请选择路径...")
        self.entry_a.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self.frame_selection, text="浏览", width=80,
                      command=lambda: self.browse_folder(self.path_a)).grid(row=0, column=2, padx=10, pady=10)

        ctk.CTkLabel(self.frame_selection, text="文件夹 B:").grid(row=1, column=0, padx=10, pady=10)
        self.entry_b = ctk.CTkEntry(self.frame_selection, textvariable=self.path_b, placeholder_text="请选择路径...")
        self.entry_b.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self.frame_selection, text="浏览", width=80,
                      command=lambda: self.browse_folder(self.path_b)).grid(row=1, column=2, padx=10, pady=10)

        # --- 3. 配置选项区域 (相似度 + 忽略年份) ---
        self.frame_config = ctk.CTkFrame(self)
        self.frame_config.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # 相似度滑动条
        self.label_sim = ctk.CTkLabel(self.frame_config, text=f"相似度阈值: {self.similarity_threshold.get():.0%}")
        self.label_sim.grid(row=0, column=0, padx=20, pady=10)
        self.slider = ctk.CTkSlider(self.frame_config, from_=0, to=1, variable=self.similarity_threshold,
                                    command=self.update_slider_label)
        self.slider.grid(row=0, column=1, sticky="ew", padx=10)
        self.frame_config.grid_columnconfigure(1, weight=1)

        # 忽略年份开关 (核心新增功能)
        self.switch_year = ctk.CTkSwitch(self.frame_config, text="忽略名称末尾年份后缀 (例如: (2016))",
                                         variable=self.ignore_year, font=ctk.CTkFont(size=12))
        self.switch_year.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="w")

        # --- 4. 操作按钮 ---
        self.btn_compare = ctk.CTkButton(self, text="立即开始深度对比", font=ctk.CTkFont(size=16, weight="bold"),
                                         height=45, fg_color="#1f538d", hover_color="#14375e",
                                         command=self.compare_folders)
        self.btn_compare.grid(row=3, column=0, padx=20, pady=15, sticky="ew")

        # --- 5. 结果展示区域 ---
        self.result_box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=13), border_width=2)
        self.result_box.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="nsew")

    def update_slider_label(self, value):
        self.label_sim.configure(text=f"相似度阈值: {value:.0%}")

    def browse_folder(self, var):
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    def clean_folder_name(self, name):
        """如果开启了忽略年份，则移除末尾的 (YYYY) 格式"""
        if self.ignore_year.get():
            # 正则解释: \s* (可选空格) \( (左括号) \d{4} (四位数字) \) (右括号) $ (行尾)
            return re.sub(r'\s*\(\d{4}\)$', '', name).strip()
        return name

    def get_subfolders_data(self, path):
        """获取文件夹数据，返回 {清洗后的名称: 原始名称} 的字典"""
        try:
            original_names = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
            data_map = {}
            for name in original_names:
                clean = self.clean_folder_name(name)
                # 如果有重名（如清洗后都叫 Project），保留第一个遇到的
                if clean not in data_map:
                    data_map[clean] = name
            return data_map
        except Exception as e:
            messagebox.showerror("错误", f"无法读取路径: {path}\n{e}")
            return None

    def calculate_similarity(self, s1, s2):
        return difflib.SequenceMatcher(None, s1, s2).ratio()

    def compare_folders(self):
        dir_a = self.path_a.get()
        dir_b = self.path_b.get()
        threshold = self.similarity_threshold.get()

        if not dir_a or not dir_b:
            messagebox.showwarning("提示", "请先选择两个文件夹")
            return

        map_a = self.get_subfolders_data(dir_a)
        map_b = self.get_subfolders_data(dir_b)

        if map_a is None or map_b is None: return

        self.result_box.delete("1.0", "end")
        header = f"🚀 对比模式: {'忽略年份后缀' if self.ignore_year.get() else '完全匹配'}\n"
        header += f"🔍 相似度阈值: {threshold:.0%}\n"
        header += "=" * 60 + "\n\n"
        self.result_box.insert("end", header)

        # 逻辑处理：使用清洗后的 Key 进行对比
        set_clean_a = set(map_a.keys())
        set_clean_b = set(map_b.keys())

        # 1. 完全匹配的项 (清洗后相同)
        exact_matches = set_clean_a & set_clean_b

        # 2. 差异项
        diff_a = sorted(list(set_clean_a - set_clean_b))
        diff_b = list(set_clean_b - set_clean_a)

        similar_pairs = []
        pure_missing_in_b = []

        for item_a in diff_a:
            best_match_key = None
            max_score = 0

            for item_b in diff_b:
                score = self.calculate_similarity(item_a, item_b)
                if score > max_score:
                    max_score = score
                    best_match_key = item_b

            if max_score >= threshold and best_match_key:
                similar_pairs.append((map_a[item_a], map_b[best_match_key], max_score))
                if best_match_key in diff_b: diff_b.remove(best_match_key)
            else:
                pure_missing_in_b.append(map_a[item_a])

        # --- 格式化输出 ---
        res = []
        res.append(f"📊 统计:")
        res.append(f"   - 文件夹 A: {len(map_a)} | 文件夹 B: {len(map_b)}")
        res.append(f"   - 匹配成功: {len(exact_matches)} 个文件夹")
        res.append("-" * 50)

        if similar_pairs:
            res.append(f"\n⚠️ 发现名称高度相似 (但清洗后仍不同):")
            for a, b, s in similar_pairs:
                res.append(f"   [!] {a}  ≈  {b} ({s:.1%})")

        if pure_missing_in_b:
            res.append(f"\n❌ 仅在 A 中存在 (B 中无匹配):")
            for item in pure_missing_in_b:
                res.append(f"   [-] {item}")

        if diff_b:
            res.append(f"\n✨ 仅在 B 中存在 (A 中无匹配):")
            for item_key in diff_b:
                res.append(f"   [+] {map_b[item_key]}")

        if not similar_pairs and not pure_missing_in_b and not diff_b:
            res.append("\n✅ 所有文件夹均已匹配成功！")

        self.result_box.insert("end", "\n".join(res))
        self.result_box.see("end")


if __name__ == "__main__":
    app = FolderComparator()
    app.mainloop()