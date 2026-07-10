# Host520 

Host520 让你更流畅地访问 Steam、GitHub 等平台，解决访问时图裂、加载慢的问题。

> 本项目无需安装任何程序，仅需 5 分钟。

通过修改本地 hosts 文件，试图解决：
- Steam 商店访问速度慢的问题
- Steam 商店中的图片显示不出的问题
- GitHub 访问速度慢的问题
- GitHub 项目中的图片显示不出的问题

## 一、IP来源说明

本项目的 IP 地址通过以下 DNS 服务器解析获取：

| DNS 服务商 | 地址 | 说明 |
|-----------|------|------|
| 阿里云 DNS | 223.5.5.5, 223.6.6.6 | 国内主流 DNS，响应速度快 |
| 腾讯云 DNS | 119.29.29.29, 119.28.28.28 | 国内主流 DNS，覆盖范围广 |

**IP 获取流程：**
1. 从 ipaddress.com 网站爬取 IP 列表
2. 通过多个国内 DNS 服务器解析获取 IP
3. 合并去重后选择最优 IP

## 二、支持平台

| 平台 | 说明 | 文件 |
|------|------|------|
| Steam | 游戏平台 | `hosts_steam` |
| GitHub | 代码托管平台 | `hosts_github` |
| 合并 | 所有平台合并 | `hosts` |

## 三、使用方法

下面的地址无需访问 GitHub 即可获取到最新的 hosts 内容：

- 合并文件：`https://raw.githubusercontent.com/haowee/Host520/main/hosts`
- Steam：`https://raw.githubusercontent.com/haowee/Host520/main/hosts_steam`
- GitHub：`https://raw.githubusercontent.com/haowee/Host520/main/hosts_github`

### 3.1 手动方式

#### 复制下面的内容

```bash
# Host520 Host Start
# GitHub520 Host Start
20.205.243.166                github.com
20.205.243.168                api.github.com
185.199.108.153               github.io
192.0.66.2                    github.blog
140.82.114.18                 github.community
185.199.108.153               githubstatus.com
20.205.243.166                github.com
185.199.108.215               github.githubassets.com
185.199.108.133               raw.githubusercontent.com
185.199.108.133               user-images.githubusercontent.com
185.199.108.133               avatars.githubusercontent.com
185.199.108.133               avatars0.githubusercontent.com
185.199.108.133               avatars1.githubusercontent.com
185.199.108.133               avatars2.githubusercontent.com
185.199.108.133               avatars3.githubusercontent.com
185.199.108.133               avatars4.githubusercontent.com
185.199.108.133               avatars5.githubusercontent.com
185.199.108.133               camo.githubusercontent.com
185.199.108.133               desktop.githubusercontent.com
185.199.108.133               favicons.githubusercontent.com
185.199.108.133               media.githubusercontent.com
185.199.108.133               objects.githubusercontent.com
185.199.108.133               cloud.githubusercontent.com
20.205.243.165                codeload.github.com
37.61.54.158                  gist.github.com
185.199.108.133               gist.githubusercontent.com
128.121.146.235               github.global.ssl.fastly.net
185.199.108.133               github.map.fastly.net
185.199.108.215               github.githubassets.com
16.15.183.173                 github-cloud.s3.amazonaws.com
16.15.207.150                 github-com.s3.amazonaws.com
16.15.183.56                  github-production-release-asset-2e65be.s3.amazonaws.com
16.15.212.107                 github-production-repository-file-5c1aeb.s3.amazonaws.com
16.15.212.164                 github-production-user-asset-6210df.s3.amazonaws.com
13.107.42.16                  pipelines.actions.githubusercontent.com
140.82.113.22                 central.github.com
140.82.113.21                 collector.github.com
140.82.114.26                 live.github.com
140.82.113.22                 education.github.com
150.171.110.103               vscode.dev
185.199.108.133               private-user-images.githubusercontent.com


# Update time: 2026-07-11T02:08:21+08:00
# Platform: github
# GitHub520 Host End

# Steam520 Host Start
92.122.17.67                  store.steampowered.com
80.87.199.46                  steamcommunity.com
23.59.52.127                  api.steampowered.com
23.59.52.127                  help.steampowered.com
23.59.42.243                  steampowered.com
199.232.163.52                cdn.steamstatic.com
96.16.250.16                  steamcdn-a.akamaihd.net
23.209.125.18                 store.akamai.steamstatic.com
23.209.125.14                 cdn.akamai.steamstatic.com
23.209.125.20                 community.akamai.steamstatic.com
23.59.42.243                  steam-chat.com
23.59.42.243                  steam.tv
184.25.219.75                 steamgames.com


# Update time: 2026-07-11T02:08:21+08:00
# Platform: steam
# Steam520 Host End



# Update time: 2026-07-11T02:08:21+08:00
# Update url: https://raw.githubusercontent.com/haowee/Host520/main/hosts
# Star me: https://github.com/haowee/Host520
# Host520 Host End

```

#### 修改 hosts 文件

hosts 文件在每个系统的位置不一，详情如下：
- Windows 系统：`C:\Windows\System32\drivers\etc\hosts`
- Linux 系统：`/etc/hosts`
- Mac（苹果电脑）系统：`/etc/hosts`
- Android（安卓）系统：`/system/etc/hosts`
- iPhone（iOS）系统：`/etc/hosts`

