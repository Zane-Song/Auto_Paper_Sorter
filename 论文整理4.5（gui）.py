import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import threading
import re
import requests
import json
import csv
import os


# 原有的函数定义保持不变
def extract_next_record(file_path):
    """
    从文件中提取第一条记录（记录之间以空行分隔），
    提取后将该记录从文件中删除。
    """
    if not os.path.exists(file_path):
        return None

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        content = f.read().strip()
    if not content:
        return None

    records = re.split(r'\n\s*\n', content)
    record = records[0].strip()

    remaining = "\n\n".join(records[1:]).strip()
    with open(file_path, 'w', encoding='utf-8-sig') as f:
        f.write(remaining)
    return record

def process_abstract(abstract):
    """处理论文摘要生成结构化数据"""
    print("\n🔍 开始处理摘要...")
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
        "model": "Pro/deepseek-ai/DeepSeek-V3",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": abstract}
        ],
        "temperature": 0.1,
        "max_tokens": 128,
        "response_format": {"type": "text"}
    }

    headers = {
        "Authorization": "Bearer sk-jdurtrtvwrmplswmkhtptswxfairtnrzdsdjoiqqcppzjdfr",
        "Content-Type": "application/json"
    }

    try:
        print("🔄 正在调用API...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            print("✅ API调用成功")
            content = json.loads(response.text)['choices'][0]['message']['content']
            return content.strip()
        else:
            print(f"❌ API返回错误状态码: {response.status_code}")
            return f"ERROR {response.status_code}"
    except Exception as e:
        print(f"⚠️ 发生网络异常: {str(e)}")
        return f"ERROR {str(e)}"

# 重定向输出类
class TextRedirector:
    def __init__(self, widget):
        self.widget = widget
    def write(self, text):
        self.widget.insert(tk.END, text)
        self.widget.see(tk.END)
    def flush(self): pass

# GUI主程序
root = tk.Tk()
root.title("论文摘要处理器")
root.geometry("800x600")
root.configure(bg='#FFF3E0')  # 窗口背景色：浅杏色

# 顶部Frame
top_frame = ttk.Frame(root, style="Top.TFrame")
top_frame.pack(pady=12)

file_path_var = tk.StringVar()

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        file_path_var.set(file_path)

# 创建样式
style = ttk.Style()
style.theme_use('clam')

# 配置顶部Frame样式
style.configure("Top.TFrame", background='#FFF3E0')

# 配置按钮通用样式
style.configure("TButton", padding=8, font=("Arial Rounded MT Bold", 11), relief="flat")
style.map("TButton", foreground=[('active', '!disabled', '#FFFFFF')])

# 开始按钮（绿色）
style.configure("Start.TButton", background="#4CAF50", foreground="white")
style.map("Start.TButton",
          background=[('active', '!disabled', '#388E3C'), ('hover', '!disabled', '#66BB6A')])

# 结束按钮（红色）
style.configure("Stop.TButton", background="#FF5252", foreground="white")
style.map("Stop.TButton",
          background=[('active', '!disabled', '#D32F2F'), ('hover', '!disabled', '#FF8A80')])

# 选择文件按钮（蓝色）
style.configure("Select.TButton", background="#42A5F5", foreground="white")
style.map("Select.TButton",
          background=[('active', '!disabled', '#1976D2'), ('hover', '!disabled', '#64B5F6')])

# 文件选择按钮
select_button = ttk.Button(top_frame, text="选择文件", style="Select.TButton", command=select_file)
select_button.grid(row=0, column=0, padx=12)

# 文件路径标签
file_label = ttk.Label(top_frame, textvariable=file_path_var, wraplength=400, background='#FFF3E0', foreground='#00695C', font=("Arial Rounded MT Bold", 11))
file_label.grid(row=0, column=1, padx=12)

# 开始按钮
start_button = ttk.Button(top_frame, text="开始", style="Start.TButton", command=lambda: start_processing())
start_button.grid(row=0, column=2, padx=12)

# 结束按钮
stop_button = ttk.Button(top_frame, text="结束", style="Stop.TButton", command=lambda: stop_processing())
stop_button.grid(row=0, column=3, padx=12)

# 中部文本框
text_frame = ttk.Frame(root, style="Text.TFrame")
text_frame.pack(pady=12, fill=tk.BOTH, expand=True)

text_widget = tk.Text(text_frame, wrap=tk.WORD, height=20, bg='#F9F9F9', fg='#424242', relief='flat', bd=2, font=("Arial Rounded MT Bold", 10), padx=5, pady=5)
text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
text_widget.config(yscrollcommand=scrollbar.set)

# 配置文本框Frame样式
style.configure("Text.TFrame", background='#FFF3E0')

# 配置滚动条样式
style.configure("Vertical.TScrollbar", background="#EEEEEE", troughcolor="#FFF3E0")
style.map("Vertical.TScrollbar",
          background=[('active', '#42A5F5'), ('hover', '#64B5F6')])

# 重定向stdout到文本框
sys.stdout = TextRedirector(text_widget)

# 处理逻辑（省略具体实现）
processing_flag = False

def start_processing():
    global processing_flag
    if not file_path_var.get():
        messagebox.showwarning("警告", "请先选择文件")
        return
    processing_flag = True
    threading.Thread(target=run_main, daemon=True).start()

def stop_processing():
    global processing_flag
    processing_flag = False

def run_main():
    global processing_flag
    txt_path = file_path_var.get()
    csv_path = 'output/output.csv'

    if not os.path.exists(csv_path):
        print(f"📁 创建新CSV文件: {csv_path}")
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            csv.writer(f).writerow([
                "催化剂", "反应", "反应原料-目标产物",
                "反应原料", "目标产物", "期刊", "论文链接"
            ])
    else:
        print(f"📂 检测到已有CSV文件，将在现有文件追加数据")

    try:
        while processing_flag:
            record = extract_next_record(txt_path)
            if record is None:
                print("🎉 无更多记录需要处理，程序结束")
                break

            print("\n📝 正在处理记录：")
            print(record)

            result = process_abstract(record)
            print(f"⚙️ 处理结果: {result}")

            if not result.startswith("ERROR"):
                parts = result.split("||")
                if len(parts) == 7:
                    print("💾 正在写入CSV...")
                    with open(csv_path, 'a', newline='', encoding='utf-8-sig') as f:
                        csv.writer(f).writerow(parts)
                    print(f"✅ 成功保存到 {csv_path}")
                else:
                    print(f"⛔ 字段数量异常（期望7列，实际{len(parts)}列），跳过保存")
            else:
                print("⛔ 包含错误信息，跳过保存")
    finally:
        print("\n✨ 程序运行结束，数据已持久化保存")

# 运行主循环
root.mainloop()