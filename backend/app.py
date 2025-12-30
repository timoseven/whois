from flask import Flask, request, jsonify, redirect
import os
import whois
import re
import time
from concurrent.futures import ThreadPoolExecutor
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import socket
import random
import logging

# 配置全局日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

# 创建Flask应用
app = Flask(__name__, static_folder='../frontend', static_url_path='/whois')

# 配置安全头
csp = {
    'default-src': ['\'self\''],
    'script-src': ['\'self\''],
    'style-src': ['\'self\'', '\'unsafe-inline\''],
    'img-src': ['\'self\''],
}

# 在开发环境中禁用HTTPS重定向
Talisman(app, 
         content_security_policy=csp,
         force_https=False)

# 配置请求速率限制
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per day", "20 per hour"],
    storage_uri="memory://",
)

# 不需要CORS，因为前后端在同一端口

# 增强的域名格式验证
def is_valid_domain(domain):
    # 基本格式验证
    pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if not bool(re.match(pattern, domain)):
        return False
    
    # 验证域名长度符合RFC标准
    if len(domain) > 253:
        return False
    
    # 验证每个标签长度不超过63个字符
    labels = domain.split('.')
    for label in labels:
        if len(label) > 63:
            return False
    
    return True

# 自定义WHOIS服务器列表，按TLD分类
WHOIS_SERVERS = {
    'com': ['whois.crsnic.net', 'whois.verisign-grs.com', 'whois.godaddy.com'],
    'net': ['whois.crsnic.net', 'whois.verisign-grs.com', 'whois.godaddy.com'],
    'org': ['whois.publicinterestregistry.org', 'whois.iana.org'],
    'info': ['whois.afilias.net', 'whois.iana.org'],
    'biz': ['whois.neustar.biz', 'whois.iana.org'],
    'us': ['whois.nic.us', 'whois.iana.org'],
    'uk': ['whois.nic.uk', 'whois.centralnic.com'],
    'de': ['whois.denic.de', 'whois.registry.DE'],
    'cn': ['whois.cnnic.net.cn', 'whois.iana.org'],
    'jp': ['whois.jprs.jp', 'whois.jic.or.jp'],
    'ru': ['whois.tcinet.ru', 'whois.nic.ru'],
    'ca': ['whois.cira.ca', 'whois.ca.fury.ca'],
    'au': ['whois.auda.org.au', 'whois.iana.org'],
    'mx': ['whois.mx', 'whois.nic.mx'],
    'nl': ['whois.domain-registry.nl', 'whois.nic.nl'],
    'in': ['whois.registry.in', 'whois.iana.org'],
    'fr': ['whois.nic.fr', 'whois.iana.org'],
    'it': ['whois.nic.it', 'whois.iana.org'],
    'es': ['whois.nic.es', 'whois.iana.org'],
    'io': ['whois.nic.io', 'whois.iana.org'],
    'ai': ['whois.nic.ai', 'whois.iana.org'],
    'co': ['whois.nic.co', 'whois.iana.org'],
    'xyz': ['whois.nic.xyz', 'whois.iana.org'],
    'top': ['whois.nic.top', 'whois.iana.org'],
    'site': ['whois.nic.site', 'whois.iana.org'],
    'online': ['whois.nic.online', 'whois.iana.org'],
    'store': ['whois.centralnic.com', 'whois.iana.org'],
    'app': ['whois.nic.google', 'whois.iana.org'],
    'dev': ['whois.nic.google', 'whois.iana.org'],
    'blog': ['whois.nic.blog', 'whois.iana.org'],
    'tech': ['whois.nic.tech', 'whois.iana.org'],
    'network': ['whois.nic.network', 'whois.iana.org'],
    'company': ['whois.nic.company', 'whois.iana.org'],
    'ltd': ['whois.nic.ltd', 'whois.iana.org'],
    'wiki': ['whois.nic.wiki', 'whois.iana.org'],
    'me': ['whois.nic.me', 'whois.iana.org'],
    'tv': ['whois.nic.tv', 'whois.iana.org'],
    'cc': ['whois.nic.cc', 'whois.iana.org'],
    'name': ['whois.nic.name', 'whois.iana.org'],
    'mobi': ['whois.dotmobiregistry.net', 'whois.iana.org'],
    'tel': ['whois.nic.tel', 'whois.iana.org'],
    'travel': ['whois.nic.travel', 'whois.iana.org'],
    'xxx': ['whois.nic.xxx', 'whois.iana.org'],
    'pro': ['whois.nic.pro', 'whois.iana.org'],
    'edu': ['whois.educause.edu', 'whois.iana.org'],
    'gov': ['whois.nic.gov', 'whois.iana.org'],
    'mil': ['whois.nic.mil', 'whois.iana.org'],
    'arpa': ['whois.iana.org', 'whois.arpa.net'],
    'int': ['whois.iana.org', 'whois.int.net'],
    'africa': ['whois.nic.africa', 'whois.iana.org'],
    'asia': ['whois.nic.asia', 'whois.iana.org'],
    'eu': ['whois.nic.eu', 'whois.iana.org'],
    'lat': ['whois.nic.lat', 'whois.iana.org'],
    'link': ['whois.nic.link', 'whois.iana.org'],
    'live': ['whois.nic.live', 'whois.iana.org'],
    'mail': ['whois.nic.mail', 'whois.iana.org'],
    'market': ['whois.nic.market', 'whois.iana.org'],
    'media': ['whois.nic.media', 'whois.iana.org'],
    'money': ['whois.nic.money', 'whois.iana.org'],
    'news': ['whois.nic.news', 'whois.iana.org'],
    'one': ['whois.nic.one', 'whois.iana.org'],
    'org.uk': ['whois.nic.uk', 'whois.centralnic.com'],
    'co.uk': ['whois.nic.uk', 'whois.centralnic.com'],
    'me.uk': ['whois.nic.uk', 'whois.centralnic.com'],
    'gov.uk': ['whois.nic.uk', 'whois.centralnic.com'],
    'ac.uk': ['whois.nic.uk', 'whois.centralnic.com'],
    'sch.uk': ['whois.nic.uk', 'whois.centralnic.com'],
    'eu.org': ['whois.eu.org', 'whois.iana.org'],
    'de.com': ['whois.centralnic.com', 'whois.iana.org'],
    'uk.com': ['whois.centralnic.com', 'whois.iana.org'],
    'us.com': ['whois.centralnic.com', 'whois.iana.org'],
    'eu.com': ['whois.centralnic.com', 'whois.iana.org'],
    'ca.com': ['whois.centralnic.com', 'whois.iana.org'],
    'org.com': ['whois.centralnic.com', 'whois.iana.org'],
    'net.com': ['whois.centralnic.com', 'whois.iana.org'],
    'biz.org': ['whois.centralnic.com', 'whois.iana.org'],
    'gov.org': ['whois.centralnic.com', 'whois.iana.org'],
    'us.org': ['whois.centralnic.com', 'whois.iana.org'],
    'uk.org': ['whois.centralnic.com', 'whois.iana.org'],
    'eu.org': ['whois.centralnic.com', 'whois.iana.org'],
    'ca.org': ['whois.centralnic.com', 'whois.iana.org'],
    'de.org': ['whois.centralnic.com', 'whois.iana.org'],
    'jp.org': ['whois.centralnic.com', 'whois.iana.org'],
    'cn.org': ['whois.centralnic.com', 'whois.iana.org'],
    'ru.org': ['whois.centralnic.com', 'whois.iana.org'],
    'au.org': ['whois.centralnic.com', 'whois.iana.org'],
    'mx.org': ['whois.centralnic.com', 'whois.iana.org'],
    'fr.org': ['whois.centralnic.com', 'whois.iana.org'],
    'it.org': ['whois.centralnic.com', 'whois.iana.org'],
    'es.org': ['whois.centralnic.com', 'whois.iana.org'],
    'in.org': ['whois.centralnic.com', 'whois.iana.org'],
    'br.org': ['whois.centralnic.com', 'whois.iana.org'],
    'at.org': ['whois.centralnic.com', 'whois.iana.org'],
    'be.org': ['whois.centralnic.com', 'whois.iana.org'],
    'ch.org': ['whois.centralnic.com', 'whois.iana.org'],
    'dk.org': ['whois.centralnic.com', 'whois.iana.org'],
    'fi.org': ['whois.centralnic.com', 'whois.iana.org'],
    'gr.org': ['whois.centralnic.com', 'whois.iana.org'],
    'hu.org': ['whois.centralnic.com', 'whois.iana.org'],
    'ie.org': ['whois.centralnic.com', 'whois.iana.org'],
    'il.org': ['whois.centralnic.com', 'whois.iana.org'],
    'is.org': ['whois.centralnic.com', 'whois.iana.org'],
    'kr.org': ['whois.centralnic.com', 'whois.iana.org'],
    'lt.org': ['whois.centralnic.com', 'whois.iana.org'],
    'lv.org': ['whois.centralnic.com', 'whois.iana.org'],
    'my.org': ['whois.centralnic.com', 'whois.iana.org'],
    'nl.org': ['whois.centralnic.com', 'whois.iana.org'],
    'no.org': ['whois.centralnic.com', 'whois.iana.org'],
    'nz.org': ['whois.centralnic.com', 'whois.iana.org'],
    'pl.org': ['whois.centralnic.com', 'whois.iana.org'],
    'pt.org': ['whois.centralnic.com', 'whois.iana.org'],
    'ro.org': ['whois.centralnic.com', 'whois.iana.org'],
    'se.org': ['whois.centralnic.com', 'whois.iana.org'],
    'sg.org': ['whois.centralnic.com', 'whois.iana.org'],
    'si.org': ['whois.centralnic.com', 'whois.iana.org'],
    'sk.org': ['whois.centralnic.com', 'whois.iana.org'],
    'th.org': ['whois.centralnic.com', 'whois.iana.org'],
    'tr.org': ['whois.centralnic.com', 'whois.iana.org'],
    'tw.org': ['whois.centralnic.com', 'whois.iana.org'],
    'za.org': ['whois.centralnic.com', 'whois.iana.org'],
    'default': ['whois.iana.org', 'whois.abuse.net', 'whois.arin.net', 'whois.ripe.net', 'whois.apnic.net', 'whois.lacnic.net']
}

