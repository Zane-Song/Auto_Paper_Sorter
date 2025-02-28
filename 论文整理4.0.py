import re
import requests
import json
import csv
import os  # 用于文件存在性检查

def extract_next_record(file_path):
    """
    从文件中提取第一条记录（记录之间以空行分隔），
    提取后将该记录从文件中删除。
    """
    if not os.path.exists(file_path):
        return None

    # 读取整个文件内容，并去除首尾空白
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        content = f.read().strip()
    if not content:
        return None

    # 使用正则以一个或多个空白行作为分隔符
    records = re.split(r'\n\s*\n', content)
    record = records[0].strip()

    # 组合剩余的记录，写回文件
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
            print("response.text的内容为", response.text)
            content = json.loads(response.text)['choices'][0]['message']['content']
            print(content)
            # 确保返回的内容严格使用“||”分隔
            return content.strip()
        else:
            print(f"❌ API返回错误状态码: {response.status_code}")
            return f"ERROR {response.status_code}"
    except Exception as e:
        print(f"⚠️ 发生网络异常: {str(e)}")
        return f"ERROR {str(e)}"

def main():
    # 指定存储论文记录的txt文件路径（请确保文件格式符合约定：记录以空行分隔）
    txt_path = 'savedrecs.txt'
    csv_path = 'output.csv'

    # 初始化CSV文件，如果不存在则创建，并写入表头
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
        # 循环提取txt文件中的记录，直至文件内容处理完毕
        while True:
            record = extract_next_record(txt_path)
            if record is None:
                print("🎉 无更多记录需要处理，程序结束")
                break

            print("\n📝 正在处理记录：")
            print(record)

            # 这里将提取到的记录内容当做输入传给处理函数
            result = process_abstract(record)
            print(f"⚙️ 处理结果: {result}")

            # 确保处理结果分割后有7个字段
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

if __name__ == "__main__":
    main()
