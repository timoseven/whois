# WHOIS查询工具

一个简单的WHOIS查询单页面应用，前端使用HTML+JavaScript，后端使用Python Flask实现。

## 功能特性

- 域名WHOIS信息查询
- 美观的用户界面
- 实时加载状态显示
- 本地查询历史记录
- 响应式设计，支持各种设备

## 技术栈

- **前端**: HTML5, CSS3, JavaScript (纯原生)
- **后端**: Python 3, Flask
- **依赖**: python-whois, flask-cors

## 项目结构

```
whois/
├── frontend/           # 前端代码
│   ├── index.html      # 主页面
│   └── app.js          # JavaScript逻辑
├── backend/            # 后端代码
│   ├── app.py          # Flask应用
│   └── requirements.txt # Python依赖
├── .gitignore          # Git忽略文件
└── README.md           # 项目说明
```

## 安装说明

### 后端安装

1. 进入后端目录
```bash
cd whois/backend
```

2. 创建虚拟环境（推荐）
```bash
python3 -m venv venv
```

3. 激活虚拟环境
```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

4. 安装依赖
```bash
pip install -r requirements.txt
```

### 前端

前端不需要特殊安装，只需确保后端服务正常运行即可。

## 使用方法

1. 启动后端服务
```bash
cd whois/backend
python app.py
```

2. 打开前端页面
   - 直接在浏览器中打开 `whois/frontend/index.html` 文件
   - 或者使用任何静态文件服务器托管前端文件

3. 在输入框中输入域名（例如：example.com），然后点击查询按钮或按回车键

4. 查看WHOIS查询结果

5. 查询历史会自动保存在浏览器的本地存储中

## API端点

- **POST /api/whois**: 执行WHOIS查询
  - 请求体: `{"domain": "example.com"}`
  - 响应: `{"whois_data": "格式化的WHOIS信息"}` 或 `{"error": "错误信息"}`

- **GET /health**: 健康检查端点
  - 响应: `{"status": "healthy"}`

## 注意事项

- 后端服务默认运行在 http://localhost:5000
- 确保Python版本 >= 3.6
- 某些域名可能由于隐私保护设置无法获取完整的WHOIS信息
- 查询历史仅保存在浏览器本地，清除浏览器数据会导致历史记录丢失

## 许可证

MIT