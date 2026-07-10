#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   Steam 平台配置
#

PLATFORM_NAME = "steam"
DESCRIPTION = "Steam 游戏平台"

# Steam 相关域名
URLS = [
    # 商店与登录
    'store.steampowered.com',
    'steamcommunity.com',
    'api.steampowered.com',
    'help.steampowered.com',
    'steampowered.com',
    # 下载与CDN
    'content.steampowered.com',
    'cdn.steamstatic.com',
    'steamcdn-a.akamaihd.net',
    'steamstatic.com',
    'store.akamai.steamstatic.com',
    'cdn.akamai.steamstatic.com',
    'community.akamai.steamstatic.com',
    # 社区功能
    'steam-chat.com',
    'steam.tv',
    'steam-api.com',
    # 用户内容
    'steamusercontent.com',
    'steamcontent.com',
    'steamserver.net',
    # 游戏相关
    'steamgames.com',
]

# hosts 文件标记
HOSTS_START_TAG = "# Steam520 Host Start"
HOSTS_END_TAG = "# Steam520 Host End"