修改方法，把第一步的内容复制到文本末尾：
1. Windows 使用记事本。
2. Linux、Mac 使用 Root 权限：`sudo vi /etc/hosts`。
3. iPhone、iPad 须越狱、Android 必须要 root。

#### 激活生效

大部分情况下是直接生效，如未生效可尝试下面的办法，刷新 DNS：

1. Windows：在 CMD 窗口输入：`ipconfig /flushdns`
2. Linux 命令：`sudo nscd restart`，如报错则须安装：`sudo apt install nscd` 或 `sudo /etc/init.d/nscd restart`
3. Mac 命令：`sudo killall -HUP mDNSResponder`

**Tips：** 上述方法无效可以尝试重启机器。

### 3.2 自动方式（SwitchHosts）

**Tip：** 推荐 [SwitchHosts](https://github.com/oldj/SwitchHosts) 工具管理 hosts

以 SwitchHosts 为例，看一下怎么使用的，配置参考下面：
- Hosts 类型: `Remote`
- Hosts 标题: 随意
- URL: `https://raw.githubusercontent.com/haowee/Host520/main/hosts`
- 自动刷新: 最好选 `1 小时`

这样每次 hosts 有更新都能及时进行更新，免去手动更新。

### 3.3 一行命令

#### Windows

使用命令需要安装[git bash](https://gitforwindows.org/)

复制以下命令保存到本地命名为**fetch_hosts**

```shell
_hosts=$(mktemp /tmp/hostsXXX)
hosts=/c/Windows/System32/drivers/etc/hosts
remote=https://raw.githubusercontent.com/haowee/Host520/main/hosts
reg='/# Host520 Host Start/,/# Host520 Host End/d'

sed "$reg" $hosts > "$_hosts"
curl "$remote" >> "$_hosts"
cat "$_hosts" > "$hosts"

rm "$_hosts"
```

在**CMD**中执行以下命令，执行前需要替换 `git-bash.exe` 和 `fetch_hosts` 为你本地的路径，注意前者为windows路径格式后者为shell路径格式

`"C:\Program Files\Git\git-bash.exe" -c "/c/Users/XXX/fetch_hosts"`

可以将上述命令添加到windows的task schedular（任务计划程序）中以定时执行

#### GNU（Ubuntu/CentOS/Fedora）

`sudo sh -c 'sed -i "/# Host520 Host Start/Q" /etc/hosts && curl https://raw.githubusercontent.com/haowee/Host520/main/hosts >> /etc/hosts'`

#### BSD/macOS

`sudo sed -i "" "/# Host520 Host Start/,/# Host520 Host End/d" /etc/hosts && curl https://raw.githubusercontent.com/haowee/Host520/main/hosts | sudo tee -a /etc/hosts`

将上面的命令添加到 cron，可定时执行。使用前确保 Host520 内容在该文件最后部分。

**在 Docker 中运行，若遇到 `Device or resource busy` 错误，可使用以下命令执行**

`cp /etc/hosts ~/hosts.new && sed -i "/# Host520 Host Start/Q" ~/hosts.new && curl https://raw.githubusercontent.com/haowee/Host520/main/hosts >> ~/hosts.new && cp -f ~/hosts.new /etc/hosts`

### 3.4 AdGuard 用户（自动方式）

在 **过滤器>DNS 封锁清单>添加阻止列表>添加一个自定义列表**，配置如下：
- 名称：随意
- URL：`https://raw.githubusercontent.com/haowee/Host520/main/hosts`（和上面 SwitchHosts 使用的一样）

更新间隔在 **设置 > 常规设置 > 过滤器更新间隔（设置一小时一次即可）**，记得勾选上 **使用过滤器和 Hosts 文件以拦截指定域名**。

**Tip：** 不要添加在 **DNS 允许清单** 内，只能添加在 **DNS 封锁清单** 才管用。

## 四、效果对比

### Steam 商店

修改前：加载缓慢，图片无法显示

修改后：快速加载，图片正常显示

### GitHub

修改前：访问超时，图片无法显示

修改后：快速访问，图片正常显示

## 五、扩展平台

本项目支持扩展新平台，只需：

1. 在 `platforms/` 目录下创建新文件（如 `docker.py`）
2. 定义 `PLATFORM_NAME`、`URLS`、`HOSTS_START_TAG`、`HOSTS_END_TAG`

```python
# platforms/docker.py

PLATFORM_NAME = "docker"
DESCRIPTION = "Docker 容器平台"

# Docker 相关域名
URLS = [
    'docker.io',
    'registry-1.docker.io',
    'hub.docker.com',
]

# hosts 文件标记
HOSTS_START_TAG = "# Docker520 Host Start"
HOSTS_END_TAG = "# Docker520 Host End"
```

无需手动注册，系统会自动加载 `platforms/` 目录下的所有平台配置。

## 六、TODO

- [x] 定时自动更新 hosts 内容
- [x] hosts 内容无变动不会更新
- [x] 寻到最优 IP 解析结果
- [x] 支持多平台（Steam、GitHub）
- [x] 命令行参数控制

## 七、致谢

本项目参考了 [GitHub520](https://github.com/521xueweihan/GitHub520) 项目，使用 opencode + mimov2.5 AI 助手从零生成。
