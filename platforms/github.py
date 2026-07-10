#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   GitHub 平台配置
#

PLATFORM_NAME = "github"
DESCRIPTION = "GitHub 代码托管平台"

# GitHub 相关域名
URLS = [
    # 核心服务
    'github.com',
    'api.github.com',
    'github.io',
    'github.blog',
    'github.community',
    'githubstatus.com',
    # 登录与认证
    'login.github.com',
    'github.githubassets.com',
    # 内容与资源
    'raw.githubusercontent.com',
    'user-images.githubusercontent.com',
    'avatars.githubusercontent.com',
    'avatars0.githubusercontent.com',
    'avatars1.githubusercontent.com',
    'avatars2.githubusercontent.com',
    'avatars3.githubusercontent.com',
    'avatars4.githubusercontent.com',
    'avatars5.githubusercontent.com',
    'camo.githubusercontent.com',
    'desktop.githubusercontent.com',
    'favicons.githubusercontent.com',
    'media.githubusercontent.com',
    'objects.githubusercontent.com',
    'cloud.githubusercontent.com',
    # 下载与代码
    'codeload.github.com',
    'gist.github.com',
    'gist.githubusercontent.com',
    # CDN 与加速
    'github.global.ssl.fastly.net',
    'github.map.fastly.net',
    # AWS S3 存储
    'github-cloud.s3.amazonaws.com',
    'github-com.s3.amazonaws.com',
    'github-production-release-asset-2e65be.s3.amazonaws.com',
    'github-production-repository-file-5c1aeb.s3.amazonaws.com',
    'github-production-user-asset-6210df.s3.amazonaws.com',
    # Actions 与 CI/CD
    'pipelines.actions.githubusercontent.com',
    # 其他服务
    'central.github.com',
    'collector.github.com',
    'live.github.com',
    'education.github.com',
    'vscode.dev',
    # 私有用户图片
    'private-user-images.githubusercontent.com',
]

# hosts 文件标记
HOSTS_START_TAG = "# GitHub520 Host Start"
HOSTS_END_TAG = "# GitHub520 Host End"
