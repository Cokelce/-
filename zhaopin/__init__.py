# zhaopin 包初始化
# 用于导出平台特定爬虫模块

from .boss_scraper import BossZhipin
from .zhilian_scraper import ZhilianZhaopin
from .qiancheng_scraper import QianChengWuYou
from .lagou_scraper import LagouWang

__all__ = ['BossZhipin', 'ZhilianZhaopin', 'QianChengWuYou', 'LagouWang'] 