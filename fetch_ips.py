#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   Author  :   Host520
#   Date    :   2026-07-11
#   Desc    :   获取最新的平台域名对应 IP
#

import re
import sys
import random
import asyncio
import logging
from typing import List, Tuple, Optional, Dict, Any

import aiohttp
import aiodns

from common import DNS_SERVER_LIST, DISCARD_LIST

# -------------------------- 可配置参数 --------------------------

# 代理配置，国内运行请填写代理地址，例如 "http://127.0.0.1:7890"，不需要代理填 None
PROXY = None

# 最大并发数，不宜过高避免触发反爬
MAX_CONCURRENCY = 5

# 请求超时时间(秒)
REQUEST_TIMEOUT = 10

# 测速超时时间(秒)
PING_TIMEOUT = 3

# 最大重试次数
MAX_RETRY = 3

# 请求最小/最大间隔(秒)，随机延迟防反爬
MIN_DELAY = 0.5
MAX_DELAY = 1.5

# 目标测速端口
TEST_PORT = 443

# DoH (DNS over HTTPS) 服务器列表
DOH_SERVERS = [
    "https://dns.alidns.com/resolve",       # 阿里 DoH（国内视角）
    "https://doh.pub/dns-query",            # DNSPod DoH（国内视角）
    "https://dns.google/resolve",           # Google DoH（备用）
]

# DoH 请求超时时间(秒)
DOH_TIMEOUT = 5

# 延迟测试次数
PING_TEST_COUNT = 3

# ---------------------------------------------------------------

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 随机 User-Agent 池，防反爬
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

# IPv4 地址精确正则
IP_PATTERN = re.compile(
    r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
)


def windows_compatibility_check():
    """Windows 兼容性检查"""
    import platform as platform_mod
    if platform_mod.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def is_valid_public_ip(ip: str) -> bool:
    """验证 IP 是否为有效公网 IP，排除所有私有/保留段（含 CGNAT）"""
    try:
        octets = list(map(int, ip.split('.')))
        if len(octets) != 4:
            return False
        for o in octets:
            if o < 0 or o > 255:
                return False

        ip_int = (octets[0] << 24) | (octets[1] << 16) | (octets[2] << 8) | octets[3]

        reserved_ranges = [
            (167772160, 184549359),        # 10.0.0.0/8
            (1681915904, 1686110207),      # 100.64.0.0/10 (CGNAT)
            (2886729728, 2887778303),      # 172.16.0.0/12
            (3232235520, 3232301055),      # 192.168.0.0/16
            (2130706432, 2147483647),      # 127.0.0.0/8
            (0, 16777215),                 # 0.0.0.0/8
            (2240000000, 4294967295),      # D/E 类（组播/保留）
        ]
        for start, end in reserved_ranges:
            if start <= ip_int <= end:
                return False

        if ip in DISCARD_LIST:
            return False

        return True
    except (ValueError, IndexError):
        return False


async def fetch_ips_from_ipaddress(domain: str, semaphore: asyncio.Semaphore) -> List[str]:
    """从 ipaddress.com 爬取指定域名的 IP，带反爬和重试"""
    url = f"https://www.ipaddress.com/site/{domain}"
    headers = {"User-Agent": random.choice(USER_AGENTS)}

    for retry in range(MAX_RETRY):
        try:
            async with semaphore:
                await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, headers=headers, proxy=PROXY) as resp:
                        if resp.status != 200:
                            logger.warning(f"{domain} 请求失败，状态码：{resp.status}，重试：{retry+1}/{MAX_RETRY}")
                            await asyncio.sleep(2 ** (retry + 1))
                            continue
                        html = await resp.text()

                        # 优化解析：只匹配 IP 区块内容
                        try:
                            ip_section = html.split("<h3>IP Addresses</h3>")[-1].split("<h3>")[0]
                        except (IndexError, ValueError):
                            ip_section = html

                        ips = IP_PATTERN.findall(ip_section)
                        valid_ips = list(filter(is_valid_public_ip, set(ips)))
                        logger.info(f"{domain} 爬取到 {len(valid_ips)} 个有效公网 IP")
                        return valid_ips
        except Exception as e:
            logger.warning(f"{domain} 请求异常：{str(e)}，重试：{retry+1}/{MAX_RETRY}")
            await asyncio.sleep(2 ** (retry + 1))

    logger.error(f"{domain} 爬取失败，已达最大重试次数")
    return []


