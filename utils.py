import os
import json
import logging
import time
import random
import requests
from datetime import datetime
from wechatpy.enterprise import WeChatClient
from config import WECHAT_CONFIG, PROXY_CONFIG

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(ensure_dir('logs'), 'job_assistant.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建目录
def ensure_dir(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"创建目录: {directory}")

# 企业微信通知
def send_wechat_notification(title, content, to_user="@all"):
    """发送企业微信通知"""
    if not WECHAT_CONFIG["enabled"]:
        logger.info("企业微信通知已禁用")
        return False
    
    try:
        client = WeChatClient(
            WECHAT_CONFIG["corp_id"],
            WECHAT_CONFIG["secret"]
        )
        
        message = f"{title}\n\n{content}"
        response = client.message.send_text(
            agent_id=WECHAT_CONFIG["agent_id"],
            user_ids=to_user,
            content=message
        )
        
        if response["errcode"] == 0:
            logger.info("企业微信通知发送成功")
            return True
        else:
            logger.error(f"企业微信通知发送失败: {response}")
            return False
    except Exception as e:
        logger.error(f"企业微信通知发送异常: {str(e)}")
        return False

# 保存和加载数据
def save_data(data, filename):
    """保存数据到JSON文件"""
    ensure_dir("data")
    filepath = os.path.join("data", filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"数据已保存到 {filepath}")
        return True
    except Exception as e:
        logger.error(f"保存数据到 {filepath} 失败: {str(e)}")
        return False

def load_data(filename, default=None):
    """从JSON文件加载数据"""
    filepath = os.path.join("data", filename)
    
    if not os.path.exists(filepath):
        logger.info(f"文件 {filepath} 不存在，返回默认值")
        return default if default is not None else {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"从 {filepath} 加载数据成功")
        return data
    except Exception as e:
        logger.error(f"从 {filepath} 加载数据失败: {str(e)}")
        return default if default is not None else {}

# HTTP请求工具
def make_request(url, method="GET", headers=None, data=None, params=None, json_data=None, timeout=30, retry=3):
    """发送HTTP请求，支持代理和重试"""
    proxies = None
    if PROXY_CONFIG["enabled"]:
        proxies = {
            "http": PROXY_CONFIG["http"],
            "https": PROXY_CONFIG["https"]
        }
    
    for attempt in range(retry):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                params=params,
                json=json_data,
                proxies=proxies,
                timeout=timeout
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"请求失败 (尝试 {attempt+1}/{retry}): {str(e)}")
            if attempt == retry - 1:
                logger.error(f"请求最终失败: {str(e)}")
                raise
            time.sleep(2 * (attempt + 1))  # 指数退避

# 随机延迟
def random_delay(min_seconds=1, max_seconds=5):
    """随机延迟，模拟人类行为"""
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"随机延迟 {delay:.2f} 秒")
    time.sleep(delay)
    
# 日期时间工具
def get_current_datetime_str():
    """获取当前日期时间字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def is_time_between(start_time, end_time):
    """
    检查当前时间是否在指定时间范围内
    
    Args:
        start_time: 开始时间字符串，格式为 "HH:MM"
        end_time: 结束时间字符串，格式为 "HH:MM"
    
    Returns:
        bool: 是否在时间范围内
    """
    if not start_time or not end_time:
        return True
        
    try:
        current_time = datetime.now().time()
        start = datetime.strptime(start_time, "%H:%M").time()
        end = datetime.strptime(end_time, "%H:%M").time()
        
        if start <= end:
            return start <= current_time <= end
        else:  # 处理跨天的情况，如 23:00 - 06:00
            return start <= current_time or current_time <= end
    except Exception as e:
        logger.error(f"解析时间范围出错: {e}")
        return True  # 出错时默认允许运行

# 更新黑名单
def update_blacklist(company_name, reason):
    """更新公司黑名单"""
    blacklist = load_data("blacklist.json", default=[])
    
    # 检查公司是否已在黑名单中
    for item in blacklist:
        if item["company"] == company_name:
            # 更新原因和时间
            item["reasons"].append(reason)
            item["updated_at"] = get_current_datetime_str()
            save_data(blacklist, "blacklist.json")
            logger.info(f"更新黑名单公司: {company_name}, 原因: {reason}")
            return
    
    # 添加新公司到黑名单
    blacklist.append({
        "company": company_name,
        "reasons": [reason],
        "created_at": get_current_datetime_str(),
        "updated_at": get_current_datetime_str()
    })
    
    save_data(blacklist, "blacklist.json")
    logger.info(f"添加公司到黑名单: {company_name}, 原因: {reason}")

# 职位投递记录
def record_job_application(platform, job_id, job_title, company, status="已投递"):
    """记录职位投递"""
    applications = load_data("applications.json", default=[])
    
    # 添加新的投递记录
    applications.append({
        "platform": platform,
        "job_id": job_id,
        "job_title": job_title,
        "company": company,
        "status": status,
        "applied_at": get_current_datetime_str()
    })
    
    save_data(applications, "applications.json")
    logger.info(f"记录职位投递: {platform} - {company} - {job_title}")

# 检查是否已投递过该职位
def is_job_applied(platform, job_id):
    """检查是否已投递过该职位"""
    applications = load_data("applications.json", default=[])
    
    for app in applications:
        if app["platform"] == platform and app["job_id"] == job_id:
            logger.info(f"职位已投递过: {platform} - {job_id}")
            return True
    
    return False 