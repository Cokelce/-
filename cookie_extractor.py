#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import logging
import getpass
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv, set_key

# 设置日志
logger = logging.getLogger(__name__)

class CookieExtractor:
    """自动提取各平台Cookie的工具类"""
    
    def __init__(self, headless=False):
        """
        初始化Cookie提取器
        
        参数:
        - headless: 是否使用无头模式（不显示浏览器窗口）
        """
        self.headless = headless
        self.browser = None
        
        # 确保.env文件存在
        if not os.path.exists('.env'):
            with open('.env', 'w', encoding='utf-8') as f:
                f.write('# 自动生成的环境变量文件\n')
    
    def initialize_browser(self):
        """初始化浏览器"""
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 添加一个常见的 User-Agent
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36')
        
        logger.info("正在启动浏览器...")
        self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.browser.maximize_window()
        logger.info("浏览器启动成功")
    
    def close_browser(self):
        """关闭浏览器"""
        if self.browser:
            self.browser.quit()
            self.browser = None
            logger.info("浏览器已关闭")
    
    def extract_boss_cookie(self):
        """
        提取Boss直聘的Cookie
        
        返回:
        - cookie_str: Cookie字符串
        - user_id: 用户ID
        """
        if not self.browser:
            self.initialize_browser()
        
        try:
            # 打开Boss直聘登录页面
            self.browser.get('https://www.zhipin.com/web/user/?ka=header-login')
            logger.info("已打开Boss直聘登录页面，请在浏览器中完成登录...")
            
            # 等待用户手动登录
            print("\n========== Boss直聘登录引导 ==========")
            print("1. 在打开的浏览器窗口中，请使用扫码或其他方式登录Boss直聘")
            print("2. 登录成功后，系统将自动提取Cookie")
            print("3. 请不要关闭浏览器窗口，等待提示成功")
            print("========================================\n")
            
            # 等待登录成功，通常可以通过检测某个仅在登录后才存在的元素
            WebDriverWait(self.browser, 300).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.user-nav'))
            )
            
            # 登录成功后，提取Cookie
            cookies = self.browser.get_cookies()
            cookie_str = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
            
            # 提取用户ID（可能需要根据实际情况调整）
            # 方法1: 从URL中提取
            try:
                self.browser.get('https://www.zhipin.com/web/geek/recommend')
                time.sleep(2)
                current_url = self.browser.current_url
                # 示例URL: https://www.zhipin.com/web/geek/recommend?userId=12345678
                user_id = current_url.split('userId=')[1].split('&')[0] if 'userId=' in current_url else None
            except:
                # 方法2: 如果URL中没有，尝试从页面元素或localStorage中提取
                user_id = self.browser.execute_script("""
                    try {
                        return localStorage.getItem('userId') || '';
                    } catch (e) {
                        return '';
                    }
                """)
            
            logger.info("成功提取Boss直聘Cookie")
            print("\n✅ Boss直聘登录成功，已提取Cookie")
            
            return cookie_str, user_id
        except Exception as e:
            logger.error(f"提取Boss直聘Cookie失败: {str(e)}")
            print(f"\n❌ 提取Boss直聘Cookie失败: {str(e)}")
            return None, None
    
    def extract_zhilian_cookie(self):
        """提取智联招聘的Cookie"""
        if not self.browser:
            self.initialize_browser()
        
        try:
            # 打开智联招聘登录页面
            self.browser.get('https://passport.zhaopin.com/login')
            logger.info("已打开智联招聘登录页面，请在浏览器中完成登录...")
            
            # 等待用户手动登录
            print("\n========== 智联招聘登录引导 ==========")
            print("1. 在打开的浏览器窗口中，请使用扫码或其他方式登录智联招聘")
            print("2. 登录成功后，系统将自动提取Cookie")
            print("3. 请不要关闭浏览器窗口，等待提示成功")
            print("========================================\n")
            
            # 等待登录成功，通常可以通过检测某个仅在登录后才存在的元素
            WebDriverWait(self.browser, 300).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.navbar-nav'))
            )
            
            # 登录成功后，提取Cookie
            cookies = self.browser.get_cookies()
            cookie_str = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
            
            logger.info("成功提取智联招聘Cookie")
            print("\n✅ 智联招聘登录成功，已提取Cookie")
            
            return cookie_str
        except Exception as e:
            logger.error(f"提取智联招聘Cookie失败: {str(e)}")
            print(f"\n❌ 提取智联招聘Cookie失败: {str(e)}")
            return None
    
    def extract_qiancheng_cookie(self):
        """提取前程无忧的Cookie"""
        if not self.browser:
            self.initialize_browser()
        
        try:
            # 打开前程无忧登录页面
            self.browser.get('https://login.51job.com/login.php')
            logger.info("已打开前程无忧登录页面，请在浏览器中完成登录...")
            
            # 等待用户手动登录
            print("\n========== 前程无忧登录引导 ==========")
            print("1. 在打开的浏览器窗口中，请使用账号密码或其他方式登录前程无忧")
            print("2. 登录成功后，系统将自动提取Cookie")
            print("3. 请不要关闭浏览器窗口，等待提示成功")
            print("========================================\n")
            
            # 等待登录成功，通常可以通过检测某个仅在登录后才存在的元素
            WebDriverWait(self.browser, 300).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.uname'))
            )
            
            # 登录成功后，提取Cookie
            cookies = self.browser.get_cookies()
            cookie_str = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
            
            logger.info("成功提取前程无忧Cookie")
            print("\n✅ 前程无忧登录成功，已提取Cookie")
            
            return cookie_str
        except Exception as e:
            logger.error(f"提取前程无忧Cookie失败: {str(e)}")
            print(f"\n❌ 提取前程无忧Cookie失败: {str(e)}")
            return None
    
    def extract_lagou_cookie(self):
        """提取拉勾网的Cookie"""
        if not self.browser:
            self.initialize_browser()
        
        try:
            # 打开拉勾网登录页面
            self.browser.get('https://passport.lagou.com/login/login.html')
            logger.info("已打开拉勾网登录页面，请在浏览器中完成登录...")
            
            # 等待用户手动登录
            print("\n========== 拉勾网登录引导 ==========")
            print("1. 在打开的浏览器窗口中，请使用扫码或其他方式登录拉勾网")
            print("2. 登录成功后，系统将自动提取Cookie")
            print("3. 请不要关闭浏览器窗口，等待提示成功")
            print("========================================\n")
            
            # 等待登录成功，通常可以通过检测某个仅在登录后才存在的元素
            WebDriverWait(self.browser, 300).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.user_dropdown'))
            )
            
            # 登录成功后，提取Cookie
            cookies = self.browser.get_cookies()
            cookie_str = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
            
            logger.info("成功提取拉勾网Cookie")
            print("\n✅ 拉勾网登录成功，已提取Cookie")
            
            return cookie_str
        except Exception as e:
            logger.error(f"提取拉勾网Cookie失败: {str(e)}")
            print(f"\n❌ 提取拉勾网Cookie失败: {str(e)}")
            return None
    
    def update_env_file(self, platform_name, cookie_value, user_id=None):
        """
        更新.env文件中的Cookie信息
        
        参数:
        - platform_name: 平台名称
        - cookie_value: Cookie值
        - user_id: 用户ID（可选）
        """
        if not cookie_value:
            return False
        
        env_path = '.env'
        load_dotenv(env_path)
        
        if platform_name == 'boss':
            set_key(env_path, 'BOSS_COOKIE', cookie_value)
            if user_id:
                set_key(env_path, 'BOSS_USER_ID', user_id)
        elif platform_name == 'zhilian':
            set_key(env_path, 'ZHILIAN_COOKIE', cookie_value)
        elif platform_name == 'qiancheng':
            set_key(env_path, 'QIANCHENG_COOKIE', cookie_value)
        elif platform_name == 'lagou':
            set_key(env_path, 'LAGOU_COOKIE', cookie_value)
        
        logger.info(f"更新{platform_name}的Cookie信息到.env文件")
        return True
    
    def run_all(self):
        """运行所有平台的Cookie提取"""
        print("\n============= 求职平台Cookie提取工具 =============")
        print("此工具将引导您登录各求职平台并自动提取Cookie")
        print("请选择需要提取Cookie的平台：")
        print("1. Boss直聘")
        print("2. 智联招聘")
        print("3. 前程无忧")
        print("4. 拉勾网")
        print("5. 全部平台")
        print("0. 退出")
        
        while True:
            try:
                choice = input("\n请输入选项 (0-5): ")
                
                if choice == '0':
                    break
                
                self.initialize_browser()
                
                if choice == '1' or choice == '5':
                    cookie, user_id = self.extract_boss_cookie()
                    if cookie:
                        self.update_env_file('boss', cookie, user_id)
                
                if choice == '2' or choice == '5':
                    cookie = self.extract_zhilian_cookie()
                    if cookie:
                        self.update_env_file('zhilian', cookie)
                
                if choice == '3' or choice == '5':
                    cookie = self.extract_qiancheng_cookie()
                    if cookie:
                        self.update_env_file('qiancheng', cookie)
                
                if choice == '4' or choice == '5':
                    cookie = self.extract_lagou_cookie()
                    if cookie:
                        self.update_env_file('lagou', cookie)
                
                self.close_browser()
                
                if choice == '5':
                    print("\n✅ 所有平台Cookie提取完成！")
                    break
                
                another = input("\n是否继续提取其他平台Cookie？(y/n): ")
                if another.lower() != 'y':
                    break
            except Exception as e:
                logger.error(f"Cookie提取过程出错: {str(e)}")
                print(f"\n❌ 出错了: {str(e)}")
                self.close_browser()
        
        print("\n感谢使用Cookie提取工具！")

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/cookie_extractor.log"),
            logging.StreamHandler()
        ]
    )
    
    # 创建日志目录
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 运行Cookie提取
    extractor = CookieExtractor()
    extractor.run_all() 