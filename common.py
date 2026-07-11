#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   Author  :   Host520
#   Date    :   2026-07-11
#   Desc    :   公共函数库
#

import os
import json
from typing import Any, Optional, List, Dict
from datetime import datetime, timezone, timedelta
from retry import retry

# DNS服务器列表（国内+海外DNS，提高解析成功率）
DNS_SERVER_LIST = [
    "223.5.5.5",       # 阿里云DNS
    "223.6.6.6",       # 阿里云DNS
    "119.29.29.29",    # 腾讯云DNS
    "119.28.28.28",    # 腾讯云DNS
    "1.1.1.1",         # Cloudflare DNS
    "101.226.4.6",     # 360 DNS
    "180.184.1.1",     # 字节跳动DNS
    "180.76.76.76",    # 百度DNS
]

# 需要丢弃的IP列表（无效或不可用的IP）
DISCARD_LIST = [
    '0.0.0.0',
    '127.0.0.1',
    '255.255.255.255',
    '1.0.1.1',
    '1.2.1.1',
    '1.1.1.1',
    '8.8.8.8',
    '223.5.5.5',
    '223.6.6.6',
    '119.29.29.29',
    '119.28.28.28',
]

# 合并hosts模板
HOSTS_TEMPLATE = """# Host520 Host Start
{content}

# Update time: {update_time}
# Update url: https://raw.githubusercontent.com/haowee/Host520/main/hosts
# Star me: https://github.com/haowee/Host520
# Host520 Host End
"""


def write_platform_hosts_file(platform_name: str, hosts_content: str) -> None:
    """写入平台专属hosts文件"""
    output_file_path = os.path.join(os.path.dirname(__file__), f'hosts_{platform_name}')
    with open(output_file_path, "w", encoding='utf-8') as output_fb:
        output_fb.write(hosts_content)


def write_platform_json_file(platform_name: str, hosts_list: list) -> None:
    """写入平台专属JSON文件"""
    output_file_path = os.path.join(os.path.dirname(__file__), f'hosts_{platform_name}.json')
    with open(output_file_path, "w", encoding='utf-8') as output_fb:
        json.dump(hosts_list, output_fb, ensure_ascii=False, indent=2)


def write_merged_hosts_file(hosts_content: str) -> None:
    """写入合并hosts文件"""
    output_file_path = os.path.join(os.path.dirname(__file__), 'hosts')
    with open(output_file_path, "w", encoding='utf-8') as output_fb:
        output_fb.write(hosts_content)


def write_merged_json_file(hosts_list: list) -> None:
    """写入合并JSON文件"""
    output_file_path = os.path.join(os.path.dirname(__file__), 'hosts.json')
    with open(output_file_path, "w", encoding='utf-8') as output_fb:
        json.dump(hosts_list, output_fb, ensure_ascii=False, indent=2)


def write_file(hosts_content: str, update_time: str) -> bool:
    """写入文件并检查是否有变化"""
    output_doc_file_path = os.path.join(os.path.dirname(__file__), "README.md")
    template_path = os.path.join(os.path.dirname(__file__), "README_template.md")
    
    write_merged_hosts_file(hosts_content)
    
    if os.path.exists(output_doc_file_path):
        with open(output_doc_file_path, "r", encoding='utf-8') as old_readme_fb:
            old_content = old_readme_fb.read()
            if old_content:
                try:
                    old_hosts = old_content.split("```bash")[1].split("```")[0].strip()
                    old_hosts = old_hosts.split("# Update time:")[0].strip()
                    hosts_content_hosts = hosts_content.split("# Update time:")[0].strip()
                    if old_hosts == hosts_content_hosts:
                        print("host not change")
                        return False
                except (IndexError, ValueError):
                    pass

    if os.path.exists(template_path):
        with open(template_path, "r", encoding='utf-8') as temp_fb:
            template_str = temp_fb.read()
            readme_content = template_str.format(hosts_str=hosts_content,
                                                  update_time=update_time)
            with open(output_doc_file_path, "w", encoding='utf-8') as output_fb:
                output_fb.write(readme_content)
    return True


def generate_platform_hosts(platform_name: str, content: str, content_list: list) -> str:
    """生成并写入平台hosts内容"""
    if not content:
        return ""
    
    update_time = datetime.now(timezone.utc).astimezone(
        timezone(timedelta(hours=8))).replace(microsecond=0).isoformat()
    
    # 导入平台配置
    from platforms import get_platform
    platform = get_platform(platform_name)
    
    # 生成平台hosts内容
    platform_hosts_template = """{start_tag}
{content}

# Update time: {update_time}
# Platform: {platform_name}
{end_tag}"""
    
    hosts_content = platform_hosts_template.format(
        start_tag=platform.HOSTS_START_TAG,
        content=content,
        update_time=update_time,
        platform_name=platform_name,
        end_tag=platform.HOSTS_END_TAG
    )
    
    # 写入平台专属文件
    write_platform_hosts_file(platform_name, hosts_content)
    write_platform_json_file(platform_name, content_list)
    
    return hosts_content


def generate_merged_hosts(platform_hosts: Dict[str, str], all_content_list: List[tuple]) -> str:
    """生成并写入合并hosts内容"""
    if not platform_hosts:
        return ""
    
    update_time = datetime.now(timezone.utc).astimezone(
        timezone(timedelta(hours=8))).replace(microsecond=0).isoformat()
    
    # 合并所有平台内容
    merged_content = ""
    for platform_name, content in platform_hosts.items():
        if content:
            merged_content += content + "\n\n"
    
    if not merged_content:
        return ""
    
    # 生成合并hosts内容
    hosts_content = HOSTS_TEMPLATE.format(
        content=merged_content,
        update_time=update_time
    )
    
    # 写入合并文件
    write_file(hosts_content, update_time)
    write_merged_json_file(all_content_list)
    
    return hosts_content
