import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import requests
import json
import csv
import os
import sys

class PrintRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, text)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass

class AbstractProcessorGUI:
    def __init__(self, master):
        self.master = master
        master.title("论文摘要处理器")
        master.geometry("800x600")  # 恢复稍大窗口以容纳增大输入栏
        master.configure(bg="#fafafa")

        # 初始化CSV文件
        self.csv_path = 'output.csv'
        self.initialize_csv()

        # GUI组件初始化
        self.create_widgets()
        self.setup_print_redirector()

        # 线程通信队列
        self.queue = queue.Queue()
        self.master.after(100, self.process_queue)

        # 设置主题样式
        self.style = ttk.Style()
        self.configure_styles()

    def configure_styles(self):
        self.style.theme_use('clam')
        self.style.configure("TFrame", background="#fafafa")
        self.style.configure("TButton",
                            font=("Helvetica", 10),
                            padding=6,
                            background="#5a9bd4",
                            foreground="white")
        self.style.map("TButton",
                      background=[('active', '#487fac')],
                      foreground=[('active', 'white')])

    def initialize_csv(self):
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                csv.writer(f).writerow([
                    "催化剂", "反应", "反应原料-目标产物",
                    "反应原料", "目标产物", "期刊", "论文链接"
                ])

    def create_widgets(self):
        main_frame = ttk.Frame(self.master, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 输入区（增大）
        self.input_text = scrolledtext.ScrolledText(main_frame, height=20, wrap=tk.WORD,
                                                  font=("Helvetica", 10),
                                                  bg="#ffffff", borderwidth=0,
                                                  highlightthickness=1, highlightbackground="#e0e0e0")
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        process_btn = ttk.Button(main_frame, text="处理", command=self.start_processing)
        process_btn.pack(anchor="e", pady=(0, 10))

        # 下方双栏布局：状态和输出（缩小）
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.X)

        # 状态区
        self.status_text = scrolledtext.ScrolledText(content_frame, height=6, wrap=tk.WORD,
                                                    font=("Helvetica", 10),
                                                    bg="#f5f5f5", fg="#666666",
                                                    borderwidth=0, highlightthickness=1,
                                                    highlightbackground="#e0e0e0")
        self.status_text.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.status_text.configure(state="disabled")

        # 输出区
        self.output_text = scrolledtext.ScrolledText(content_frame, height=6, wrap=tk.WORD,
                                                    font=("Helvetica", 10),
                                                    bg="#f5f5f5", fg="#666666",
                                                    borderwidth=0, highlightthickness=1,
                                                    highlightbackground="#e0e0e0")
        self.output_text.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.output_text.configure(state="disabled")

        # 配置行列权重
        content_frame.columnconfigure((0, 1), weight=1)
        content_frame.rowconfigure(0, weight=0)  # 下方不扩展

    def setup_print_redirector(self):
        sys.stdout = PrintRedirector(self.status_text)

    def start_processing(self):
        abstract = self.input_text.get("1.0", tk.END).strip()
        if not abstract:
            print("⚠️ 请输入摘要内容")
            return

        thread = threading.Thread(target=self.process_abstract, args=(abstract,))
        thread.daemon = True
        thread.start()

    def process_abstract(self, abstract):
        print("\n🔍 开始处理...")
        url = "https://api.siliconflow.cn/v1/chat/completions"

        system_prompt = """请从化学论文摘要中提取：
    1. 催化剂（如无填N/A）
    2. 反应类型（如Suzuki偶联）
    3. 反应原料→目标产物（用→连接）
    4. 原料清单（逗号分隔）
    5. 目标产物
    6. 期刊名称（标准缩写）
    7. 论文链接（URL或DOI）

    严格按顺序输出7列，用"||"分割，保留化学物质标准命名。"""

        payload = {
            "model": "deepseek-ai/DeepSeek-V3",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": abstract}
            ],
            "temperature": 0.1,
            "max_tokens": 256,
            "response_format": {"type": "text"}
        }

        headers = {
            "Authorization": "Bearer 这里输入你的api",
            "Content-Type": "application/json"
        }

        try:
            print("🔄 正在调用API...")
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                print("✅ API调用成功")
                content = json.loads(response.text)['choices'][0]['message']['content']
                print(f"原始返回: {content}")

                if not content.startswith('ERROR'):
                    parts = content.split('||')
                    if len(parts) == 7:
                        self.write_to_csv(parts)
                        self.queue.put(lambda: self.show_output_content(parts))
                    else:
                        print(f"⛔ 字段数量异常（期望7列，实际{len(parts)}列）")
            else:
                print(f"❌ API错误: {response.status_code}")
        except Exception as e:
            print(f"⚠️ 异常: {str(e)}")

    def write_to_csv(self, parts):
        with open(self.csv_path, 'a', newline='', encoding='utf-8-sig') as f:
            csv.writer(f).writerow(parts)
        print(f"✅ 已保存到 {self.csv_path}")

    def show_output_content(self, parts):
        self.output_text.configure(state="normal")
        self.output_text.delete(1.0, tk.END)
        headers = ["催化剂", "反应", "原料→产物", "原料", "产物", "期刊", "链接"]
        for header, content in zip(headers, parts):
            self.output_text.insert(tk.END, f"{header}: {content.strip()}\n")
        self.output_text.configure(state="disabled")

    def process_queue(self):
        while not self.queue.empty():
            try:
                task = self.queue.get_nowait()
                task()
            except queue.Empty:
                pass
        self.master.after(100, self.process_queue)

if __name__ == "__main__":
    root = tk.Tk()
    app = AbstractProcessorGUI(root)
    root.mainloop()
