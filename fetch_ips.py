#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   Author  :   Host520
#   Date    :   2026-07-11
#   Desc    :   获取最新的平台域名对应 IP
#

import re
import sys
import platform
import asyncio
from typing import Any, Optional, List
from requests_html import HTMLSession
from retry import retry
import aiodns

from common import DNS_SERVER_LIST, DISCARD_LIST


def windows_compatibility_check():
    """Windows兼容性检查"""
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@retry(tries=3)
def get_ip_list_from_ipaddress_com(session: Any, domain: str) -> Optional[List[str]]:
    """从ipaddress.com获取IP列表"""
    url = f'https://sites.ipaddress.com/{domain}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
                      ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/1'
                      '06.0.0.0 Safari/537.36'}
    try:
        rs = session.get(url, headers=headers, timeout=5)
        pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
        ip_list = re.findall(pattern, rs.html.text)
        return ip_list
    except Exception as ex:
        print(f"get: {url}, error: {ex}")
        raise Exception


async def get_ip_list_from_dns(
    domain,
    record_type="A",
    dns_server_list=["223.5.5.5", "119.29.29.29"],
):
    """从DNS服务器获取IP列表"""
    windows_compatibility_check()

    resolver = aiodns.DNSResolver()
    resolver.nameservers = dns_server_list

    try:
        result = await resolver.query(domain, record_type)
        return [answer.host for answer in result]
    except aiodns.error.DNSError as e:
        print(f"{domain}: DNS 查询失败: {e}")
        return []


def is_valid_public_ip(ip: str) -> bool:
    """检查IP是否是有效的公共IP地址"""
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        # 解析IP地址的每个部分
        nums = [int(part) for part in parts]
        
        # 检查是否在有效范围内
        for num in nums:
            if num < 0 or num > 255:
                return False
        
        # 排除私有IP地址
        if nums[0] == 10:  # 10.0.0.0/8
            return False
        if nums[0] == 172 and 16 <= nums[1] <= 31:  # 172.16.0.0/12
            return False
        if nums[0] == 192 and nums[1] == 168:  # 192.168.0.0/16
            return False
        
        # 排除保留IP地址
        if nums[0] == 127:  # 127.0.0.0/8 (loopback)
            return False
        if nums[0] == 0:  # 0.0.0.0/8
            return False
        if nums[0] == 169 and nums[1] == 254:  # 169.254.0.0/16 (link-local)
            return False
        if nums[0] >= 224:  # 224.0.0.0/4 (multicast) 和更高范围
            return False
        
        # 排除其他保留地址
        if ip in DISCARD_LIST:
            return False
        
        return True
    except (ValueError, IndexError):
        return False


def select_ip_from_list(ip_list: List[str], domain: str = "") -> Optional[str]:
    """从IP列表中选择最优IP"""
    # 首先尝试选择有效的公共IP
    valid_ips = [ip for ip in ip_list if is_valid_public_ip(ip)]
    if not valid_ips:
        return None
    
    # 返回第一个有效IP
    return valid_ips[0]


async def get_ip(session: Any, domain: str) -> Optional[str]:
    """获取域名的最优IP"""
    ip_list_web = []
    try:
        ip_list_web = get_ip_list_from_ipaddress_com(session, domain)
    except Exception as ex:
        pass
    
    ip_list_dns = []
    try:
        ip_list_dns = await get_ip_list_from_dns(domain, dns_server_list=DNS_SERVER_LIST)
    except Exception as ex:
        pass
    
    ip_list_set = set(ip_list_web + ip_list_dns)
    for discard_ip in DISCARD_LIST:
        ip_list_set.discard(discard_ip)
    
    ip_list = list(ip_list_set)
    ip_list.sort()
    
    if len(ip_list) == 0:
        return None
    
    print(f"{domain}: {ip_list}")
    best_ip = select_ip_from_list(ip_list, domain)
    return best_ip


def fetch_ips_for_platform(platform_urls: List[str], verbose: bool = False) -> tuple:
    """获取指定平台的所有域名IP"""
    if verbose:
        print(f'Start fetching IPs for platform...')
    
    session = HTMLSession()
    content = ""
    content_list = []
    
    for index, domain in enumerate(platform_urls):
        try:
            ip = asyncio.run(get_ip(session, domain))
            if ip:
                content += ip.ljust(30) + domain + "\n"
                content_list.append((ip, domain))
        except Exception as ex:
            continue
        
        if verbose:
            print(f'process url: {index + 1}/{len(platform_urls)}')
    
    if verbose:
        print('End fetching IPs.')
    
    return content, content_list


def main(verbose=False, platform_name=None):
    """主函数：获取指定平台的IP"""
    from platforms import get_platform, get_all_platforms
    
    if platform_name:
        # 获取指定平台
        platform = get_platform(platform_name)
        if not platform:
            print(f"Unknown platform: {platform_name}")
            return None, None
        
        return fetch_ips_for_platform(platform.URLS, verbose)
    else:
        # 获取所有平台
        results = {}
        all_content_list = []
        
        for name, platform in get_all_platforms().items():
            print(f"\n=== Fetching {name} ===")
            content, content_list = fetch_ips_for_platform(platform.URLS, verbose)
            results[name] = (content, content_list)
            all_content_list.extend(content_list)
        
        return results, all_content_list


if __name__ == '__main__':
    # 测试单个平台
    content, content_list = main(True, 'steam')
    print("\n=== Results ===")
    print(content)
