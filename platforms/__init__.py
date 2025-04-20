# Platforms package initialization
# This module contains platform-specific implementations for different job sites

from .boss import BossZhipin
from .other_platforms import ZhilianZhaopin, QianChengWuYou, LagouWang, JobPlatform

__all__ = ['BossZhipin', 'ZhilianZhaopin', 'QianChengWuYou', 'LagouWang', 'JobPlatform'] 