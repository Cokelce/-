"""
Boss直聘平台爬虫

此脚本实现了对Boss直聘平台的求职功能，包括搜索职位、过滤职位、投递简历等。
"""

import os
import json
import time
import random
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("boss_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BossZhipin:
    """Boss直聘平台实现"""
    
    def __init__(self, config_path="config.json"):
        """初始化Boss直聘平台
        
        Args:
            config_path: 配置文件路径
        """
        logger.info("初始化Boss直聘平台")
        self.base_url = "https://www.zhipin.com"
        self.session = requests.Session()
        
        # 加载配置
        self.config = self._load_config(config_path)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Cookie": self.config.get("cookies", ""),
        }
        
        # 设置代理
        if self.config.get("proxy"):
            self.session.proxies = {
                "http": self.config["proxy"],
                "https": self.config["proxy"]
            }
            
        # 设置过滤条件
        self.keyword = self.config.get("keyword", "Python")
        self.city = self.config.get("city", "101010100")  # 默认北京
        self.experience = self.config.get("experience", "")
        self.degree = self.config.get("degree", "")
        self.salary = self.config.get("salary", "")
        self.exclude_keywords = self.config.get("exclude_keywords", [])
        self.company_exclude_keywords = self.config.get("company_exclude_keywords", [])
        self.require_exclude_keywords = self.config.get("require_exclude_keywords", [])
        self.job_exclude_types = self.config.get("job_exclude_types", [])
        self.applied_jobs_path = self.config.get("applied_jobs_path", "applied_jobs.json")
        self.applied_jobs = self._load_applied_jobs()
        
        # 设置请求间隔
        self.min_interval = self.config.get("min_interval", 5)
        self.max_interval = self.config.get("max_interval", 10)
    
    def _load_config(self, config_path):
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            dict: 配置信息
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")
                return {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def _load_applied_jobs(self):
        """加载已申请的职位记录
        
        Returns:
            list: 已申请的职位ID列表
        """
        try:
            if os.path.exists(self.applied_jobs_path):
                with open(self.applied_jobs_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                logger.info(f"已申请职位记录文件 {self.applied_jobs_path} 不存在，创建新文件")
                return []
        except Exception as e:
            logger.error(f"加载已申请职位记录失败: {e}")
            return []
    
    def _save_applied_jobs(self):
        """保存已申请的职位记录"""
        try:
            with open(self.applied_jobs_path, "w", encoding="utf-8") as f:
                json.dump(self.applied_jobs, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存已申请职位记录失败: {e}")
    
    def check_login_status(self):
        """检查登录状态
        
        Returns:
            bool: 是否已登录
        """
        logger.info("检查Boss直聘登录状态")
        try:
            response = self.session.get(
                f"{self.base_url}/wapi/zpgeek/common/data/getUserIds.json",
                headers=self.headers
            )
            data = response.json()
            if data.get("code") == 0 and data.get("zpData"):
                logger.info("Boss直聘已登录")
                return True
            else:
                logger.warning("Boss直聘未登录")
                return False
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False
    
    def get_user_profile(self):
        """获取用户简历信息
        
        Returns:
            dict: 用户简历信息
        """
        logger.info("获取Boss直聘用户简历")
        try:
            response = self.session.get(
                f"{self.base_url}/wapi/zpgeek/resume/parser",
                headers=self.headers
            )
            data = response.json()
            if data.get("code") == 0 and data.get("zpData"):
                logger.info("获取Boss直聘用户简历成功")
                return data.get("zpData", {})
            else:
                logger.warning("获取Boss直聘用户简历失败")
                return {}
        except Exception as e:
            logger.error(f"获取用户简历失败: {e}")
            return {}
    
    def search_jobs(self, keyword=None, city=None, page=1, experience=None, degree=None, salary=None):
        """搜索职位
        
        Args:
            keyword: 关键词
            city: 城市代码
            page: 页码
            experience: 工作经验要求
            degree: 学历要求
            salary: 薪资要求
            
        Returns:
            list: 职位信息列表
        """
        keyword = keyword or self.keyword
        city = city or self.city
        experience = experience or self.experience
        degree = degree or self.degree
        salary = salary or self.salary
        
        logger.info(f"搜索Boss直聘职位: {keyword}, 城市: {city}, 页码: {page}")
        
        # 构建URL
        url = f"{self.base_url}/wapi/zpgeek/search/joblist.json?city={city}&query={keyword}&page={page}"
        if experience:
            url += f"&experience={experience}"
        if degree:
            url += f"&degree={degree}"
        if salary:
            url += f"&salary={salary}"
        
        try:
            # 添加随机延迟
            sleep_time = random.uniform(self.min_interval, self.max_interval)
            logger.debug(f"请求前随机延迟 {sleep_time:.2f} 秒")
            time.sleep(sleep_time)
            
            response = self.session.get(url, headers=self.headers)
            data = response.json()
            
            if data.get("code") == 0 and data.get("zpData") and data["zpData"].get("jobList"):
                jobs = data["zpData"]["jobList"]
                logger.info(f"搜索到 {len(jobs)} 个职位")
                
                # 提取职位信息
                job_list = []
                for job in jobs:
                    job_info = {
                        "jobId": job.get("encryptJobId", ""),
                        "title": job.get("jobName", ""),
                        "salary": job.get("salaryDesc", ""),
                        "company": job.get("encryptBrandId", ""),
                        "company_name": job.get("brandName", ""),
                        "city": job.get("cityName", ""),
                        "experience": job.get("experienceName", ""),
                        "education": job.get("degreeName", ""),
                        "company_size": job.get("scaleName", ""),
                        "company_type": job.get("property", {}).get("name", ""),
                        "publish_time": job.get("timeDesc", ""),
                        "welfare": job.get("welfare", []),
                        "hrInfo": {
                            "name": job.get("geekName", ""),
                            "position": job.get("brandPositionName", "")
                        },
                        "url": f"{self.base_url}/job_detail/{job.get('encryptJobId', '')}.html"
                    }
                    job_list.append(job_info)
                    
                return job_list
            else:
                logger.warning("搜索Boss直聘职位失败")
                return []
        except Exception as e:
            logger.error(f"搜索职位失败: {e}")
            return []
    
    def get_job_detail(self, job_id):
        """获取职位详情
        
        Args:
            job_id: 职位ID
            
        Returns:
            dict: 职位详情
        """
        logger.info(f"获取Boss直聘职位详情: {job_id}")
        try:
            # 添加随机延迟
            sleep_time = random.uniform(self.min_interval, self.max_interval)
            logger.debug(f"请求前随机延迟 {sleep_time:.2f} 秒")
            time.sleep(sleep_time)
            
            url = f"{self.base_url}/job_detail/{job_id}.html"
            response = self.session.get(url, headers=self.headers)
            
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, "html.parser")
                
                # 提取职位描述
                job_desc = ""
                job_desc_div = soup.select_one(".job-detail-section.text")
                if job_desc_div:
                    job_desc = job_desc_div.get_text(strip=True)
                
                # 提取公司介绍
                company_desc = ""
                company_desc_div = soup.select_one(".job-sec-text")
                if company_desc_div:
                    company_desc = company_desc_div.get_text(strip=True)
                
                # 提取公司地址
                company_address = ""
                address_div = soup.select_one(".location-address")
                if address_div:
                    company_address = address_div.get_text(strip=True)
                
                job_detail = {
                    "jobId": job_id,
                    "job_description": job_desc,
                    "company_description": company_desc,
                    "company_address": company_address,
                }
                
                logger.info(f"获取Boss直聘职位详情成功: {job_id}")
                return job_detail
            else:
                logger.warning(f"获取Boss直聘职位详情失败，状态码: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"获取职位详情失败: {e}")
            return {}
    
    def filter_jobs(self, jobs):
        """过滤职位
        
        Args:
            jobs: 职位列表
            
        Returns:
            list: 过滤后的职位列表
        """
        logger.info(f"过滤Boss直聘职位，共 {len(jobs)} 个职位")
        filtered_jobs = []
        
        for job in jobs:
            # 已申请过的职位跳过
            if job.get("jobId") in self.applied_jobs:
                logger.debug(f"跳过已申请的职位: {job.get('title')} - {job.get('company_name')}")
                continue
            
            # 标题关键词过滤
            if any(kw.lower() in job.get("title", "").lower() for kw in self.exclude_keywords):
                logger.debug(f"职位标题包含排除关键词，跳过: {job.get('title')}")
                continue
            
            # 公司名称关键词过滤
            if any(kw.lower() in job.get("company_name", "").lower() for kw in self.company_exclude_keywords):
                logger.debug(f"公司名称包含排除关键词，跳过: {job.get('company_name')}")
                continue
            
            # 获取职位详情
            job_detail = self.get_job_detail(job.get("jobId"))
            if not job_detail:
                logger.debug(f"获取职位详情失败，跳过: {job.get('title')}")
                continue
            
            # 合并职位信息
            job.update(job_detail)
            
            # 职位描述关键词过滤
            if any(kw.lower() in job.get("job_description", "").lower() for kw in self.require_exclude_keywords):
                logger.debug(f"职位描述包含排除关键词，跳过: {job.get('title')}")
                continue
            
            # 公司类型过滤
            if job.get("company_type") in self.job_exclude_types:
                logger.debug(f"公司类型在排除列表中，跳过: {job.get('company_type')}")
                continue
            
            filtered_jobs.append(job)
        
        logger.info(f"过滤后剩余 {len(filtered_jobs)} 个职位")
        return filtered_jobs
    
    def get_chat_id(self, job_id):
        """获取聊天ID
        
        Args:
            job_id: 职位ID
            
        Returns:
            str: 聊天ID
        """
        logger.info(f"获取Boss直聘职位聊天ID: {job_id}")
        try:
            url = f"{self.base_url}/wapi/zpgeek/message/start/v2.json"
            payload = {
                "jobId": job_id,
                "brandId": "",
                "lid": "",
                "source": 0
            }
            
            # 添加随机延迟
            sleep_time = random.uniform(self.min_interval, self.max_interval)
            logger.debug(f"请求前随机延迟 {sleep_time:.2f} 秒")
            time.sleep(sleep_time)
            
            response = self.session.post(url, json=payload, headers=self.headers)
            data = response.json()
            
            if data.get("code") == 0 and data.get("zpData") and data["zpData"].get("id"):
                chat_id = data["zpData"]["id"]
                logger.info(f"获取Boss直聘职位聊天ID成功: {chat_id}")
                return chat_id
            else:
                logger.warning(f"获取Boss直聘职位聊天ID失败: {data.get('message', '')}")
                return ""
        except Exception as e:
            logger.error(f"获取聊天ID失败: {e}")
            return ""
    
    def send_greeting(self, chat_id, greeting=None):
        """发送打招呼消息
        
        Args:
            chat_id: 聊天ID
            greeting: 打招呼消息
            
        Returns:
            bool: 是否发送成功
        """
        if not greeting:
            greeting = self.config.get("greeting", "您好，我对贵公司的职位很感兴趣，希望能有机会进一步了解。")
        
        logger.info(f"发送Boss直聘打招呼消息: {chat_id}")
        try:
            url = f"{self.base_url}/wapi/zprelation/message/save.json"
            payload = {
                "contactId": chat_id,
                "switchOn": True,
                "replyTemplateId": "",
                "content": greeting
            }
            
            # 添加随机延迟
            sleep_time = random.uniform(self.min_interval, self.max_interval)
            logger.debug(f"请求前随机延迟 {sleep_time:.2f} 秒")
            time.sleep(sleep_time)
            
            response = self.session.post(url, json=payload, headers=self.headers)
            data = response.json()
            
            if data.get("code") == 0:
                logger.info(f"发送Boss直聘打招呼消息成功: {chat_id}")
                return True
            else:
                logger.warning(f"发送Boss直聘打招呼消息失败: {data.get('message', '')}")
                return False
        except Exception as e:
            logger.error(f"发送打招呼消息失败: {e}")
            return False
    
    def send_resume_image(self, chat_id):
        """发送简历图片
        
        Args:
            chat_id: 聊天ID
            
        Returns:
            bool: 是否发送成功
        """
        resume_path = self.config.get("resume_image_path", "")
        if not resume_path or not os.path.exists(resume_path):
            logger.warning(f"简历图片不存在: {resume_path}")
            return False
        
        logger.info(f"发送Boss直聘简历图片: {chat_id}")
        try:
            url = f"{self.base_url}/wapi/zprelation/attachment/resume/upload/image.json"
            
            with open(resume_path, "rb") as f:
                files = {"file": f}
                
                # 添加随机延迟
                sleep_time = random.uniform(self.min_interval, self.max_interval)
                logger.debug(f"请求前随机延迟 {sleep_time:.2f} 秒")
                time.sleep(sleep_time)
                
                response = self.session.post(url, files=files, headers=self.headers)
                data = response.json()
                
                if data.get("code") == 0 and data.get("zpData") and data["zpData"].get("mediaId"):
                    media_id = data["zpData"]["mediaId"]
                    
                    # 发送图片消息
                    message_url = f"{self.base_url}/wapi/zprelation/message/save.json"
                    payload = {
                        "contactId": chat_id,
                        "switchOn": True,
                        "replyTemplateId": "",
                        "attachmentMediaId": media_id,
                        "content": "简历"
                    }
                    
                    # 添加随机延迟
                    sleep_time = random.uniform(self.min_interval, self.max_interval)
                    logger.debug(f"请求前随机延迟 {sleep_time:.2f} 秒")
                    time.sleep(sleep_time)
                    
                    message_response = self.session.post(message_url, json=payload, headers=self.headers)
                    message_data = message_response.json()
                    
                    if message_data.get("code") == 0:
                        logger.info(f"发送Boss直聘简历图片成功: {chat_id}")
                        return True
                    else:
                        logger.warning(f"发送Boss直聘简历图片消息失败: {message_data.get('message', '')}")
                        return False
                else:
                    logger.warning(f"上传Boss直聘简历图片失败: {data.get('message', '')}")
                    return False
        except Exception as e:
            logger.error(f"发送简历图片失败: {e}")
            return False
    
    def apply_job(self, job):
        """申请职位
        
        Args:
            job: 职位信息
            
        Returns:
            bool: 是否申请成功
        """
        job_id = job.get("jobId")
        if not job_id:
            logger.warning("职位ID为空，无法申请")
            return False
        
        logger.info(f"申请Boss直聘职位: {job.get('title', '未知职位')} - {job.get('company_name', '未知公司')}")
        
        # 获取聊天ID
        chat_id = self.get_chat_id(job_id)
        if not chat_id:
            logger.warning(f"获取聊天ID失败，无法申请职位: {job_id}")
            return False
        
        # 发送打招呼消息
        if not self.send_greeting(chat_id):
            logger.warning(f"发送打招呼消息失败，继续尝试申请职位: {job_id}")
        
        # 发送简历图片
        if self.config.get("send_resume_image", False):
            if not self.send_resume_image(chat_id):
                logger.warning(f"发送简历图片失败，继续尝试申请职位: {job_id}")
        
        # 标记为已申请
        self.applied_jobs.append(job_id)
        self._save_applied_jobs()
        
        logger.info(f"申请Boss直聘职位成功: {job.get('title', '未知职位')} - {job.get('company_name', '未知公司')}")
        return True
    
    def run(self):
        """执行求职流程"""
        logger.info("执行Boss直聘求职流程")
        
        # 检查登录状态
        if not self.check_login_status():
            logger.error("Boss直聘未登录，无法执行求职流程")
            return False
        
        # 获取用户简历
        user_profile = self.get_user_profile()
        if not user_profile:
            logger.warning("获取用户简历失败，继续执行求职流程")
        
        # 搜索职位
        all_jobs = []
        for page in range(1, self.config.get("max_pages", 5) + 1):
            jobs = self.search_jobs(page=page)
            if not jobs:
                logger.info(f"第 {page} 页没有搜索到职位，停止搜索")
                break
            
            all_jobs.extend(jobs)
            logger.info(f"已搜索到 {len(all_jobs)} 个职位")
            
            # 判断是否达到最大职位数
            if len(all_jobs) >= self.config.get("max_jobs", 100):
                logger.info(f"已达到最大职位数 {self.config.get('max_jobs', 100)}，停止搜索")
                break
            
            # 添加页面间随机延迟
            if page < self.config.get("max_pages", 5):
                sleep_time = random.uniform(self.min_interval * 2, self.max_interval * 2)
                logger.debug(f"页面间随机延迟 {sleep_time:.2f} 秒")
                time.sleep(sleep_time)
        
        # 过滤职位
        filtered_jobs = self.filter_jobs(all_jobs)
        
        # 申请职位
        applied_count = 0
        for job in filtered_jobs:
            if applied_count >= self.config.get("max_apply", 10):
                logger.info(f"已达到最大申请数 {self.config.get('max_apply', 10)}，停止申请")
                break
            
            if self.apply_job(job):
                applied_count += 1
                
                # 申请间随机延迟
                if applied_count < len(filtered_jobs) and applied_count < self.config.get("max_apply", 10):
                    sleep_time = random.uniform(self.min_interval * 3, self.max_interval * 3)
                    logger.debug(f"申请间随机延迟 {sleep_time:.2f} 秒")
                    time.sleep(sleep_time)
        
        logger.info(f"Boss直聘求职流程执行完成，共申请 {applied_count} 个职位")
        return applied_count > 0

if __name__ == "__main__":
    boss = BossZhipin()
    boss.run() 