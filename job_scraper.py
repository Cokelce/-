#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
求职网站爬虫主程序

此脚本用于管理多个求职网站的爬虫，支持Boss直聘、智联招聘、前程无忧和拉勾网。
可以单独运行某个平台的爬虫，也可以一次性运行多个平台的爬虫。
"""

import os
import json
import logging
import argparse
import time
import schedule
from datetime import datetime

# 导入各平台爬虫
try:
    from zhaopin.boss_scraper import BossZhipin
except ImportError:
    BossZhipin = None
    print("警告: 未找到Boss直聘爬虫模块")

try:
    from zhaopin.zhilian_scraper import ZhilianZhaopin
except ImportError:
    ZhilianZhaopin = None
    print("警告: 未找到智联招聘爬虫模块")

try:
    from zhaopin.qiancheng_scraper import QianChengWuYou
except ImportError:
    QianChengWuYou = None
    print("警告: 未找到前程无忧爬虫模块")

try:
    from zhaopin.lagou_scraper import LagouWang
except ImportError:
    LagouWang = None
    print("警告: 未找到拉勾网爬虫模块")

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("job_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_logging():
    """设置日志"""
    # 创建日志目录
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 设置日志文件名，包含日期
    log_file = os.path.join(log_dir, f"job_scraper_{datetime.now().strftime('%Y%m%d')}.log")
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger.info("日志系统初始化完成")

def create_directories():
    """创建必要的目录"""
    dirs = ["logs", "data"]
    for dir_name in dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            logger.info(f"创建目录: {dir_name}")

def run_boss():
    """运行Boss直聘爬虫"""
    if BossZhipin:
        logger.info("开始运行Boss直聘爬虫")
        try:
            boss = BossZhipin()
            result = boss.run()
            logger.info(f"Boss直聘爬虫运行{'成功' if result else '失败'}")
            return result
        except Exception as e:
            logger.error(f"Boss直聘爬虫运行出错: {e}")
            return False
    else:
        logger.warning("Boss直聘爬虫模块未找到，跳过")
        return False

def run_zhilian():
    """运行智联招聘爬虫"""
    if ZhilianZhaopin:
        logger.info("开始运行智联招聘爬虫")
        try:
            zhilian = ZhilianZhaopin()
            result = zhilian.run()
            logger.info(f"智联招聘爬虫运行{'成功' if result else '失败'}")
            return result
        except Exception as e:
            logger.error(f"智联招聘爬虫运行出错: {e}")
            return False
    else:
        logger.warning("智联招聘爬虫模块未找到，跳过")
        return False

def run_qiancheng():
    """运行前程无忧爬虫"""
    if QianChengWuYou:
        logger.info("开始运行前程无忧爬虫")
        try:
            qiancheng = QianChengWuYou()
            result = qiancheng.run()
            logger.info(f"前程无忧爬虫运行{'成功' if result else '失败'}")
            return result
        except Exception as e:
            logger.error(f"前程无忧爬虫运行出错: {e}")
            return False
    else:
        logger.warning("前程无忧爬虫模块未找到，跳过")
        return False

def run_lagou():
    """运行拉勾网爬虫"""
    if LagouWang:
        logger.info("开始运行拉勾网爬虫")
        try:
            lagou = LagouWang()
            result = lagou.run()
            logger.info(f"拉勾网爬虫运行{'成功' if result else '失败'}")
            return result
        except Exception as e:
            logger.error(f"拉勾网爬虫运行出错: {e}")
            return False
    else:
        logger.warning("拉勾网爬虫模块未找到，跳过")
        return False

def run_all_platforms():
    """运行所有平台爬虫"""
    logger.info("开始运行所有平台爬虫")
    
    results = {
        "boss": run_boss(),
        "zhilian": run_zhilian(),
        "qiancheng": run_qiancheng(),
        "lagou": run_lagou()
    }
    
    # 统计成功数量
    success_count = sum(1 for result in results.values() if result)
    logger.info(f"所有平台爬虫运行完成，成功 {success_count} 个，失败 {4 - success_count} 个")
    
    # 保存运行结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = os.path.join("data", f"result_{timestamp}.json")
    try:
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": timestamp,
                "results": results
            }, f, ensure_ascii=False)
        logger.info(f"运行结果已保存到: {result_file}")
    except Exception as e:
        logger.error(f"保存运行结果失败: {e}")
    
    return success_count > 0

def schedule_jobs(run_time="10:00"):
    """设置定时任务
    
    Args:
        run_time: 运行时间，格式为"HH:MM"
    """
    logger.info(f"设置定时任务，每天 {run_time} 运行")
    
    # 设置定时任务
    schedule.every().day.at(run_time).do(run_all_platforms)
    
    logger.info("定时任务已设置，按 Ctrl+C 退出程序")
    
    # 运行定时任务
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("用户中断，程序退出")
            break
        except Exception as e:
            logger.error(f"定时任务出错: {e}")
            time.sleep(300)  # 出错后等待5分钟再继续

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="求职网站爬虫主程序")
    parser.add_argument("--platform", "-p", choices=["boss", "zhilian", "qiancheng", "lagou", "all"], 
                        default="all", help="指定要运行的平台，默认为全部")
    parser.add_argument("--schedule", "-s", action="store_true", help="设置定时任务")
    parser.add_argument("--time", "-t", default="10:00", help="定时任务运行时间，格式为HH:MM，默认为10:00")
    
    args = parser.parse_args()
    
    # 初始化
    setup_logging()
    create_directories()
    
    # 根据参数运行相应的平台
    if args.schedule:
        schedule_jobs(args.time)
    else:
        if args.platform == "boss":
            run_boss()
        elif args.platform == "zhilian":
            run_zhilian()
        elif args.platform == "qiancheng":
            run_qiancheng()
        elif args.platform == "lagou":
            run_lagou()
        else:  # all
            run_all_platforms()

if __name__ == "__main__":
    main() 