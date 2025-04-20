#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import argparse
import schedule
from datetime import datetime, timedelta

from config import PLATFORMS, SCHEDULE_CONFIG
from utils import ensure_dir, send_wechat_notification, is_time_between, random_delay
from platforms.boss import BossZhipin
from platforms.other_platforms import ZhilianZhaopin, QianChengWuYou, LagouWang
from cookie_extractor import CookieExtractor

# 设置日志
def setup_logging():
    """设置日志记录"""
    ensure_dir("logs")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/job_assistant.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# 创建必要的目录
def create_directories():
    """创建必要的目录结构"""
    ensure_dir("data")
    ensure_dir("data/boss")
    ensure_dir("data/zhilian")
    ensure_dir("data/qiancheng")
    ensure_dir("data/lagou")
    ensure_dir("resumes")
    ensure_dir("logs")
    
    # 复制示例文件（如果不存在正式文件）
    example_files = [
        ("data/applications.json.example", "data/applications.json"),
        ("data/blacklist.json.example", "data/blacklist.json"),
        ("data/boss/profile.json.example", "data/boss/profile.json")
    ]
    
    for example, target in example_files:
        if os.path.exists(example) and not os.path.exists(target):
            try:
                with open(example, 'r', encoding='utf-8') as src, open(target, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
                logger.info(f"创建示例文件: {target}")
            except Exception as e:
                logger.error(f"创建示例文件失败: {target}, 错误: {str(e)}")

# 单次运行所有平台
def run_all_platforms():
    """运行所有启用的平台进行求职"""
    logger.info("开始运行所有平台")
    
    # 检查当前时间是否在允许的时间范围内
    if SCHEDULE_CONFIG["enabled"] and not is_time_between(
        SCHEDULE_CONFIG.get("start_time", ""), 
        SCHEDULE_CONFIG.get("end_time", "")
    ):
        logger.info(f"当前时间不在允许的时间范围内 ({SCHEDULE_CONFIG.get('start_time', '不限')} - {SCHEDULE_CONFIG.get('end_time', '不限')})")
        return
    
    success_count = 0
    platforms_count = 0
    
    # Boss直聘
    if PLATFORMS["boss"]["enabled"]:
        platforms_count += 1
        try:
            boss = BossZhipin()
            if boss.run():
                success_count += 1
        except Exception as e:
            logger.error(f"运行Boss直聘出错: {str(e)}")
    
    # 智联招聘
    if PLATFORMS["zhilian"]["enabled"]:
        platforms_count += 1
        try:
            zhilian = ZhilianZhaopin()
            if zhilian.run():
                success_count += 1
        except Exception as e:
            logger.error(f"运行智联招聘出错: {str(e)}")
    
    # 前程无忧
    if PLATFORMS["qiancheng"]["enabled"]:
        platforms_count += 1
        try:
            qiancheng = QianChengWuYou()
            if qiancheng.run():
                success_count += 1
        except Exception as e:
            logger.error(f"运行前程无忧出错: {str(e)}")
    
    # 拉勾网
    if PLATFORMS["lagou"]["enabled"]:
        platforms_count += 1
        try:
            lagou = LagouWang()
            if lagou.run():
                success_count += 1
        except Exception as e:
            logger.error(f"运行拉勾网出错: {str(e)}")
    
    # 发送运行总结
    summary = f"本次运行总结:\n启用平台数: {platforms_count}\n成功运行: {success_count}\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    logger.info(summary.replace("\n", " | "))
    send_wechat_notification("智能求职助手运行总结", summary)

# 定时任务
def schedule_jobs():
    """设置定时任务"""
    if not SCHEDULE_CONFIG["enabled"]:
        logger.info("定时任务已禁用")
        return
    
    # 设置定时任务，按照配置的间隔时间运行
    interval_minutes = SCHEDULE_CONFIG["interval_minutes"]
    
    logger.info(f"设置定时任务，间隔时间: {interval_minutes}分钟")
    schedule.every(interval_minutes).minutes.do(run_all_platforms)
    
    # 立即运行一次
    run_all_platforms()
    
    # 持续运行定时任务
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次

# 提取Cookie
def extract_cookies():
    """运行Cookie提取器"""
    logger.info("启动Cookie提取器")
    try:
        extractor = CookieExtractor()
        extractor.run_all()
        logger.info("Cookie提取完成")
    except Exception as e:
        logger.error(f"Cookie提取出错: {str(e)}")
        print(f"\n❌ Cookie提取失败: {str(e)}")

# 提取Cookie（无头模式）
def extract_cookies_headless():
    """以无头模式运行Cookie提取器"""
    logger.info("以无头模式启动Cookie提取器")
    try:
        extractor = CookieExtractor(headless=True)
        extractor.run_all()
        logger.info("Cookie提取完成")
    except Exception as e:
        logger.error(f"Cookie提取出错: {str(e)}")
        print(f"\n❌ Cookie提取失败: {str(e)}")

# 检查是否在允许的时间范围内
def is_time_between(start_time_str, end_time_str):
    """
    检查当前时间是否在指定时间范围内
    
    Args:
        start_time_str: 开始时间字符串，格式为 "HH:MM"
        end_time_str: 结束时间字符串，格式为 "HH:MM"
    
    Returns:
        bool: 是否在时间范围内
    """
    if not start_time_str or not end_time_str:
        return True
        
    try:
        current_time = datetime.now().time()
        start = datetime.strptime(start_time_str, "%H:%M").time()
        end = datetime.strptime(end_time_str, "%H:%M").time()
        
        if start <= end:
            return start <= current_time <= end
        else:  # 处理跨天的情况，如 23:00 - 06:00
            return start <= current_time or current_time <= end
    except Exception as e:
        logger.error(f"解析时间范围出错: {e}")
        return True  # 出错时默认允许运行

# 主函数
def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="智能求职助手")
    parser.add_argument("--schedule", action="store_true", help="启用定时任务")
    parser.add_argument("--run-once", action="store_true", help="立即运行一次")
    parser.add_argument("--cookie", action="store_true", help="提取Cookie")
    parser.add_argument("--cookie-headless", action="store_true", help="无头模式提取Cookie（不显示浏览器）")
    args = parser.parse_args()
    
    # 创建必要的目录
    create_directories()
    
    # 处理Cookie提取
    if args.cookie or args.cookie_headless:
        if args.cookie_headless:
            extract_cookies_headless()
        else:
            extract_cookies()
        return
    
    # 发送启动通知
    send_wechat_notification("智能求职助手已启动", f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n模式: {'定时任务' if args.schedule else '单次运行'}")
    
    try:
        if args.schedule:
            schedule_jobs()
        elif args.run_once:
            run_all_platforms()
        else:
            parser.print_help()
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        send_wechat_notification("智能求职助手已停止", "程序被用户手动停止")
    except Exception as e:
        logger.error(f"程序异常: {str(e)}")
        send_wechat_notification("智能求职助手异常", f"程序发生异常: {str(e)}")

# 设置日志
logger = setup_logging()

if __name__ == "__main__":
    main() 