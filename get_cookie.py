#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import platform
from dotenv import load_dotenv, set_key
import argparse

# 加载已有的环境变量
load_dotenv()

# 定义常量
PLATFORMS = {
    "boss": {
        "name": "BOSS直聘",
        "url": "https://www.zhipin.com/web/user/?ka=header-login",
        "description": "BOSS直聘是一个知名的招聘平台，提供各种职位的招聘信息。",
        "domains": ["www.zhipin.com"],
        "env_key": "BOSS_COOKIE"
    },
    "lagou": {
        "name": "拉勾网",
        "url": "https://passport.lagou.com/login/login.html",
        "description": "拉勾网是一个专注于互联网行业的招聘平台。",
        "domains": ["www.lagou.com", "passport.lagou.com"],
        "env_key": "LAGOU_COOKIE"
    },
    # 可以根据需要添加更多平台
}

class CookieHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求，提供Cookie提取页面"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = self._generate_html()
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')
    
    def do_POST(self):
        """处理POST请求，接收并保存Cookie"""
        if self.path == '/save_cookie':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            cookie_data = json.loads(post_data)
            
            platform = cookie_data.get('platform', '')
            cookie = cookie_data.get('cookie', '')
            
            result = self._save_cookie(platform, cookie)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = json.dumps({"success": True, "message": result})
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')
    
    def _save_cookie(self, platform, cookie):
        """保存Cookie到.env文件"""
        if platform in PLATFORMS:
            env_key = PLATFORMS[platform]['env_key']
            set_key('.env', env_key, cookie)
            return f"成功保存{PLATFORMS[platform]['name']}的Cookie到.env文件"
        return "未知平台"
    
    def _generate_html(self):
        """生成Cookie提取页面的HTML"""
        platform_options = '\n'.join([
            f'<option value="{key}">{platform["name"]}</option>'
            for key, platform in PLATFORMS.items()
        ])
        
        platform_tabs = '\n'.join([
            f'''
            <div class="tab-pane fade" id="{key}-tab" role="tabpanel">
                <div class="card mt-3">
                    <div class="card-body">
                        <h5 class="card-title">{platform["name"]}</h5>
                        <p class="card-text">{platform["description"]}</p>
                        <button class="btn btn-primary" onclick="openLoginPage('{key}')">
                            打开{platform["name"]}登录页面
                        </button>
                    </div>
                </div>
                <div class="card mt-3">
                    <div class="card-body">
                        <h5 class="card-title">获取Cookie步骤</h5>
                        <ol>
                            <li>点击上方按钮，在新窗口中打开{platform["name"]}登录页面</li>
                            <li>使用您的账号登录</li>
                            <li>登录成功后，按F12打开开发者工具</li>
                            <li>在开发者工具中，选择"应用"或"Application"标签</li>
                            <li>在左侧的"存储"栏中，展开"Cookies"，选择{platform["domains"][0]}</li>
                            <li>右键点击列表，选择"复制全部"或使用Ctrl+A全选后复制</li>
                            <li>回到本页面，将复制的内容粘贴到下方输入框中</li>
                            <li>点击"保存Cookie"按钮</li>
                        </ol>
                    </div>
                </div>
            </div>
            '''
            for key, platform in PLATFORMS.items()
        ])
        
        platform_buttons = '\n'.join([
            f'''
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="{key}-tab-btn" data-bs-toggle="tab" 
                        data-bs-target="#{key}-tab" type="button" role="tab"
                        aria-controls="{key}-tab" aria-selected="false">
                    {platform["name"]}
                </button>
            </li>
            '''
            for key, platform in PLATFORMS.items()
        ])
        
        html = f'''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>智能求职助手 - Cookie提取工具</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{ padding: 20px; }}
                .cookie-input {{ min-height: 100px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="row">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-header bg-primary text-white">
                                <h3>智能求职助手 - Cookie提取工具</h3>
                            </div>
                            <div class="card-body">
                                <div class="alert alert-info">
                                    <p><strong>使用说明：</strong>此工具可以帮助您从各招聘网站获取Cookie并保存到配置文件中。</p>
                                    <p>Cookie仅保存在本地，不会上传到任何服务器。</p>
                                </div>
                                
                                <!-- 平台选项卡 -->
                                <ul class="nav nav-tabs" id="platformTabs" role="tablist">
                                    {platform_buttons}
                                </ul>
                                
                                <!-- 选项卡内容 -->
                                <div class="tab-content" id="platformTabContent">
                                    {platform_tabs}
                                </div>
                                
                                <!-- Cookie输入区域 -->
                                <div class="card mt-3">
                                    <div class="card-body">
                                        <h5 class="card-title">保存Cookie</h5>
                                        <div class="mb-3">
                                            <label for="platformSelect" class="form-label">选择平台</label>
                                            <select class="form-select" id="platformSelect">
                                                {platform_options}
                                            </select>
                                        </div>
                                        <div class="mb-3">
                                            <label for="cookieInput" class="form-label">粘贴Cookie</label>
                                            <textarea class="form-control cookie-input" id="cookieInput" rows="5" placeholder="请粘贴Cookie..."></textarea>
                                        </div>
                                        <button class="btn btn-success" onclick="saveCookie()">保存Cookie</button>
                                    </div>
                                </div>
                                
                                <!-- 状态显示 -->
                                <div id="statusArea" class="mt-3" style="display: none;">
                                    <div class="alert alert-success" role="alert" id="statusMessage"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // 页面加载时激活第一个选项卡
                document.addEventListener('DOMContentLoaded', function() {{
                    // 获取第一个选项卡按钮并点击
                    const firstTab = document.querySelector('#platformTabs .nav-link');
                    if (firstTab) {{
                        firstTab.classList.add('active');
                        const tabId = firstTab.getAttribute('data-bs-target');
                        const tabPane = document.querySelector(tabId);
                        if (tabPane) {{
                            tabPane.classList.add('show', 'active');
                        }}
                    }}
                }});
                
                // 打开登录页面
                function openLoginPage(platform) {{
                    const platforms = {json.dumps(PLATFORMS)};
                    if (platforms[platform]) {{
                        window.open(platforms[platform].url, '_blank');
                    }}
                }}
                
                // 保存Cookie
                function saveCookie() {{
                    const platform = document.getElementById('platformSelect').value;
                    const cookie = document.getElementById('cookieInput').value.trim();
                    
                    if (!cookie) {{
                        alert('请粘贴Cookie');
                        return;
                    }}
                    
                    fetch('/save_cookie', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{ platform, cookie }})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success) {{
                            const statusArea = document.getElementById('statusArea');
                            const statusMessage = document.getElementById('statusMessage');
                            statusMessage.textContent = data.message;
                            statusArea.style.display = 'block';
                            
                            // 清空输入框
                            document.getElementById('cookieInput').value = '';
                            
                            // 5秒后隐藏状态信息
                            setTimeout(() => {{
                                statusArea.style.display = 'none';
                            }}, 5000);
                        }}
                    }})
                    .catch(error => {{
                        console.error('Error:', error);
                        alert('保存失败：' + error);
                    }});
                }}
            </script>
        </body>
        </html>
        '''
        return html

def start_server(port=8000):
    """启动HTTP服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, CookieHandler)
    print(f"Cookie提取服务器已启动，监听端口: {port}")
    print(f"请在浏览器中访问: http://localhost:{port}")
    
    # 自动打开浏览器
    webbrowser.open(f'http://localhost:{port}')
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    
    httpd.server_close()
    print("服务器已关闭")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Cookie提取工具')
    parser.add_argument('--port', type=int, default=8000, help='服务器端口号')
    args = parser.parse_args()
    
    # 欢迎信息
    print("="*50)
    print("智能求职助手 - Cookie提取工具")
    print("="*50)
    print("本工具帮助您从各招聘网站获取Cookie，并自动保存到.env配置文件")
    print("注意: Cookie包含您的登录凭证，请勿分享给他人")
    
    # 启动服务器
    start_server(args.port)

if __name__ == "__main__":
    main() 