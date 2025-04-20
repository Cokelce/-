import os
import json
import time
import logging
import base64
from datetime import datetime
from urllib.parse import urlencode
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from playwright.sync_api import sync_playwright

from config import PLATFORMS, USER_PREFERENCES, FILTER_CONFIG
from utils import (
    make_request, random_delay, update_blacklist,
    record_job_application, is_job_applied, send_wechat_notification,
    load_data, save_data, ensure_dir
)
from ai_module import analyze_job_relevance, generate_greeting_message
from city_codes import get_city_code, BOSS_CITY_CODES

# 设置日志
logger = logging.getLogger(__name__)

class BossZhipin:
    """Boss直聘平台操作类"""
    
    def __init__(self):
        self.config = PLATFORMS["boss"]
        self.cookie = self.config["cookie"]
        self.user_id = self.config["user_id"]
        self.resume_path = self.config["resume_path"]
        self.daily_limit = self.config["daily_limit"]
        self.base_url = "https://www.zhipin.com"
        self.api_url = "https://www.zhipin.com/wapi"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
            "Cookie": self.cookie,
            "Referer": "https://www.zhipin.com/",
            "Connection": "keep-alive",
        }
        # 确保目录存在
        ensure_dir("data/boss")
        
    def check_login_status(self):
        """检查登录状态"""
        try:
            url = f"{self.api_url}/zpgeek/user/recommend.json"
            response = make_request(url, headers=self.headers)
            data = response.json()
            
            if data.get("code") == 0:
                logger.info("Boss直聘登录状态正常")
                return True
            else:
                logger.warning(f"Boss直聘登录状态异常: {data}")
                return False
        except Exception as e:
            logger.error(f"检查Boss直聘登录状态失败: {str(e)}")
            return False
    
    def get_user_profile(self):
        """获取用户简历信息"""
        try:
            # 先尝试从缓存加载
            profile = load_data("boss/profile.json")
            if profile:
                return profile
            
            # 如果没有缓存，则从API获取
            url = f"{self.api_url}/zpgeek/resume/preview.json"
            response = make_request(url, headers=self.headers)
            data = response.json()
            
            if data.get("code") == 0:
                profile = data.get("zpData", {}).get("resume", {})
                # 缓存用户简历
                save_data(profile, "boss/profile.json")
                logger.info("获取Boss直聘用户简历成功")
                return profile
            else:
                logger.error(f"获取Boss直聘用户简历失败: {data}")
                return {}
        except Exception as e:
            logger.error(f"获取Boss直聘用户简历异常: {str(e)}")
            return {}
    
    def format_user_profile(self, profile):
        """将用户简历格式化为文本"""
        if not profile:
            return "无法获取求职者简历信息"
        
        text = "## 求职者简历\n"
        
        # 基本信息
        text += f"### 基本信息\n"
        text += f"- 姓名: {profile.get('name', '未知')}\n"
        text += f"- 年龄: {profile.get('age', '未知')}\n"
        text += f"- 工作年限: {profile.get('workExpYear', '未知')}\n"
        text += f"- 学历: {profile.get('education', '未知')}\n"
        
        # 工作经历
        if "workExperienceList" in profile and profile["workExperienceList"]:
            text += f"\n### 工作经历\n"
            for exp in profile["workExperienceList"]:
                text += f"- {exp.get('company', '未知公司')} | {exp.get('position', '未知职位')} | {exp.get('startDate', '')} - {exp.get('endDate', '至今')}\n"
                text += f"  {exp.get('description', '无职责描述')}\n"
        
        # 项目经历
        if "projectExperienceList" in profile and profile["projectExperienceList"]:
            text += f"\n### 项目经历\n"
            for proj in profile["projectExperienceList"]:
                text += f"- {proj.get('projectName', '未知项目')} | {proj.get('startDate', '')} - {proj.get('endDate', '至今')}\n"
                text += f"  {proj.get('description', '无项目描述')}\n"
        
        # 教育经历
        if "educationList" in profile and profile["educationList"]:
            text += f"\n### 教育经历\n"
            for edu in profile["educationList"]:
                text += f"- {edu.get('school', '未知学校')} | {edu.get('major', '未知专业')} | {edu.get('degree', '未知学历')} | {edu.get('startDate', '')} - {edu.get('endDate', '至今')}\n"
        
        # 技能标签
        if "skillList" in profile and profile["skillList"]:
            text += f"\n### 技能标签\n"
            for skill in profile["skillList"]:
                text += f"- {skill.get('name', '')}: {skill.get('level', '熟练')}\n"
        
        return text
    
    def search_jobs(self, keyword, city="101010100", page=1, experience="", degree="", salary=""):
        """
        搜索职位
        
        参数:
        - keyword: 搜索关键词
        - city: 城市代码，默认北京(101010100)
        - page: 页码
        - experience: 工作经验要求，如"105" 代表 3-5年
        - degree: 学历要求，如"203" 代表 本科
        - salary: 薪资要求，如"406" 代表 25k-50k
        
        返回:
        - jobs: 职位列表
        """
        try:
            url = f"{self.base_url}/c{city}/"
            params = {
                "query": keyword,
                "page": page,
                "ka": "page-{page}"
            }
            
            if experience:
                params["experience"] = experience
            if degree:
                params["degree"] = degree
            if salary:
                params["salary"] = salary
            
            # 发起请求
            full_url = url + "?" + urlencode(params)
            response = make_request(full_url, headers=self.headers)
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'lxml')
            job_list_div = soup.find('div', class_='job-list')
            
            if not job_list_div:
                logger.warning("没有找到职位列表")
                return []
            
            job_items = job_list_div.find_all('li')
            jobs = []
            
            for item in job_items:
                try:
                    # 提取职位ID
                    job_card = item.find('div', class_='job-card-body')
                    if not job_card:
                        continue
                    
                    job_url = job_card.find('a')['href']
                    job_id = job_url.split('/')[-1].split('.')[0]
                    
                    # 提取职位标题
                    title_div = job_card.find('div', class_='job-title')
                    title = title_div.text.strip() if title_div else "未知职位"
                    
                    # 提取公司名称
                    company_div = item.find('div', class_='company-name')
                    company = company_div.a.text.strip() if company_div and company_div.a else "未知公司"
                    
                    # 提取薪资
                    salary_div = item.find('div', class_='salary')
                    salary = salary_div.text.strip() if salary_div else "薪资面议"
                    
                    # 提取HR信息
                    hr_div = item.find('div', class_='info-public')
                    hr_name = ""
                    hr_title = ""
                    hr_active = ""
                    
                    if hr_div:
                        hr_name_span = hr_div.find('span', class_='name')
                        hr_name = hr_name_span.text.strip() if hr_name_span else ""
                        
                        hr_title_span = hr_div.find('span', class_='title')
                        hr_title = hr_title_span.text.strip() if hr_title_span else ""
                        
                        hr_active_span = hr_div.find('span', class_='active')
                        hr_active = hr_active_span.text.strip() if hr_active_span else ""
                    
                    # 构建职位信息
                    job_info = {
                        "id": job_id,
                        "title": title,
                        "company": company,
                        "salary": salary,
                        "hr_name": hr_name,
                        "hr_title": hr_title,
                        "hr_active": hr_active,
                        "url": f"{self.base_url}{job_url}",
                        "platform": "boss"
                    }
                    
                    jobs.append(job_info)
                except Exception as e:
                    logger.error(f"解析职位信息失败: {str(e)}")
            
            logger.info(f"搜索到 {len(jobs)} 个职位")
            return jobs
        except Exception as e:
            logger.error(f"搜索职位失败: {str(e)}")
            return []
    
    def get_job_detail(self, job_id):
        """
        获取职位详情
        
        参数:
        - job_id: 职位ID
        
        返回:
        - job_detail: 职位详情
        """
        try:
            url = f"{self.base_url}/job_detail/{job_id}.html"
            response = make_request(url, headers=self.headers)
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 提取职位描述
            description_div = soup.find('div', class_='job-sec-text')
            description = description_div.text.strip() if description_div else "无职位描述"
            
            # 提取公司信息
            company_div = soup.find('div', class_='company-info')
            company_info = {}
            
            if company_div:
                # 公司规模
                scale_div = company_div.find('div', text='规模')
                if scale_div and scale_div.find_next_sibling('div'):
                    company_info['scale'] = scale_div.find_next_sibling('div').text.strip()
                
                # 公司行业
                industry_div = company_div.find('div', text='行业')
                if industry_div and industry_div.find_next_sibling('div'):
                    company_info['industry'] = industry_div.find_next_sibling('div').text.strip()
            
            # 返回职位详情
            job_detail = {
                "id": job_id,
                "description": description,
                "company_info": company_info
            }
            
            return job_detail
        except Exception as e:
            logger.error(f"获取职位详情失败: {str(e)}")
            return {"id": job_id, "description": "获取职位描述失败", "company_info": {}}
    
    def filter_jobs(self, jobs):
        """
        根据过滤条件筛选职位
        
        参数:
        - jobs: 职位列表
        
        返回:
        - filtered_jobs: 过滤后的职位列表
        """
        filtered_jobs = []
        blacklist_companies = FILTER_CONFIG["blacklist_companies"]
        exclude_headhunter = FILTER_CONFIG["exclude_headhunter"]
        hr_activity_threshold = FILTER_CONFIG["hr_activity_threshold"]
        
        for job in jobs:
            # 检查是否已投递
            if FILTER_CONFIG["exclude_applied"] and is_job_applied("boss", job["id"]):
                logger.info(f"过滤已投递职位: {job['title']} - {job['company']}")
                continue
            
            # 检查公司是否在黑名单中
            if job["company"] in blacklist_companies:
                logger.info(f"过滤黑名单公司: {job['company']}")
                continue
            
            # 检查是否是猎头
            if exclude_headhunter and job.get("hr_title", "").find("猎头") >= 0:
                logger.info(f"过滤猎头职位: {job['title']} - {job['company']}")
                continue
            
            # 检查HR活跃度
            if hr_activity_threshold > 0 and "hr_active" in job and job["hr_active"]:
                # 提取HR最后活跃时间
                active_text = job["hr_active"]
                if "刚刚" in active_text or "分钟" in active_text:
                    pass  # 活跃度高，保留
                elif "小时" in active_text:
                    hours = int(active_text.split("小时")[0])
                    if hours > hr_activity_threshold:
                        logger.info(f"过滤不活跃HR职位: {job['title']} - {job['company']} - {active_text}")
                        continue
                elif "天" in active_text:
                    logger.info(f"过滤不活跃HR职位: {job['title']} - {job['company']} - {active_text}")
                    continue
            
            # 获取职位详情
            job_detail = self.get_job_detail(job["id"])
            job["description"] = job_detail["description"]
            job["company_info"] = job_detail["company_info"]
            
            # 检查职位描述中是否包含黑名单关键词
            has_blacklist_keyword = False
            for keyword in FILTER_CONFIG["blacklist_keywords"]:
                if keyword in job["description"]:
                    logger.info(f"过滤黑名单关键词职位: {job['title']} - {job['company']} - 关键词: {keyword}")
                    has_blacklist_keyword = True
                    break
            
            if has_blacklist_keyword:
                continue
            
            # 通过所有过滤条件，添加到结果列表
            filtered_jobs.append(job)
            
            # 随机延迟，避免请求过快
            random_delay(2, 5)
        
        logger.info(f"过滤后剩余 {len(filtered_jobs)} 个职位")
        return filtered_jobs
    
    def send_greeting(self, job_id, message):
        """
        发送打招呼语
        
        参数:
        - job_id: 职位ID
        - message: 打招呼语内容
        
        返回:
        - success: 是否成功
        """
        try:
            url = f"{self.api_url}/zpgeek/chat/greeting.json"
            data = {
                "jobId": job_id,
                "greeting": message,
                "securityId": "",  # 可能需要动态获取
                "content": message
            }
            
            response = make_request(url, method="POST", headers=self.headers, json_data=data)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"发送打招呼语成功: {job_id}")
                return True
            else:
                logger.error(f"发送打招呼语失败: {result}")
                return False
        except Exception as e:
            logger.error(f"发送打招呼语异常: {str(e)}")
            return False
    
    def send_resume_image(self, job_id, chat_id):
        """
        发送图片简历
        
        参数:
        - job_id: 职位ID
        - chat_id: 聊天ID
        
        返回:
        - success: 是否成功
        """
        try:
            if not os.path.exists(self.resume_path):
                logger.error(f"简历图片不存在: {self.resume_path}")
                return False
            
            # 这部分可能需要使用Selenium或Playwright来实现，因为涉及到文件上传
            # 以下是使用Playwright的示例实现
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                
                # 设置Cookie
                cookies = []
                for cookie_str in self.cookie.split(';'):
                    if '=' in cookie_str:
                        name, value = cookie_str.strip().split('=', 1)
                        cookies.append({"name": name, "value": value, "domain": "www.zhipin.com", "path": "/"})
                
                context.add_cookies(cookies)
                page = context.new_page()
                
                # 进入聊天页面
                page.goto(f"https://www.zhipin.com/web/geek/chat?id={chat_id}")
                page.wait_for_load_state("networkidle")
                
                # 点击发送图片按钮
                page.click("button.send-img")
                
                # 上传图片
                file_input = page.query_selector('input[type="file"]')
                if file_input:
                    file_input.set_input_files(self.resume_path)
                    
                    # 等待上传完成
                    page.wait_for_selector("img.msg-img")
                    
                    # 点击发送
                    page.click("button.submit")
                    
                    # 等待发送完成
                    page.wait_for_timeout(2000)
                    
                    logger.info(f"发送图片简历成功: {job_id}")
                    browser.close()
                    return True
                else:
                    logger.error("找不到文件上传输入框")
                    browser.close()
                    return False
        except Exception as e:
            logger.error(f"发送图片简历异常: {str(e)}")
            return False
    
    def get_chat_id(self, job_id):
        """
        获取与职位对应的聊天ID
        
        参数:
        - job_id: 职位ID
        
        返回:
        - chat_id: 聊天ID
        """
        try:
            url = f"{self.api_url}/zpgeek/chat/list.json"
            response = make_request(url, headers=self.headers)
            result = response.json()
            
            if result.get("code") == 0:
                chats = result.get("zpData", {}).get("chatList", [])
                for chat in chats:
                    if chat.get("jobId") == job_id:
                        logger.info(f"找到聊天ID: {chat.get('encryptId')}")
                        return chat.get("encryptId")
            
            logger.warning(f"找不到职位对应的聊天ID: {job_id}")
            return None
        except Exception as e:
            logger.error(f"获取聊天ID异常: {str(e)}")
            return None
    
    def apply_job(self, job, user_profile_text):
        """
        投递职位
        
        参数:
        - job: 职位信息
        - user_profile_text: 用户简历文本
        
        返回:
        - success: 是否成功
        """
        try:
            # 生成打招呼语
            greeting_message = generate_greeting_message(job, user_profile_text)
            
            # 发送打招呼语
            if self.send_greeting(job["id"], greeting_message):
                # 记录投递
                record_job_application("boss", job["id"], job["title"], job["company"])
                
                # 获取聊天ID
                chat_id = self.get_chat_id(job["id"])
                if chat_id:
                    # 发送图片简历
                    random_delay(3, 6)
                    self.send_resume_image(job["id"], chat_id)
                
                # 发送通知
                notification_content = f"平台: Boss直聘\n职位: {job['title']}\n公司: {job['company']}\n匹配度: {job.get('match_score', 'N/A')}\n状态: 已投递"
                send_wechat_notification("职位投递成功", notification_content)
                
                logger.info(f"投递职位成功: {job['title']} - {job['company']}")
                return True
            else:
                logger.error(f"投递职位失败: {job['title']} - {job['company']}")
                return False
        except Exception as e:
            logger.error(f"投递职位异常: {str(e)}")
            return False
    
    def run(self):
        """执行Boss直聘求职流程"""
        logger.info("开始Boss直聘求职流程")
        
        # 检查登录状态
        if not self.check_login_status():
            logger.error("Boss直聘登录状态异常，退出流程")
            send_wechat_notification("登录状态异常", "Boss直聘登录状态异常，请更新Cookie")
            return False
        
        # 获取用户简历
        profile = self.get_user_profile()
        if not profile:
            logger.error("获取用户简历失败，退出流程")
            send_wechat_notification("获取简历失败", "无法获取Boss直聘用户简历，请检查")
            return False
        
        # 格式化用户简历
        user_profile_text = self.format_user_profile(profile)
        
        # 统计今日已投递数量
        today = datetime.now().strftime("%Y-%m-%d")
        applications = load_data("applications.json", default=[])
        today_applications = [
            app for app in applications
            if app["platform"] == "boss" and app["applied_at"].startswith(today)
        ]
        
        remaining_limit = self.daily_limit - len(today_applications)
        if remaining_limit <= 0:
            logger.warning("已达到今日投递上限，退出流程")
            send_wechat_notification("投递上限提醒", f"Boss直聘今日已达到投递上限 {self.daily_limit} 个职位")
            return False
        
        logger.info(f"今日还可投递 {remaining_limit} 个职位")
        
        # 搜索职位
        all_jobs = []
        for intention in USER_PREFERENCES["job_intentions"]:
            for city in USER_PREFERENCES["target_cities"]:
                # 转换城市名称为城市代码
                city_code = get_city_code('boss', city, "101010100")  # 默认北京
                logger.info(f"搜索职位: {intention} 在 {city}(城市代码: {city_code})")
                
                jobs = self.search_jobs(intention, city=city_code, page=1)
                all_jobs.extend(jobs)
                
                # 随机延迟
                random_delay(2, 5)
        
        # 去重
        unique_jobs = []
        job_ids = set()
        for job in all_jobs:
            if job["id"] not in job_ids:
                job_ids.add(job["id"])
                unique_jobs.append(job)
        
        logger.info(f"搜索到 {len(unique_jobs)} 个唯一职位")
        
        # 过滤职位
        filtered_jobs = self.filter_jobs(unique_jobs)
        
        # 使用AI分析职位匹配度
        from ai_module import filter_jobs_by_ai
        matched_jobs = filter_jobs_by_ai(filtered_jobs, user_profile_text, threshold=70)
        
        # 限制投递数量
        if len(matched_jobs) > remaining_limit:
            matched_jobs = matched_jobs[:remaining_limit]
        
        # 投递职位
        success_count = 0
        for job in matched_jobs:
            if self.apply_job(job, user_profile_text):
                success_count += 1
            
            # 随机延迟
            random_delay(10, 20)
        
        # 发送总结通知
        summary = f"搜索到 {len(unique_jobs)} 个职位\n过滤后 {len(filtered_jobs)} 个职位\n匹配到 {len(matched_jobs)} 个职位\n成功投递 {success_count} 个职位"
        send_wechat_notification("Boss直聘投递总结", summary)
        
        logger.info(f"Boss直聘求职流程完成: {summary}")
        return True 