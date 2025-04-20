"""
智联招聘平台爬虫

此脚本实现了对智联招聘平台的求职功能，包括搜索职位、过滤职位、投递简历等。
"""

import os
import json
import time
import random
import logging
import requests
from bs4 import BeautifulSoup

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("zhilian_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ZhilianZhaopin:
    """智联招聘平台实现"""
    
    def __init__(self, config_path="config.json"):
        """初始化智联招聘平台
        
        Args:
            config_path: 配置文件路径
        """
        logger.info("初始化智联招聘平台")
        self.base_url = "https://www.zhaopin.com"
        self.session = requests.Session()
        
        # 加载配置
        self.config = self._load_config(config_path)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Cookie": self.config.get("zhilian_cookies", ""),
        }
        
        # 设置代理
        if self.config.get("proxy"):
            self.session.proxies = {
                "http": self.config["proxy"],
                "https": self.config["proxy"]
            }
            
        # 设置过滤条件
        self.keyword = self.config.get("keyword", "Python")
        self.city = self.config.get("zhilian_city", "530")  # 默认北京
        self.experience = self.config.get("zhilian_experience", "")
        self.degree = self.config.get("zhilian_degree", "")
        self.salary = self.config.get("zhilian_salary", "")
        self.exclude_keywords = self.config.get("exclude_keywords", [])
        self.company_exclude_keywords = self.config.get("company_exclude_keywords", [])
        self.require_exclude_keywords = self.config.get("require_exclude_keywords", [])
        self.job_exclude_types = self.config.get("job_exclude_types", [])
        self.applied_jobs_path = self.config.get("zhilian_applied_jobs_path", "zhilian_applied_jobs.json")
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
        logger.info("检查智联招聘登录状态")
        try:
            url = f"{self.base_url}/api/user/getuserinfo"
            response = self.session.get(url, headers=self.headers)
            data = response.json()
            
            if data.get("code") == 200 and data.get("data") and data["data"].get("name"):
                logger.info("智联招聘已登录")
                return True
            else:
                logger.warning("智联招聘未登录")
                return False
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False
    
    def get_user_profile(self):
        """获取用户简历信息
        
        Returns:
            dict: 用户简历信息
        """
        logger.info("获取智联招聘用户简历")
        try:
            url = f"{self.base_url}/api/resume/getresumeinfo"
            response = self.session.get(url, headers=self.headers)
            data = response.json()
            
            if data.get("code") == 200 and data.get("data"):
                logger.info("获取智联招聘用户简历成功")
                return data.get("data", {})
            else:
                logger.warning("获取智联招聘用户简历失败")
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
        
        logger.info(f"搜索智联招聘职位: {keyword}, 城市: {city}, 页码: {page}")
        
        # 构建URL参数
        params = {
            "kw": keyword,
            "city": city,
            "pageNo": page,
            "pageSize": 20,
        }
        
        if experience:
            params["workExperience"] = experience
        if degree:
            params["eduLevel"] = degree
        if salary:
            params["salary"] = salary
        
        try:
            # 添加随机延迟
            sleep_time = random.uniform(self.min_interval, self.max_interval)
            logger.debug(f"请求前随机延迟 {sleep_time:.2f} 秒")
            time.sleep(sleep_time)
            
            url = f"{self.base_url}/api/sou"
            response = self.session.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if data.get("code") == 200 and data.get("data") and data["data"].get("list"):
                jobs = data["data"]["list"]
                logger.info(f"搜索到 {len(jobs)} 个职位")
                
                # 提取职位信息
                job_list = []
                for job in jobs:
                    job_info = {
                        "jobId": job.get("positionId", ""),
                        "title": job.get("positionName", ""),
                        "salary": job.get("salary", ""),
                        "company_id": job.get("companyId", ""),
                        "company_name": job.get("companyName", ""),
                        "city": job.get("cityName", ""),
                        "experience": job.get("workingExp", ""),
                        "education": job.get("education", ""),
                        "company_size": job.get("companySize", ""),
                        "company_type": job.get("companyType", ""),
                        "publish_time": job.get("createDate", ""),
                        "welfare": job.get("welfare", []),
                        "url": f"{self.base_url}/job_detail/{job.get('positionId', '')}.html"
                    }
                    job_list.append(job_info)
                
                return job_list
            else:
                logger.warning("搜索智联招聘职位失败")
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
        logger.info(f"获取智联招聘职位详情: {job_id}")
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
                job_desc_div = soup.select_one(".job-description")
                if job_desc_div:
                    job_desc = job_desc_div.get_text(strip=True)
                
                # 提取公司介绍
                company_desc = ""
                company_desc_div = soup.select_one(".company-introduction")
                if company_desc_div:
                    company_desc = company_desc_div.get_text(strip=True)
                
                # 提取公司地址
                company_address = ""
                address_div = soup.select_one(".job-address")
                if address_div:
                    company_address = address_div.get_text(strip=True)
                
                job_detail = {
                    "jobId": job_id,
                    "job_description": job_desc,
                    "company_description": company_desc,
                    "company_address": company_address,
                }
                
                logger.info(f"获取智联招聘职位详情成功: {job_id}")
                return job_detail
            else:
                logger.warning(f"获取智联招聘职位详情失败，状态码: {response.status_code}")
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
        logger.info(f"过滤智联招聘职位，共 {len(jobs)} 个职位")
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
        
        logger.info(f"申请智联招聘职位: {job.get('title', '未知职位')} - {job.get('company_name', '未知公司')}")
        
        try:
            # 添加随机延迟
            sleep_time = random.uniform(self.min_interval, self.max_interval)
            logger.debug(f"请求前随机延迟 {sleep_time:.2f} 秒")
            time.sleep(sleep_time)
            
            url = f"{self.base_url}/api/apply/apply"
            payload = {
                "positionId": job_id,
                "resumeId": self.config.get("zhilian_resume_id", ""),
                "source": "PC"
            }
            
            response = self.session.post(url, json=payload, headers=self.headers)
            data = response.json()
            
            if data.get("code") == 200:
                # 标记为已申请
                self.applied_jobs.append(job_id)
                self._save_applied_jobs()
                
                logger.info(f"申请智联招聘职位成功: {job.get('title', '未知职位')} - {job.get('company_name', '未知公司')}")
                return True
            else:
                logger.warning(f"申请智联招聘职位失败: {data.get('message', '')}")
                return False
        except Exception as e:
            logger.error(f"申请职位失败: {e}")
            return False
    
    def run(self):
        """执行求职流程"""
        logger.info("执行智联招聘求职流程")
        
        # 检查登录状态
        if not self.check_login_status():
            logger.error("智联招聘未登录，无法执行求职流程")
            return False
        
        # 获取用户简历
        user_profile = self.get_user_profile()
        if not user_profile:
            logger.warning("获取用户简历失败，继续执行求职流程")
        
        # 搜索职位
        all_jobs = []
        for page in range(1, self.config.get("zhilian_max_pages", 5) + 1):
            jobs = self.search_jobs(page=page)
            if not jobs:
                logger.info(f"第 {page} 页没有搜索到职位，停止搜索")
                break
            
            all_jobs.extend(jobs)
            logger.info(f"已搜索到 {len(all_jobs)} 个职位")
            
            # 判断是否达到最大职位数
            if len(all_jobs) >= self.config.get("zhilian_max_jobs", 100):
                logger.info(f"已达到最大职位数 {self.config.get('zhilian_max_jobs', 100)}，停止搜索")
                break
            
            # 添加页面间随机延迟
            if page < self.config.get("zhilian_max_pages", 5):
                sleep_time = random.uniform(self.min_interval * 2, self.max_interval * 2)
                logger.debug(f"页面间随机延迟 {sleep_time:.2f} 秒")
                time.sleep(sleep_time)
        
        # 过滤职位
        filtered_jobs = self.filter_jobs(all_jobs)
        
        # 申请职位
        applied_count = 0
        for job in filtered_jobs:
            if applied_count >= self.config.get("zhilian_max_apply", 10):
                logger.info(f"已达到最大申请数 {self.config.get('zhilian_max_apply', 10)}，停止申请")
                break
            
            if self.apply_job(job):
                applied_count += 1
                
                # 申请间随机延迟
                if applied_count < len(filtered_jobs) and applied_count < self.config.get("zhilian_max_apply", 10):
                    sleep_time = random.uniform(self.min_interval * 3, self.max_interval * 3)
                    logger.debug(f"申请间随机延迟 {sleep_time:.2f} 秒")
                    time.sleep(sleep_time)
        
        logger.info(f"智联招聘求职流程执行完成，共申请 {applied_count} 个职位")
        return applied_count > 0

if __name__ == "__main__":
    zhilian = ZhilianZhaopin()
    zhilian.run() 