# 开发环境配置

## 后端要求
- Pythin 3.12.11
- 依赖包： 详见 requirements.txt

## 前端要求
- 现代浏览器（chrome/Firefox/Edge）
- VS Code + Live Server 扩展

## API接口规范
### 上传图片
- 端口：POS /api/upload
- 参数：image（文件）
- 返回：{"task_id":"xxx","status":"success"}

### 获取结果
- 端点：GET /api/result/<task_id>
- 返回：{
    "student_id": "oo1",
    "total_score": "85",
    "ai_feedback": "评分细则"
}