#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   Author  :   Host520
#   Date    :   2026-07-11
#   Desc    :   GitHub Action 运行的脚本
#

import argparse
from typing import Dict, List

from fetch_ips import main as fetch_ips_main
from common import generate_platform_hosts, generate_merged_hosts
from platforms import list_platforms, get_all_platforms


def update_single_platform(platform_name: str, verbose: bool = True) -> None:
    """更新单个平台"""
    print(f"\n{'='*50}")
    print(f"Updating platform: {platform_name}")
    print(f"{'='*50}")
    
    content, content_list = fetch_ips_main(verbose=verbose, platform_name=platform_name)
    
    if content:
        hosts_content = generate_platform_hosts(platform_name, content, content_list)
        if verbose:
            print(f"\n{hosts_content}")
    else:
        print(f"No IP addresses found for {platform_name}")


def update_all_platforms(verbose: bool = True) -> None:
    """更新所有平台"""
    print(f"\n{'='*50}")
    print(f"Updating all platforms")
    print(f"{'='*50}")
    
    results, all_content_list = fetch_ips_main(verbose=verbose, platform_name=None)
    
    if results:
        platform_hosts = {}
        for platform_name, (content, content_list) in results.items():
            if content:
                hosts_content = generate_platform_hosts(platform_name, content, content_list)
                platform_hosts[platform_name] = hosts_content
                if verbose:
                    print(f"\n--- {platform_name} ---")
                    print(hosts_content)
        
        # 生成合并hosts
        merged_hosts = generate_merged_hosts(platform_hosts, all_content_list)
        if verbose:
            print(f"\n{'='*50}")
            print("Merged hosts:")
            print(f"{'='*50}")
            print(merged_hosts)
    else:
        print("No IP addresses found for any platform")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Host520 - 获取各平台最新IP并生成hosts文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
可用平台: {', '.join(list_platforms())}

示例:
  python update_ips.py                          # 更新所有平台
  python update_ips.py --platform steam         # 仅更新Steam
  python update_ips.py --platform github        # 仅更新GitHub
  python update_ips.py --platform all           # 更新所有平台
  python update_ips.py --list                   # 列出所有可用平台
"""
    )
    
    parser.add_argument(
        '--platform', '-p',
        type=str,
        default='all',
        help='指定要更新的平台 (默认: all)'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='列出所有可用平台'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='静默模式，减少输出'
    )
    
    args = parser.parse_args()
    
    # 列出平台
    if args.list:
        print("可用平台:")
        for name in list_platforms():
            from platforms import get_platform
            platform = get_platform(name)
            print(f"  - {name}: {platform.DESCRIPTION}")
        return
    
    verbose = not args.quiet
    
    # 更新平台
    if args.platform == 'all':
        update_all_platforms(verbose=verbose)
    elif args.platform in list_platforms():
        update_single_platform(args.platform, verbose=verbose)
    else:
        print(f"错误: 未知平台 '{args.platform}'")
        print(f"可用平台: {', '.join(list_platforms())}")
        return


if __name__ == '__main__':
    main()
