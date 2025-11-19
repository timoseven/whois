from flask import Flask, request, jsonify, send_from_directory
import os
import whois
import re
import time
from concurrent.futures import ThreadPoolExecutor

# 创建Flask应用
app = Flask(__name__, static_folder='../frontend', static_url_path='/')
# 不需要CORS，因为前后端在同一端口

# 简单的域名格式验证
def is_valid_domain(domain):
    pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))

# 检查域名是否可注册
def check_domain_availability(domain):
    try:
        # 执行WHOIS查询
        w = whois.whois(domain)
        
        # 判断域名是否可注册的逻辑
        # 1. 检查是否有域名名称 (有些未注册的域名会返回空的domain_name)
        if not w.domain_name:
            return True
        
        # 2. 检查是否有注册商信息
        if not w.registrar:
            return True
        
        # 3. 检查是否有创建日期
        if not w.creation_date:
            return True
        
        # 4. 检查状态信息，有些未注册的域名可能返回特定状态
        if hasattr(w, 'status') and w.status:
            # 某些状态可能表明域名未注册或可重新注册
            status_str = str(w.status).lower()
            if any(keyword in status_str for keyword in ['available', 'not found', 'no match']):
                return True
        
        # 5. 检查是否有多个不同的结果（有时会有多个WHOIS服务器返回结果）
        if isinstance(w.domain_name, list):
            # 如果列表中的所有元素都相同，可能是重复的结果
            if all(d == w.domain_name[0] for d in w.domain_name):
                return False
            # 否则可能是未找到有效信息
            return True
        
        # 默认认为已注册
        return False
    except Exception as e:
        # 捕获异常，可能是域名未注册或其他错误
        # 常见的未注册域名异常消息通常包含特定关键词
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in [
            'not found', 'no match', 'no data found', 'available', 
            'does not exist', 'not registered', 'invalid domain'
        ]):
            return True
        # 其他异常可能是网络错误或服务器问题，默认返回False（保守处理）
        return False

# WHOIS查询API端点（单个域名）
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
            # 同时检查是否可注册
            available = check_domain_availability(domain)
            return jsonify({'whois_data': whois_result, 'available': available})
        except Exception as e:
            # 尝试直接检查可用性
            available = check_domain_availability(domain)
            return jsonify({'error': f'WHOIS查询失败: {str(e)}', 'available': available}), 500
            
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

# 批量WHOIS查询API端点
@app.route('/api/whois-batch', methods=['POST'])
def whois_batch_query():
    try:
        data = request.get_json()
        
        # 检查请求数据是否包含域名列表
        if not data or 'domains' not in data or not isinstance(data['domains'], list):
            return jsonify({'error': '缺少有效的域名列表参数'}), 400
        
        domains = data['domains']
        
        # 验证域名数量限制
        if len(domains) > 100:
            return jsonify({'error': '单次查询域名数量不能超过100个'}), 400
        
        # 验证每个域名的格式
        for domain in domains:
            if not isinstance(domain, str) or not is_valid_domain(domain.strip()):
                return jsonify({'error': f'无效的域名格式: {domain}'}), 400
        
        # 执行批量查询
        results = {}
        
        # 使用线程池并发查询
        with ThreadPoolExecutor(max_workers=10) as executor:
            # 提交所有查询任务
            future_to_domain = {executor.submit(check_domain_availability, domain.strip()): domain for domain in domains}
            
            # 收集结果
            for future in future_to_domain:
                domain = future_to_domain[future]
                try:
                    # 添加延迟避免请求过于频繁
                    time.sleep(0.1)
                    available = future.result()
                    results[domain] = {'available': available}
                except Exception as e:
                    # 如果单个域名查询失败，设置为False（保守处理）
                    results[domain] = {'available': False, 'error': str(e)}
        
        return jsonify(results)
        
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

# 首页路由，提供index.html
@app.route('/')
def index():
    return app.send_static_file('index.html')

# 处理其他静态文件
@app.route('/<path:path>')
def static_files(path):
    if path.endswith(('.js', '.css', '.html', '.json', '.png', '.jpg', '.jpeg', '.gif', '.ico')):
        return app.send_static_file(path)
    else:
        return app.send_static_file('index.html')  # SPA路由支持

if __name__ == '__main__':
    # 使用8000端口作为统一访问端口
    print("服务启动在: http://localhost:8000")
    app.run(debug=True, host='0.0.0.0', port=8000)