async def resolve_ips_from_doh(domain: str) -> List[str]:
    """通过 DNS over HTTPS (DoH) 获取 IP，优先使用国内 DoH 服务器"""
    for doh_url in DOH_SERVERS:
        try:
            timeout = aiohttp.ClientTimeout(total=DOH_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                params = {"name": domain, "type": "A"}
                headers = {"Accept": "application/dns-json"}
                async with session.get(doh_url, params=params, headers=headers) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    if data.get("Status") == 0 and "Answer" in data:
                        ips = [r["data"] for r in data["Answer"] if r.get("type") == 1]
                        valid_ips = [ip for ip in ips if is_valid_public_ip(ip)]
                        if valid_ips:
                            logger.info(f"DoH {doh_url} -> {domain}: {valid_ips}")
                            return valid_ips
        except Exception as e:
            logger.debug(f"DoH query {doh_url} for {domain} failed: {e}")
            continue
    return []


async def resolve_ips_from_dns(domain: str, resolver: aiodns.DNSResolver) -> List[str]:
    """从 DNS 解析获取候选 IP"""
    try:
        result = await resolver.query(domain, "A")
        ips = [ans.host for ans in result]
        valid_ips = list(filter(is_valid_public_ip, set(ips)))
        logger.info(f"{domain} DNS 解析到 {len(valid_ips)} 个有效公网 IP")
        return valid_ips
    except Exception as e:
        logger.warning(f"{domain} DNS 解析失败：{str(e)}")
        return []


# 延迟测试缓存
PING_CACHE: Dict[str, float] = {}


async def test_ip_latency(ip: str) -> Tuple[float, str]:
    """测试 IP 的 TCP 延迟，多次测试取中位数，带缓存"""
    if ip in PING_CACHE:
        return (PING_CACHE[ip], ip)

    latencies = []
    for _ in range(PING_TEST_COUNT):
        try:
            start = asyncio.get_event_loop().time()
            conn = asyncio.open_connection(ip, TEST_PORT)
            reader, writer = await asyncio.wait_for(conn, timeout=PING_TIMEOUT)
            latencies.append((asyncio.get_event_loop().time() - start) * 1000)
            writer.close()
            await writer.wait_closed()
        except (asyncio.TimeoutError, Exception):
            latencies.append(PING_TIMEOUT * 1000)

    latencies.sort()
    median_latency = latencies[1]  # 取中位数
    PING_CACHE[ip] = median_latency
    return (median_latency, ip)


async def select_best_ip(candidate_ips: List[str], domain: str) -> Optional[str]:
    """从候选 IP 中选择延迟最低的最优 IP"""
    if not candidate_ips:
        return None

    # 并发测速
    tasks = [test_ip_latency(ip) for ip in candidate_ips]
    results = await asyncio.gather(*tasks)

    # 按延迟升序排序，选第一个可用的
    results.sort(key=lambda x: x[0])
    for latency, ip in results:
        if latency != float('inf'):
            logger.info(f"{domain} 选出最优 IP: {ip} 延迟: {latency:.2f}ms")
            return ip

    # 如果所有 IP 都超时，回退到第一个有效 IP
    logger.warning(f"{domain} 所有 IP 延迟测试超时，使用第一个有效 IP")
    return candidate_ips[0]


async def process_domain(domain: str, semaphore: asyncio.Semaphore, resolver: aiodns.DNSResolver) -> Tuple[str, Optional[str]]:
    """处理单个域名：合并爬取+DNS+DoH 的候选 IP，选最优"""
    domain = domain.strip()
    if not domain or domain.startswith("#"):
        return (domain, None)

    # 并发获取三个来源的 IP
    ip_web_task = fetch_ips_from_ipaddress(domain, semaphore)
    ip_dns_task = resolve_ips_from_dns(domain, resolver)
    ip_doh_task = resolve_ips_from_doh(domain)

    ip_list_web, ip_list_dns, ip_list_doh = await asyncio.gather(
        ip_web_task, ip_dns_task, ip_doh_task
    )

    all_ips = list(set(ip_list_web + ip_list_dns + ip_list_doh))

    if not all_ips:
        return (domain, None)

    best_ip = await select_best_ip(all_ips, domain)
    return (domain, best_ip)


def fetch_ips_for_platform(platform_urls: List[str], verbose: bool = False) -> Tuple[str, List[Tuple[str, str]]]:
    """获取指定平台的所有域名 IP（同步入口，内部异步）"""
    windows_compatibility_check()

    if verbose:
        print(f'Start fetching IPs for platform...')

    async def _fetch_all():
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
        resolver = aiodns.DNSResolver(
            nameservers=[s.split(':')[0] for s in DNS_SERVER_LIST],
            timeout=REQUEST_TIMEOUT
        )
        tasks = [process_domain(domain, semaphore, resolver) for domain in platform_urls]
        return await asyncio.gather(*tasks)

    results = asyncio.run(_fetch_all())

    content = ""
    content_list = []

    for i, domain in enumerate(platform_urls):
        domain_result, best_ip = results[i]
        if best_ip:
            line = best_ip.ljust(30) + domain
            # 标记超时 IP
            if PING_CACHE.get(best_ip) == PING_TIMEOUT * 1000:
                line += "  # Timeout"
            content += line + "\n"
            content_list.append((best_ip, domain))

    if verbose:
        print('End fetching IPs.')

    return content, content_list


def main(verbose=False, platform_name=None):
    """主函数：获取指定平台的 IP"""
    from platforms import get_platform, get_all_platforms

    if platform_name:
        platform = get_platform(platform_name)
        if not platform:
            print(f"Unknown platform: {platform_name}")
            return None, None

        return fetch_ips_for_platform(platform.URLS, verbose)
    else:
        results = {}
        all_content_list = []

        for name, platform in get_all_platforms().items():
            print(f"\n=== Fetching {name} ===")
            content, content_list = fetch_ips_for_platform(platform.URLS, verbose)
            results[name] = (content, content_list)
            all_content_list.extend(content_list)

        return results, all_content_list


if __name__ == '__main__':
    content, content_list = main(True, 'steam')
    print("\n=== Results ===")
    print(content)
