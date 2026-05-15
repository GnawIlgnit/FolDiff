import os
import re
import difflib
import time
import customtkinter as ctk
from tkinter import filedialog, messagebox

# --- Google 品牌配色方案 ---
G_BLUE = "#4285F4"
G_RED = "#EA4335"
G_YELLOW = "#FBBC05"
G_GREEN = "#34A853"
G_BG_DARK = "#202124"  # Google 深色模式背景色

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class PathPeer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("FolDiff Pro - 文件夹名对比工具")
        self.width = 900
        self.height = 800
        self.center_window()  # 居中显示

        self.configure(fg_color=G_BG_DARK)

        # 布局配置
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # 数据变量
        self.path_a = ctk.StringVar()
        self.path_b = ctk.StringVar()
        self.similarity_threshold = ctk.DoubleVar(value=0.8)
        self.ignore_year = ctk.BooleanVar(value=True)

        # --- 1. 顶部装饰条 (Google 四色线) ---
        self.canvas_line = ctk.CTkCanvas(self, height=4, highlightthickness=0, bg=G_BG_DARK)
        self.canvas_line.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.draw_google_line()

        # --- 2. 标题 ---
        self.label_title = ctk.CTkLabel(self, text="文件夹名差异分析",
                                        font=ctk.CTkFont(family="Microsoft YaHei", size=26, weight="bold"),
                                        text_color="white")
        self.label_title.grid(row=1, column=0, padx=20, pady=10)

        # --- 3. 路径选择区域 ---
        self.frame_selection = ctk.CTkFrame(self, fg_color="#292a2d", corner_radius=15)
        self.frame_selection.grid(row=2, column=0, padx=30, pady=15, sticky="ew")
        self.frame_selection.grid_columnconfigure(1, weight=1)

        # 文件夹 A
        ctk.CTkLabel(self.frame_selection, text="源文件夹 A:", text_color=G_BLUE).grid(row=0, column=0, padx=15,
                                                                                       pady=15)
        self.entry_a = ctk.CTkEntry(self.frame_selection, textvariable=self.path_a, border_color="#5f6368",
                                    fg_color="#3c4043")
        self.entry_a.grid(row=0, column=1, padx=5, pady=15, sticky="ew")
        ctk.CTkButton(self.frame_selection, text="选择", width=70, fg_color=G_BLUE, hover_color="#3367D6",
                      command=lambda: self.browse_folder(self.path_a)).grid(row=0, column=2, padx=15, pady=15)

        # 文件夹 B
        ctk.CTkLabel(self.frame_selection, text="对比文件夹 B:", text_color=G_GREEN).grid(row=1, column=0, padx=15,
                                                                                          pady=15)
        self.entry_b = ctk.CTkEntry(self.frame_selection, textvariable=self.path_b, border_color="#5f6368",
                                    fg_color="#3c4043")
        self.entry_b.grid(row=1, column=1, padx=5, pady=15, sticky="ew")
        ctk.CTkButton(self.frame_selection, text="选择", width=70, fg_color=G_GREEN, hover_color="#2D8C47",
                      command=lambda: self.browse_folder(self.path_b)).grid(row=1, column=2, padx=15, pady=15)

        # --- 4. 配置选项 ---
        self.frame_config = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_config.grid(row=3, column=0, padx=30, pady=5, sticky="ew")
        self.frame_config.grid_columnconfigure(1, weight=1)

        self.label_sim = ctk.CTkLabel(self.frame_config, text=f"相似度匹配: {self.similarity_threshold.get():.0%}")
        self.label_sim.grid(row=0, column=0, padx=15)
        self.slider = ctk.CTkSlider(self.frame_config, from_=0, to=1, variable=self.similarity_threshold,
                                    button_color=G_YELLOW, button_hover_color="#E6AC05", progress_color=G_YELLOW,
                                    command=self.update_slider_label)
        self.slider.grid(row=0, column=1, sticky="ew", padx=10)

        self.switch_year = ctk.CTkSwitch(self.frame_config, text="忽略名称末尾年份 (20XX)",
                                         variable=self.ignore_year, progress_color=G_BLUE)
        self.switch_year.grid(row=0, column=2, padx=20)

        # --- 5. 动画进度条 & 按钮 ---
        self.progress_bar = ctk.CTkProgressBar(self, mode="determinate", height=4, progress_color=G_BLUE,
                                               fg_color="#3c4043")
        self.progress_bar.set(0)
        self.progress_bar.grid(row=4, column=0, padx=30, pady=(20, 10), sticky="ew")

        self.btn_compare = ctk.CTkButton(self, text="开始深度扫描", font=ctk.CTkFont(size=16, weight="bold"),
                                         height=50, fg_color=G_BLUE, hover_color="#3367D6", corner_radius=25,
                                         command=self.start_analysis_animation)
        self.btn_compare.grid(row=5, column=0, padx=30, pady=10, sticky="ew")

        # --- 6. 结果区域 ---
        self.result_box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=13),
                                         fg_color="#171717", border_color="#3c4043", border_width=1)
        self.result_box.grid(row=6, column=0, padx=30, pady=(10, 30), sticky="nsew")

    def center_window(self):
        """窗口居中逻辑"""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (self.width // 2)
        y = (screen_height // 2) - (self.height // 2)
        self.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def draw_google_line(self):
        """绘制顶部 Google 彩色条"""
        w = self.width
        unit = w // 4
        self.canvas_line.create_rectangle(0, 0, unit, 4, fill=G_BLUE, outline="")
        self.canvas_line.create_rectangle(unit, 0, unit * 2, 4, fill=G_RED, outline="")
        self.canvas_line.create_rectangle(unit * 2, 0, unit * 3, 4, fill=G_YELLOW, outline="")
        self.canvas_line.create_rectangle(unit * 3, 0, w, 4, fill=G_GREEN, outline="")

    def update_slider_label(self, value):
        self.label_sim.configure(text=f"相似度匹配: {value:.0%}")

    def browse_folder(self, var):
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    def clean_name(self, name):
        if self.ignore_year.get():
            return re.sub(r'\s*\(\d{4}\)$', '', name).strip()
        return name

    def start_analysis_animation(self):
        """模拟丝滑的分析动画"""
        if not self.path_a.get() or not self.path_b.get():
            messagebox.showwarning("提示", "请先选择两个网络文件夹路径")
            return

        self.btn_compare.configure(state="disabled", text="正在扫描文件系统...")
        self.result_box.delete("1.0", "end")

        # 平滑进度条增长动画
        def step(v):
            if v <= 1.0:
                self.progress_bar.set(v)
                self.after(10, lambda: step(v + 0.05))
            else:
                self.run_comparison()
                self.btn_compare.configure(state="normal", text="开始深度扫描")

        step(0)

    def run_comparison(self):
        """执行对比逻辑"""
        dir_a = self.path_a.get()
        dir_b = self.path_b.get()
        threshold = self.similarity_threshold.get()

        try:
            # 读取数据
            list_a = [f for f in os.listdir(dir_a) if os.path.isdir(os.path.join(dir_a, f))]
            list_b = [f for f in os.listdir(dir_b) if os.path.isdir(os.path.join(dir_b, f))]
        except Exception as e:
            messagebox.showerror("读取失败", f"无法访问网络文件夹:\n{e}")
            return

        map_a = {self.clean_name(n): n for n in list_a}
        map_b = {self.clean_name(n): n for n in list_b}

        set_clean_a = set(map_a.keys())
        set_clean_b = set(map_b.keys())

        # 核心逻辑
        exact = set_clean_a & set_clean_b
        diff_a = sorted(list(set_clean_a - set_clean_b))
        diff_b = list(set_clean_b - set_clean_a)

        similar = []
        missing_a = []

        for item_a in diff_a:
            best_match, max_score = None, 0
            for item_b in diff_b:
                score = difflib.SequenceMatcher(None, item_a, item_b).ratio()
                if score > max_score:
                    max_score, best_match = score, item_b

            if max_score >= threshold and best_match:
                similar.append((map_a[item_a], map_b[best_match], max_score))
                if best_match in diff_b: diff_b.remove(best_match)
            else:
                missing_a.append(map_a[item_a])

        # 结果输出
        out = [f"【分析报告】生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n" + "=" * 60 + "\n"]
        out.append(f"🟢 匹配成功: {len(exact)} 个文件夹")

        if similar:
            out.append(f"\n🟡 疑似命名差异 (相似度 > {threshold:.0%}):")
            for a, b, s in similar:
                out.append(f"   [!] {a}  >>  {b} ({s:.1%})")

        if missing_a:
            out.append(f"\n🔴 仅在文件夹 A 中存在:")
            for item in missing_a:
                out.append(f"   [-] {item}")

        if diff_b:
            out.append(f"\n🔵 仅在文件夹 B 中存在:")
            for item_key in diff_b:
                out.append(f"   [+] {map_b[item_key]}")

        if not similar and not missing_a and not diff_b:
            out.append("\n🌈 完美匹配！两个路径下的文件夹结构完全一致。")

        self.result_box.insert("end", "\n".join(out))
        self.result_box.see("end")


if __name__ == "__main__":
    app = PathPeer()
    app.mainloop()