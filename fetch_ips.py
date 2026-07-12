#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   Author  :   Host520
#   Date    :   2026-07-11
#   Desc    :   获取最新的平台域名对应 IP
#

import sys
import asyncio
import logging
from typing import List, Tuple, Optional, Dict, Any

import aiohttp
import aiodns

from retry import retry

from common import DNS_SERVER_LIST, DISCARD_LIST

# -------------------------- 可配置参数 --------------------------

# 请求超时时间(秒)
REQUEST_TIMEOUT = 10

# 测速超时时间(秒)
PING_TIMEOUT = 3

# 最大重试次数
MAX_RETRY = 3

# 目标测速端口
TEST_PORT = 443

# DoH (DNS over HTTPS) 服务器列表
DOH_SERVERS = [
    "https://dns.alidns.com/resolve",       # 阿里 DoH（国内视角）
    "https://doh.pub/dns-query",            # DNSPod DoH（国内视角）
    "https://cloudflare-dns.com/dns-query", # Cloudflare DoH（海外备选）
    "https://dns.google/resolve",           # Google DoH（海外备选）
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
            (3758096384, 4294967295),      # 224.0.0.0/3（组播+保留）
        ]
        for start, end in reserved_ranges:
            if start <= ip_int <= end:
                return False

        if ip in DISCARD_LIST:
            return False

        return True
    except (ValueError, IndexError):
        return False


async def _query_doh_single(doh_url: str, domain: str) -> List[str]:
    """查询单个 DoH 服务器"""
    for retry in range(MAX_RETRY):
        try:
            timeout = aiohttp.ClientTimeout(total=DOH_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                params = {"name": domain, "type": "A"}
                headers = {"Accept": "application/dns-json"}
                async with session.get(doh_url, params=params, headers=headers) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(1)
                        continue
                    data = await resp.json()
                    if data.get("Status") == 0 and "Answer" in data:
                        ips = [r["data"] for r in data["Answer"] if r.get("type") == 1]
                        valid_ips = [ip for ip in ips if is_valid_public_ip(ip)]
                        if valid_ips:
                            return valid_ips
        except Exception as e:
            logger.debug(f"DoH query {doh_url} for {domain} failed (retry {retry+1}): {e}")
            await asyncio.sleep(1)
    return []


async def resolve_ips_from_doh(domain: str) -> List[str]:
    """通过 DNS over HTTPS (DoH) 获取 IP，并行查询所有 DoH 服务器并合并结果"""
    tasks = [_query_doh_single(url, domain) for url in DOH_SERVERS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_ips = []
    for ips in results:
        if isinstance(ips, list):
            all_ips.extend(ips)

    merged = list(set(all_ips))
    if merged:
        logger.info(f"DoH 并行查询 {domain}: {merged}")
    return merged


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

    # 如果所有 IP 都超时，跳过该域名
    logger.warning(f"{domain} 所有 IP 延迟测试超时，跳过")
    return None


async def process_domain(domain: str, resolver: aiodns.DNSResolver) -> Tuple[str, Optional[str]]:
    """处理单个域名：合并 DNS+DoH 的候选 IP，选最优"""
    domain = domain.strip()
    if not domain or domain.startswith("#"):
        return (domain, None)

    # 并发获取两个来源的 IP
    ip_dns_task = resolve_ips_from_dns(domain, resolver)
    ip_doh_task = resolve_ips_from_doh(domain)

    ip_list_dns, ip_list_doh = await asyncio.gather(
        ip_dns_task, ip_doh_task
    )

    all_ips = list(set(ip_list_dns + ip_list_doh))

    if not all_ips:
        return (domain, None)

    best_ip = await select_best_ip(all_ips, domain)
    return (domain, best_ip)


async def _fetch_remote_data(url: str) -> Optional[List[Tuple[str, str]]]:
    """从远程 URL 获取已解析的 IP 数据"""
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.warning(f"远程数据源 {url} 返回状态码 {resp.status}")
                    return None
                data = await resp.json()
                if isinstance(data, list):
                    return [(item[0], item[1]) for item in data if len(item) >= 2]
                logger.warning(f"远程数据源 {url} 格式异常: {type(data)}")
                return None
    except Exception as e:
        logger.warning(f"获取远程数据源 {url} 失败: {e}")
        return None


def fetch_ips_for_platform(
    platform_urls: List[str], verbose: bool = False,
    remote_data_url: Optional[str] = None
) -> Tuple[str, List[Tuple[str, str]]]:
    """获取指定平台的所有域名 IP（同步入口，内部异步）"""
    windows_compatibility_check()

    if verbose:
        print('Start fetching IPs for platform...')

    # 1. 远程数据源（优先使用）
    remote_map: Dict[str, str] = {}
    if remote_data_url:
        remote_data = asyncio.run(_fetch_remote_data(remote_data_url))
        if remote_data:
            allowed = set(platform_urls)
            for ip, domain in remote_data:
                if domain in allowed and is_valid_public_ip(ip):
                    remote_map[domain] = ip
            if verbose:
                print(f"从远程数据源获取到 {len(remote_map)} 个域名的 IP")

    # 2. DNS 解析（远程数据源未覆盖的域名）
    dns_urls = [d for d in platform_urls if d not in remote_map]

    dns_results_map: Dict[str, Optional[str]] = {}
    if dns_urls:
        async def _fetch_all():
            resolver = aiodns.DNSResolver(
                nameservers=[s.split(':')[0] for s in DNS_SERVER_LIST],
                timeout=REQUEST_TIMEOUT
            )
            tasks = [process_domain(domain, resolver) for domain in dns_urls]
            return await asyncio.gather(*tasks)

        dns_results = asyncio.run(_fetch_all())
        for domain, best_ip in dns_results:
            dns_results_map[domain] = best_ip
        if verbose and dns_urls:
            print(f"DNS 解析到 {len(dns_results_map)} 个域名")

    # 3. 合并结果（按 platform_urls 顺序输出）
    content = ""
    content_list = []

    for domain in platform_urls:
        ip = remote_map.get(domain) or dns_results_map.get(domain)
        if ip:
            line = ip.ljust(30) + domain
            if PING_CACHE.get(ip) == PING_TIMEOUT * 1000:
                line += "  # Timeout"
            content += line + "\n"
            content_list.append((ip, domain))

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

        remote_url = getattr(platform, 'REMOTE_DATA_URL', None)
        return fetch_ips_for_platform(platform.URLS, verbose, remote_data_url=remote_url)
    else:
        results = {}
        all_content_list = []

        for name, platform in get_all_platforms().items():
            print(f"\n=== Fetching {name} ===")
            remote_url = getattr(platform, 'REMOTE_DATA_URL', None)
            content, content_list = fetch_ips_for_platform(
                platform.URLS, verbose, remote_data_url=remote_url
            )
            results[name] = (content, content_list)
            all_content_list.extend(content_list)

        return results, all_content_list


if __name__ == '__main__':
    content, content_list = main(True, 'steam')
    print("\n=== Results ===")
    print(content)
