import json

# 你的 JSON 文件路径
json_path = r"D:\Project\Automatic-Grading\output\res.json"          # 可以改成你的路径，比如 "D:\\Project\\Automatic-Grading\\data.json"
cpp_output_path = "output.cpp"   # 输出的 C++ 文件路径

# 读取 JSON
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取 rec_texts 部分
rec_texts = data.get("rec_texts", [])

# 写入 cpp 文件
with open(cpp_output_path, 'w', encoding='utf-8') as f:
    for line in rec_texts:
        f.write(line + "\n")

print(f"✅ 已生成 C++ 文件：{cpp_output_path}")
