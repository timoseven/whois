from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import whois
import re
import os

# 创建Flask应用，设置静态文件夹路径为前端目录
app = Flask(__name__, 
            static_folder='../frontend',
            static_url_path='/'
)
CORS(app)  # 启用CORS支持所有跨域请求

# 简单的域名格式验证
def is_valid_domain(domain):
    pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))

# WHOIS查询API端点
@app.route('/api/whois', methods=['POST'])
def whois_query():
    try:
        data = request.get_json()
        
        # 检查请求数据是否包含域名
        if not data or 'domain' not in data:
            return jsonify({'error': '缺少域名参数'}), 400
        
        domain = data['domain'].strip()
        
        # 验证域名格式
        if not is_valid_domain(domain):
            return jsonify({'error': '无效的域名格式'}), 400
        
        # 执行WHOIS查询
        try:
            w = whois.whois(domain)
            # 将结果转换为字符串格式
            whois_result = format_whois_result(w)
            return jsonify({'whois_data': whois_result})
        except Exception as e:
            return jsonify({'error': f'WHOIS查询失败: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

# 格式化WHOIS结果
def format_whois_result(whois_data):
    result_lines = []
    
    # 提取主要信息
    fields = [
        ('域名', 'domain_name'),
        ('注册商', 'registrar'),
        ('创建日期', 'creation_date'),
        ('过期日期', 'expiration_date'),
        ('更新日期', 'updated_date'),
        ('名称服务器', 'name_servers'),
        ('所有者', 'registrant_name'),
        ('邮箱', 'emails'),
        ('状态', 'status'),
        ('DNSSEC', 'dnssec')
    ]
    
    for label, field in fields:
        value = getattr(whois_data, field, None)
        if value:
            # 处理列表类型的值
            if isinstance(value, list):
                # 处理日期列表
                if all(isinstance(item, whois.parser.WhoisEntry) for item in value):
                    # 对于嵌套的WhoisEntry，递归格式化
                    for i, item in enumerate(value, 1):
                        result_lines.append(f"\n--- {label} {i} ---")
                        result_lines.append(format_whois_result(item))
                else:
                    result_lines.append(f"{label}: {', '.join(str(v) for v in value)}")
            # 处理WhoisEntry对象
            elif isinstance(value, whois.parser.WhoisEntry):
                result_lines.append(f"\n--- {label} ---")
                result_lines.append(format_whois_result(value))
            else:
                result_lines.append(f"{label}: {str(value)}")
    
    # 如果没有结构化数据，尝试使用原始文本
    if not result_lines and hasattr(whois_data, 'text') and whois_data.text:
        return '\n'.join(whois_data.text)
    
    return '\n'.join(result_lines) if result_lines else '未找到WHOIS信息'

# 健康检查端点
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

# 根路径路由 - 提供前端index.html页面
@app.route('/', methods=['GET'])
def index():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)