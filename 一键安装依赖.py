#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def check_python_version():
    """检查Python版本是否满足要求"""
    print("检查Python版本...")
    
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        return False
    
    print(f"Python版本 {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} ✓")
    return True

def create_virtual_env():
    """创建虚拟环境"""
    create_venv = input("是否创建虚拟环境? (y/n): ").lower() == 'y'
    if create_venv:
        print("创建虚拟环境...")
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print("虚拟环境创建成功 ✓")
            
            # 确定激活脚本路径
            if platform.system() == "Windows":
                activate_script = os.path.join("venv", "Scripts", "activate")
                python_path = os.path.join("venv", "Scripts", "python")
            else:
                activate_script = os.path.join("venv", "bin", "activate")
                python_path = os.path.join("venv", "bin", "python")
            
            print(f"请使用以下命令激活虚拟环境:")
            if platform.system() == "Windows":
                print(f"    {activate_script}")
            else:
                print(f"    source {activate_script}")
                
            return python_path
        except Exception as e:
            print(f"创建虚拟环境失败: {e}")
            return sys.executable
    
    return sys.executable

def install_dependencies(python_path):
    """安装依赖包"""
    print("安装依赖包...")
    requirements_file = "requirements.txt"
    
    if not os.path.exists(requirements_file):
        print(f"错误: 未找到 {requirements_file} 文件")
        return False
    
    try:
        subprocess.run([python_path, "-m", "pip", "install", "-r", requirements_file], check=True)
        print("依赖安装完成 ✓")
        return True
    except Exception as e:
        print(f"安装依赖失败: {e}")
        return False

def create_directories():
    """创建必要的目录结构"""
    print("创建必要的目录结构...")
    
    directories = [
        "logs",
        "data",
        "data/boss",
        "data/lagou",
        "resumes",
        "platforms",
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"创建目录: {directory} ✓")
        else:
            print(f"目录已存在: {directory} ✓")
    
    return True

def create_env_file():
    """创建.env文件"""
    print("创建环境配置文件...")
    
    env_example = ".env.example"
    env_file = ".env"
    
    if os.path.exists(env_file):
        override = input(f"{env_file}文件已存在，是否覆盖? (y/n): ").lower() == 'y'
        if not override:
            print(f"保留现有{env_file}文件 ✓")
            return True
    
    if os.path.exists(env_example):
        shutil.copy(env_example, env_file)
        print(f"创建{env_file}文件 ✓")
        print(f"请记得编辑{env_file}文件，填写您的配置信息")
    else:
        # 如果没有示例文件，创建一个基本的.env文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# 智能求职助手环境配置\n")
            f.write("# 各平台Cookie\n")
            f.write("BOSS_COOKIE=\n")
            f.write("LAGOU_COOKIE=\n")
            f.write("# 企业微信通知配置（可选）\n")
            f.write("WX_CORP_ID=\n")
            f.write("WX_APP_ID=\n")
            f.write("WX_APP_SECRET=\n")
            f.write("WX_TO_USER=@all\n")
            f.write("# 代理配置（可选）\n")
            f.write("USE_PROXY=false\n")
            f.write("HTTP_PROXY=\n")
            f.write("HTTPS_PROXY=\n")
        print(f"创建基本{env_file}文件 ✓")
        print(f"请编辑{env_file}文件，填写您的配置信息")
    
    return True

def create_launch_scripts(python_path):
    """创建启动脚本"""
    print("创建启动脚本...")
    
    is_windows = platform.system() == "Windows"
    
    # 创建提取Cookie的脚本
    if is_windows:
        with open("获取Cookie.bat", 'w', encoding='utf-8') as f:
            f.write(f'@echo off\n')
            f.write(f'chcp 65001 > nul\n')  # 设置UTF-8编码
            if python_path != sys.executable:
                f.write(f'call {os.path.join("venv", "Scripts", "activate")}\n')
            f.write(f'python main.py --cookie\n')
            f.write(f'echo 按任意键退出...\n')
            f.write(f'pause > nul\n')
    else:
        with open("获取Cookie.sh", 'w', encoding='utf-8') as f:
            f.write(f'#!/bin/bash\n')
            if python_path != sys.executable:
                f.write(f'source {os.path.join("venv", "bin", "activate")}\n')
            f.write(f'python main.py --cookie\n')
        os.chmod("获取Cookie.sh", 0o755)
    
    # 创建主程序启动脚本
    if is_windows:
        with open("启动求职助手.bat", 'w', encoding='utf-8') as f:
            f.write(f'@echo off\n')
            f.write(f'chcp 65001 > nul\n')  # 设置UTF-8编码
            if python_path != sys.executable:
                f.write(f'call {os.path.join("venv", "Scripts", "activate")}\n')
            f.write(f'python main.py --run-once\n')
            f.write(f'echo 按任意键退出...\n')
            f.write(f'pause > nul\n')
        
        with open("定时任务模式.bat", 'w', encoding='utf-8') as f:
            f.write(f'@echo off\n')
            f.write(f'chcp 65001 > nul\n')  # 设置UTF-8编码
            if python_path != sys.executable:
                f.write(f'call {os.path.join("venv", "Scripts", "activate")}\n')
            f.write(f'echo 启动定时任务模式...\n')
            f.write(f'python main.py --schedule\n')
            f.write(f'pause\n')
    else:
        with open("启动求职助手.sh", 'w', encoding='utf-8') as f:
            f.write(f'#!/bin/bash\n')
            if python_path != sys.executable:
                f.write(f'source {os.path.join("venv", "bin", "activate")}\n')
            f.write(f'python main.py --run-once\n')
        os.chmod("启动求职助手.sh", 0o755)
        
        with open("定时任务模式.sh", 'w', encoding='utf-8') as f:
            f.write(f'#!/bin/bash\n')
            if python_path != sys.executable:
                f.write(f'source {os.path.join("venv", "bin", "activate")}\n')
            f.write(f'echo "启动定时任务模式..."\n')
            f.write(f'python main.py --schedule\n')
        os.chmod("定时任务模式.sh", 0o755)
    
    print("启动脚本创建完成 ✓")
    return True

def main():
    """主函数"""
    print("="*50)
    print("智能求职助手一键安装脚本")
    print("="*50)
    
    # 检查Python版本
    if not check_python_version():
        return False
    
    # 创建虚拟环境
    python_path = create_virtual_env()
    
    # 安装依赖
    if not install_dependencies(python_path):
        return False
    
    # 创建目录
    if not create_directories():
        return False
    
    # 创建.env文件
    if not create_env_file():
        return False
    
    # 创建启动脚本
    if not create_launch_scripts(python_path):
        return False
    
    print("\n"+"="*50)
    print("安装完成!")
    print("="*50)
    
    print("\n使用说明:")
    if platform.system() == "Windows":
        print("1. 运行 获取Cookie.bat 获取各平台Cookie")
        print("2. 编辑 .env 文件填写配置信息")
        print("3. 运行 启动求职助手.bat 单次运行求职助手")
        print("4. 运行 定时任务模式.bat 启动定时任务模式")
    else:
        print("1. 运行 ./获取Cookie.sh 获取各平台Cookie")
        print("2. 编辑 .env 文件填写配置信息")
        print("3. 运行 ./启动求职助手.sh 单次运行求职助手")
        print("4. 运行 ./定时任务模式.sh 启动定时任务模式")
    
    return True

if __name__ == "__main__":
    main() 