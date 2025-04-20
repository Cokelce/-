import logging
import openai
from config import AI_CONFIG, USER_PREFERENCES

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置OpenAI API
openai.api_key = AI_CONFIG["openai_api_key"]

def analyze_job_relevance(job_description, user_profile):
    """
    分析职位与用户背景的匹配度
    
    参数:
    - job_description: 职位描述文本
    - user_profile: 用户简历和技能信息
    
    返回:
    - score: 0-100的匹配分数
    - analysis: 匹配分析结果
    """
    try:
        # 构建提示词
        prompt = f"""
        你是一位专业的职业顾问，请分析以下职位描述与求职者背景的匹配程度。
        
        ## 职位描述
        {job_description}
        
        ## 求职者背景
        {user_profile}
        
        ## 评分标准
        请基于以下因素给出0-100的匹配分数:
        1. 技能匹配度: 求职者技能与职位要求的匹配程度
        2. 经验匹配度: 求职者经验与职位要求的匹配程度
        3. 教育背景匹配度: 求职者学历与职位要求的匹配程度
        4. 行业相关度: 求职者从业背景与目标公司行业的匹配程度
        
        ## 输出格式
        仅返回JSON格式数据，包含以下字段:
        - total_score: 总分(0-100)
        - skill_score: 技能匹配分数(0-100)
        - experience_score: 经验匹配分数(0-100)
        - education_score: 教育背景匹配分数(0-100)
        - industry_score: 行业相关度分数(0-100)
        - analysis: 匹配分析(不超过200字)
        - recommendation: 是否推荐投递(true/false)
        """
        
        # 调用API
        response = openai.chat.completions.create(
            model=AI_CONFIG["model"],
            messages=[
                {"role": "system", "content": "你是一位专业的职业顾问，负责分析职位与求职者的匹配度。"},
                {"role": "user", "content": prompt}
            ],
            temperature=AI_CONFIG["temperature"],
            max_tokens=AI_CONFIG["max_tokens"],
            response_format={"type": "json_object"}
        )
        
        # 解析结果
        result = response.choices[0].message.content
        logger.info(f"职位匹配分析完成，总分: {result['total_score']}")
        
        return result
    except Exception as e:
        logger.error(f"AI分析职位匹配度失败: {str(e)}")
        # 返回默认值
        return {
            "total_score": 50,
            "skill_score": 50,
            "experience_score": 50,
            "education_score": 50,
            "industry_score": 50,
            "analysis": "AI分析失败，无法提供详细匹配信息。",
            "recommendation": False
        }

def generate_greeting_message(job_info, user_profile):
    """
    生成个性化的打招呼语
    
    参数:
    - job_info: 职位信息字典，包含职位名称、公司名称、职位描述等
    - user_profile: 用户简历和技能信息
    
    返回:
    - message: 生成的打招呼语
    """
    try:
        # 构建提示词
        prompt = f"""
        你是一位专业的求职顾问，请根据以下职位信息和求职者背景，生成一段简短有力的打招呼语。
        
        ## 职位信息
        - 职位名称: {job_info.get('title', '未知职位')}
        - 公司名称: {job_info.get('company', '未知公司')}
        - 职位描述: {job_info.get('description', '无职位描述')}
        
        ## 求职者背景
        {user_profile}
        
        ## 要求
        1. 简短有力，150字以内
        2. 表达对该职位的强烈兴趣
        3. 突出自己的核心优势，与职位要求匹配的关键技能和经验
        4. 语气自信但不傲慢，友好但专业
        5. 不要过于做作或套路化，保持真诚
        6. 不要逐条列举自己的技能，而是重点突出与职位最匹配的1-2项关键能力
        
        ## 输出
        仅返回打招呼语内容，不要包含任何其他说明或格式。
        """
        
        # 调用API
        response = openai.chat.completions.create(
            model=AI_CONFIG["model"],
            messages=[
                {"role": "system", "content": "你是一位专业的求职顾问，负责生成个性化的求职打招呼语。"},
                {"role": "user", "content": prompt}
            ],
            temperature=AI_CONFIG["temperature"],
            max_tokens=AI_CONFIG["max_tokens"]
        )
        
        # 获取结果
        message = response.choices[0].message.content.strip()
        logger.info("生成打招呼语成功")
        
        return message
    except Exception as e:
        logger.error(f"AI生成打招呼语失败: {str(e)}")
        # 返回默认模板
        return f"""您好，我对贵公司的{job_info.get('title', '职位')}很感兴趣。我有相关领域的工作经验和技能，希望能有机会进一步沟通。"""

def filter_jobs_by_ai(jobs, user_profile, threshold=70):
    """
    使用AI过滤职位列表，返回匹配度高的职位
    
    参数:
    - jobs: 职位列表
    - user_profile: 用户简历和技能信息
    - threshold: 匹配度阈值，低于此分数的职位将被过滤
    
    返回:
    - filtered_jobs: 过滤后的职位列表，每个职位添加匹配度分数
    """
    filtered_jobs = []
    
    for job in jobs:
        # 分析职位匹配度
        analysis_result = analyze_job_relevance(job["description"], user_profile)
        
        # 添加匹配信息到职位
        job["match_score"] = analysis_result["total_score"]
        job["match_analysis"] = analysis_result["analysis"]
        job["recommendation"] = analysis_result["recommendation"]
        
        # 根据阈值过滤
        if analysis_result["total_score"] >= threshold:
            filtered_jobs.append(job)
            logger.info(f"职位匹配通过: {job['title']} - 分数: {job['match_score']}")
        else:
            logger.info(f"职位匹配不通过: {job['title']} - 分数: {job['match_score']}")
    
    # 按匹配度排序
    filtered_jobs.sort(key=lambda x: x["match_score"], reverse=True)
    
    return filtered_jobs 