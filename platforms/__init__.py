#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   平台配置包
#

import importlib
import os

# 平台配置文件目录
PLATFORMS_DIR = os.path.dirname(__file__)

# 平台注册表
PLATFORMS = {}

def _load_platforms():
    """动态加载所有平台配置"""
    global PLATFORMS
    
    # 遍历platforms目录下的所有Python文件
    for filename in os.listdir(PLATFORMS_DIR):
        if filename.endswith('.py') and filename != '__init__.py':
            platform_name = filename[:-3]  # 去掉.py后缀
            try:
                # 动态导入模块
                module = importlib.import_module(f'.{platform_name}', package='platforms')
                
                # 检查模块是否包含必要的配置
                if hasattr(module, 'PLATFORM_NAME') and hasattr(module, 'URLS'):
                    PLATFORMS[platform_name] = module
            except Exception as e:
                print(f"Warning: Failed to load platform {platform_name}: {e}")

# 加载平台
_load_platforms()

def get_platform(name: str):
    """获取平台配置模块"""
    return PLATFORMS.get(name)

def get_all_platforms():
    """获取所有平台"""
    return PLATFORMS

def list_platforms():
    """列出所有可用平台"""
    return list(PLATFORMS.keys())
