import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 用户求职偏好
USER_PREFERENCES = {
    # 求职意向
    "job_intentions": [
        "Python开发工程师",
        "后端开发工程师",
        "全栈开发工程师",
        # 添加更多求职意向...
    ],
    
    # 目标城市
    "target_cities": [
        "北京",
        "上海",
        "深圳",
        "杭州",
        # 添加更多目标城市...
    ],
    
    # 目标薪资范围（单位：k）
    "salary_range": {
        "min": 20,  # 最低薪资期望
        "max": 50,  # 最高薪资期望
    },
    
    # 工作经验要求（年）
    "experience": {
        "min": 1,  # 最低经验要求
        "max": 5,  # 最高经验要求
    },
    
    # 学历要求
    "education": [
        "本科",
        "硕士",
        # 可选: "专科", "博士"
    ],
    
    # 公司类型
    "company_types": [
        "互联网",
        "人工智能",
        "软件开发",
        # 添加更多公司类型...
    ],
    
    # 公司规模
    "company_sizes": [
        "50-150人",
        "150-500人",
        "500-2000人",
        "2000人以上",
    ],
}

# 求职平台配置
PLATFORMS = {
    "boss": {
        "enabled": True,
        "name": "Boss直聘",
        "cookie": os.getenv("BOSS_COOKIE", ""),
        "user_id": os.getenv("BOSS_USER_ID", ""),
        "resume_path": "resumes/resume_boss.jpg",  # 图片简历路径
        "daily_limit": 100,  # 每日投递上限
    },
    "zhilian": {
        "enabled": True,
        "name": "智联招聘",
        "cookie": os.getenv("ZHILIAN_COOKIE", ""),
        "daily_limit": 50,
    },
    "qiancheng": {
        "enabled": True,
        "name": "前程无忧",
        "cookie": os.getenv("QIANCHENG_COOKIE", ""),
        "daily_limit": 50,
    },
    "lagou": {
        "enabled": True,
        "name": "拉勾网",
        "cookie": os.getenv("LAGOU_COOKIE", ""),
        "daily_limit": 30,
    },
}

# 过滤条件配置
FILTER_CONFIG = {
    # 黑名单公司（不投递）
    "blacklist_companies": [
        "某问题公司1",
        "某问题公司2",
        # 添加更多黑名单公司...
    ],
    
    # 黑名单关键词（职位描述中包含以下关键词则不投递）
    "blacklist_keywords": [
        "外包",
        "965",
        "加班",
        # 添加更多黑名单关键词...
    ],
    
    # 最低活跃度要求（HR最近登录时间，单位：小时）
    "hr_activity_threshold": 24,
    
    # 排除猎头
    "exclude_headhunter": True,
    
    # 排除已投递过的职位
    "exclude_applied": True,
}

# AI配置
AI_CONFIG = {
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "model": "gpt-4",  # 可选: "gpt-3.5-turbo"
    "temperature": 0.7,
    "max_tokens": 500,
}

# 企业微信通知配置
WECHAT_CONFIG = {
    "enabled": True,
    "corp_id": os.getenv("WECHAT_CORP_ID", ""),
    "agent_id": os.getenv("WECHAT_AGENT_ID", ""),
    "secret": os.getenv("WECHAT_SECRET", ""),
}

# 定时任务配置
SCHEDULE_CONFIG = {
    "enabled": True,
    "start_time": "09:00",  # 每日开始时间
    "end_time": "18:00",    # 每日结束时间
    "interval_minutes": 30,  # 投递间隔时间（分钟）
}

# 代理配置
PROXY_CONFIG = {
    "enabled": os.getenv("USE_PROXY", "false").lower() == "true",
    "http": os.getenv("HTTP_PROXY", ""),
    "https": os.getenv("HTTPS_PROXY", ""),
} 