# 自定义WHOIS查询函数，支持多服务器重试
def custom_whois_query(domain, whois_server=None, max_retries=3, timeout=10):
    """
    自定义WHOIS查询函数，支持多服务器重试
    domain: 要查询的域名
    whois_server: 用户指定的WHOIS服务器（可选）
    max_retries: 最大重试次数
    timeout: 超时时间（秒）
    """
    import logging
    
    logging.info(f"开始查询域名: {domain}, 使用服务器: {whois_server or 'auto'}")
    
    # 如果用户指定了服务器，优先使用
    if whois_server and whois_server != 'auto':
        servers = [whois_server]
        logging.debug(f"用户指定了WHOIS服务器，将只使用: {whois_server}")
    else:
        # 提取TLD
        tld = domain.split('.')[-1].lower()
        # 获取该TLD对应的WHOIS服务器列表
        servers = WHOIS_SERVERS.get(tld, WHOIS_SERVERS['default'])
        logging.debug(f"根据TLD '{tld}'选择的WHOIS服务器列表: {servers}")
        
        # 打乱服务器顺序，避免总是从同一个服务器开始查询
        random.shuffle(servers)
        logging.debug(f"打乱后的WHOIS服务器列表: {servers}")
    
    logging.debug(f"最终使用的WHOIS服务器列表: {servers}")
    
    # 准备尝试的服务器列表，每个服务器可能会被尝试多次
    # 如果用户指定了单个服务器，我们只使用该服务器进行所有重试
    if len(servers) == 1:
        # 单个服务器情况：在同一服务器上重试
        server = servers[0]
        for attempt in range(max_retries):
            try:
                # 指数退避策略
                retry_delay = min(1 * (2 ** attempt), 8)  # 1s, 2s, 4s, 8s...
                if attempt > 0:
                    logging.debug(f"查询 {domain} 时服务器 {server} 第 {attempt+1}/{max_retries} 次尝试，等待 {retry_delay}s")
                    time.sleep(retry_delay)
                
                # 创建socket连接
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                s.connect((server, 43))
                
                # 发送查询请求
                s.send(f"{domain}\r\n".encode())
                
                # 接收响应
                response = b""
                while True:
                    data = s.recv(4096)
                    if not data:
                        break
                    response += data
                
                # 确保socket正确关闭
                s.close()
                
                # 检查响应是否为空
                if not response:
                    logging.warning(f"查询 {domain} 时服务器 {server} 返回空响应 (尝试 {attempt+1}/{max_retries})")
                    continue
                
                # 检查响应是否包含错误信息
                response_str = response.decode('utf-8', 'replace')
                if any(error_keyword in response_str.lower() for error_keyword in [
                    'error', 'failed', 'limit exceeded', 'too many requests',
                    'blocked', 'access denied', 'permission denied'
                ]):
                    logging.warning(f"查询 {domain} 时服务器 {server} 返回错误响应: {response_str[:100]}... (尝试 {attempt+1}/{max_retries})")
                    continue
                
                # 返回解析后的结果
                try:
                    return whois.parser.WhoisEntry.load(domain, response_str)
                except Exception as parse_error:
                    logging.warning(f"查询 {domain} 时解析服务器 {server} 的响应失败: {parse_error} (尝试 {attempt+1}/{max_retries})")
                    # 解析失败继续尝试
                    continue
            except socket.timeout:
                logging.warning(f"查询 {domain} 时服务器 {server} 超时 (尝试 {attempt+1}/{max_retries})")
                if s:
                    s.close()
                # 超时后继续尝试下一次
            except socket.error as e:
                error_msg = str(e).lower()
                if 'connection refused' in error_msg:
                    logging.warning(f"查询 {domain} 时服务器 {server} 拒绝连接 (尝试 {attempt+1}/{max_retries})")
                elif 'network is unreachable' in error_msg:
                    logging.warning(f"查询 {domain} 时网络不可达 (尝试 {attempt+1}/{max_retries})")
                else:
                    logging.warning(f"查询 {domain} 时服务器 {server} 连接失败: {e} (尝试 {attempt+1}/{max_retries})")
                if s:
                    s.close()
            except Exception as e:
                logging.warning(f"查询 {domain} 时服务器 {server} 发生未知错误: {e} (尝试 {attempt+1}/{max_retries})")
                if s:
                    s.close()
    else:
        # 多个服务器情况：每次重试尝试不同的服务器
        total_attempts = len(servers) * max_retries
        attempt_count = 0
        
        while attempt_count < total_attempts:
            # 计算当前应该使用的服务器索引
            server_index = attempt_count % len(servers)
            server = servers[server_index]
            attempt_count += 1
            
            try:
                # 指数退避策略
                retry_delay = min(1 * (2 ** ((attempt_count - 1) // len(servers))), 8)  # 1s, 2s, 4s, 8s...
                if attempt_count > 1:
                    logging.debug(f"查询 {domain} 时服务器 {server} 第 {attempt_count}/{total_attempts} 次尝试，等待 {retry_delay}s")
                    time.sleep(retry_delay)
                
                # 创建socket连接
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                s.connect((server, 43))
                
                # 发送查询请求
                s.send(f"{domain}\r\n".encode())
                
                # 接收响应
                response = b""
                while True:
                    data = s.recv(4096)
                    if not data:
                        break
                    response += data
                
                # 确保socket正确关闭
                s.close()
                
                # 检查响应是否为空
                if not response:
                    logging.warning(f"查询 {domain} 时服务器 {server} 返回空响应 (尝试 {attempt_count}/{total_attempts})")
                    continue
                
                # 检查响应是否包含错误信息
                response_str = response.decode('utf-8', 'replace')
                if any(error_keyword in response_str.lower() for error_keyword in [
                    'error', 'failed', 'limit exceeded', 'too many requests',
                    'blocked', 'access denied', 'permission denied'
                ]):
                    logging.warning(f"查询 {domain} 时服务器 {server} 返回错误响应: {response_str[:100]}... (尝试 {attempt_count}/{total_attempts})")
                    continue
                
                # 返回解析后的结果
                try:
                    return whois.parser.WhoisEntry.load(domain, response_str)
                except Exception as parse_error:
                    logging.warning(f"查询 {domain} 时解析服务器 {server} 的响应失败: {parse_error} (尝试 {attempt_count}/{total_attempts})")
                    # 解析失败继续尝试
                    continue
            except socket.timeout:
                logging.warning(f"查询 {domain} 时服务器 {server} 超时 (尝试 {attempt_count}/{total_attempts})")
                if s:
                    s.close()
                # 超时后尝试下一个服务器
            except socket.error as e:
                error_msg = str(e).lower()
                if 'connection refused' in error_msg:
                    logging.warning(f"查询 {domain} 时服务器 {server} 拒绝连接 (尝试 {attempt_count}/{total_attempts})")
                elif 'network is unreachable' in error_msg:
                    logging.warning(f"查询 {domain} 时网络不可达 (尝试 {attempt_count}/{total_attempts})")
                else:
                    logging.warning(f"查询 {domain} 时服务器 {server} 连接失败: {e} (尝试 {attempt_count}/{total_attempts})")
                if s:
                    s.close()
            except Exception as e:
                logging.warning(f"查询 {domain} 时服务器 {server} 发生未知错误: {e} (尝试 {attempt_count}/{total_attempts})")
                if s:
                    s.close()
    
    # 所有服务器都尝试失败，使用默认的whois库作为最后的尝试
    logging.warning(f"所有自定义服务器查询 {domain} 失败，尝试使用默认whois库")
    try:
        return whois.whois(domain)
    except Exception as e:
        logging.error(f"默认whois库查询 {domain} 也失败: {e}")
        raise e

# 获取域名完整信息（可用性、注册时间、过期时间等）
def get_domain_info(domain, whois_server=None):
    try:
        import logging
        # 执行WHOIS查询（使用自定义多服务器查询函数）
        w = custom_whois_query(domain, whois_server=whois_server)
        
        logging.debug(f"查询域名 {domain} 完整信息，使用服务器 {whois_server}")
        logging.debug(f"WHOIS结果对象: {type(w)}, 包含domain_name: {hasattr(w, 'domain_name') and w.domain_name}")
        
        # 初始化结果
        result = {
            'available': True,
            'creation_date': None,
            'expiration_date': None
        }
        
        # 首先检查原始文本内容，这是最可靠的
        if hasattr(w, 'text') and isinstance(w.text, list):
            text_content = '\n'.join(w.text).lower()
            # 检查是否包含未注册的关键词
            if any(keyword in text_content for keyword in [
                'not found', 'no match', 'no data found', 'available', 
                'does not exist', 'not registered', 'invalid domain',
                'no such domain', 'domain not found', 'not registered'
            ]):
                logging.debug(f"域名 {domain} 未注册: 在原始文本中找到未注册关键词")
                return result
            # 检查是否包含已注册的关键词
            if any(keyword in text_content for keyword in [
                'registered', 'domain name:', 'registrar:', 'creation date:',
                'expiration date:', 'status:', 'name servers:'
            ]):
                result['available'] = False
        
        # 针对不同WHOIS服务器的特殊处理
        if whois_server and 'iana.org' in whois_server:
            # IANA服务器返回非常简洁的信息，通常只包含"domain: EXAMPLE.COM"表示已注册
            if hasattr(w, 'text') and isinstance(w.text, list):
                text_content = '\n'.join(w.text)
                if domain.lower() in text_content.lower() and 'domain:' in text_content.lower():
                    logging.debug(f"域名 {domain} 已注册: IANA服务器返回了域名信息")
                    result['available'] = False
        
        # 传统的字段检查，作为补充
        has_registration_info = False
        
        # 检查域名名称
        if hasattr(w, 'domain_name') and w.domain_name:
            has_registration_info = True
            logging.debug(f"找到域名名称: {w.domain_name}")
        
        # 检查注册商信息
        if hasattr(w, 'registrar') and w.registrar:
            has_registration_info = True
            logging.debug(f"找到注册商: {w.registrar}")
        
        # 检查创建日期
        if hasattr(w, 'creation_date') and w.creation_date:
            has_registration_info = True
            result['creation_date'] = w.creation_date
            logging.debug(f"找到创建日期: {w.creation_date}")
        
        # 检查过期日期
        if hasattr(w, 'expiration_date') and w.expiration_date:
            has_registration_info = True
            result['expiration_date'] = w.expiration_date
            logging.debug(f"找到过期日期: {w.expiration_date}")
        
        # 检查状态信息
        if hasattr(w, 'status') and w.status:
            status_str = str(w.status).lower()
            if any(keyword in status_str for keyword in ['available', 'not found', 'no match']):
                logging.debug(f"域名 {domain} 未注册: 状态包含未注册关键词")
                result['available'] = True
                return result
            has_registration_info = True
            logging.debug(f"找到状态信息: {w.status}")
        
        # 如果有任何注册信息，认为域名已注册
        if has_registration_info:
            logging.debug(f"域名 {domain} 已注册: 找到注册信息")
            result['available'] = False
        
        # 如果没有任何注册信息，保守处理为已注册
        if not result['available'] and (result['creation_date'] is None or result['expiration_date'] is None):
            logging.debug(f"域名 {domain} 已注册但缺少日期信息")
        
        return result
    except Exception as e:
        # 捕获异常，可能是域名未注册或其他错误
        import logging
        logging.debug(f"查询域名 {domain} 信息时发生异常: {e}")
        # 常见的未注册域名异常消息通常包含特定关键词
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in [
            'not found', 'no match', 'no data found', 'available', 
            'does not exist', 'not registered', 'invalid domain',
            'no such domain', 'domain not found'
        ]):
            logging.debug(f"域名 {domain} 未注册: 异常消息包含未注册关键词")
            return {'available': True, 'creation_date': None, 'expiration_date': None}
        # 其他异常可能是网络错误或服务器问题，默认返回False（保守处理）
        logging.debug(f"域名 {domain} 状态不确定: 发生异常且不包含未注册关键词，保守处理为已注册")
        return {'available': False, 'creation_date': None, 'expiration_date': None}

# 检查域名是否可注册（保持向后兼容）
def check_domain_availability(domain, whois_server=None):
    # 调用新的函数并返回可用性状态
    result = get_domain_info(domain, whois_server)
    return result['available']

# WHOIS查询API端点（单个域名）
@app.route('/whois/api/whois', methods=['POST'])
def whois_query():
    try:
        data = request.get_json()
        
        # 检查请求数据是否包含域名
        if not data or 'domain' not in data:
            return jsonify({'error': '缺少域名参数'}), 400
        
        domain = data['domain'].strip()
        
        # 获取用户选择的WHOIS服务器（如果有）
        whois_server = data.get('whois_server', 'auto')
        logging.debug(f"接收到的WHOIS服务器参数: {whois_server}")
        
        # 验证域名格式
        if not is_valid_domain(domain):
            return jsonify({'error': '无效的域名格式'}), 400
        
        # 执行WHOIS查询（使用自定义多服务器查询函数）
        try:
            w = custom_whois_query(domain, whois_server=whois_server)
            # 将结果转换为字符串格式
            whois_result = format_whois_result(w)
            # 获取完整的域名信息
            domain_info = get_domain_info(domain, whois_server=whois_server)
            return jsonify({
                'whois_data': whois_result,
                'available': domain_info['available'],
                'creation_date': domain_info['creation_date'],
                'expiration_date': domain_info['expiration_date']
            })
        except Exception as e:
            # 尝试直接检查可用性
            domain_info = get_domain_info(domain, whois_server=whois_server)
            # 不暴露敏感错误信息给用户
            return jsonify({
                'error': 'WHOIS查询失败，请稍后重试',
                'available': domain_info['available'],
                'creation_date': domain_info['creation_date'],
                'expiration_date': domain_info['expiration_date']
            }), 500
            
    except Exception as e:
        # 不暴露敏感错误信息给用户
        return jsonify({'error': '服务器错误，请稍后重试'}), 500

# 批量WHOIS查询API端点
@app.route('/whois/api/whois-batch', methods=['POST'])
def whois_batch_query():
    try:
        data = request.get_json()
        
        # 检查请求数据是否包含域名列表
        if not data or 'domains' not in data or not isinstance(data['domains'], list):
            return jsonify({'error': '缺少有效的域名列表参数'}), 400
        
        domains = data['domains']
        
        # 获取用户选择的WHOIS服务器（如果有）
        whois_server = data.get('whois_server', 'auto')
        logging.debug(f"接收到的批量查询WHOIS服务器参数: {whois_server}")
        
        # 验证域名数量限制
        if len(domains) > 100:
            return jsonify({'error': '单次查询域名数量不能超过100个'}), 400
        
        # 验证每个域名的格式
        for domain in domains:
            if not isinstance(domain, str) or not is_valid_domain(domain.strip()):
                return jsonify({'error': '无效的域名格式'}), 400
        
        # 执行批量查询
        results = {}
        
        # 使用线程池并发查询
        with ThreadPoolExecutor(max_workers=10) as executor:
            # 提交所有查询任务
            future_to_domain = {executor.submit(get_domain_info, domain.strip(), whois_server=whois_server): domain for domain in domains}
            
            # 收集结果
            for future in future_to_domain:
                domain = future_to_domain[future]
                try:
                    # 添加延迟避免请求过于频繁
                    time.sleep(0.1)
                    domain_info = future.result()
                    results[domain] = domain_info
                except Exception as e:
                    # 如果单个域名查询失败，设置为False（保守处理），不暴露具体错误
                    results[domain] = {'available': False, 'creation_date': None, 'expiration_date': None, 'error': '查询失败'}
        
        return jsonify(results)
        
    except Exception as e:
        # 不暴露敏感错误信息给用户
        return jsonify({'error': '服务器错误，请稍后重试'}), 500

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
@app.route('/whois/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

# 首页路由，提供index.html
@app.route('/whois/')
def index():
    return app.send_static_file('index.html')

# 处理其他静态文件
@app.route('/whois/<path:path>')
def static_files(path):
    if path.endswith(('.js', '.css', '.html', '.json', '.png', '.jpg', '.jpeg', '.gif', '.ico')):
        return app.send_static_file(path)
    else:
        return app.send_static_file('index.html')  # SPA路由支持

# 根路径重定向到whois子路径
@app.route('/')
def root():
    return redirect('/whois/')

if __name__ == '__main__':
    # 使用8000端口作为统一访问端口
    print("服务启动在: http://localhost:8000/whois")
    # 生产环境禁用debug模式
    app.run(debug=False, host='0.0.0.0', port=8000)