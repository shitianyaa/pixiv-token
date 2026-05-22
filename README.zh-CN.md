# Pixiv OAuth Token Fetcher

🌍 [English](README.md) | [简体中文](README.zh-CN.md)

使用 Python + Playwright 自动模拟 Pixiv OAuth 登录流程，提取授权码，并换取 access_token。

本仓库 fork 自 [piglig/pixiv-token](https://github.com/piglig/pixiv-token)，主要增强了当前 Pixiv 登录流程下的 OAuth 回调捕获稳定性。
上游来源说明和原 MIT License 均保留。

---

## 📦 功能亮点

- ✅ 自动化模拟 Pixiv 登录流程（用户名密码）
- ✅ 支持无头模式
- ✅ 支持窗口模式（非无头）
- ✅ 获取 access_token 与 refresh_token
- ✅ 缓慢输入以降低机器人检测干扰

---

## 🔁 本 Fork 变更

本 fork 保留原项目目标，并针对当前 Pixiv 登录流程补充了一些实用兼容性改动：

- 通过 CDP、Playwright 事件、页面注入脚本和手动兜底多路捕获授权码
- 支持自动使用系统 Chrome / Edge，也可通过 `PIXIV_BROWSER_PATH` 指定浏览器
- 可使用已有 `refresh_token` 刷新 access token
- 可配置页面导航超时、授权码捕获超时、登录输入框等待超时、请求超时和输入延迟
- 异常路径显式清理浏览器资源，并提供明确的 token 交换错误信息
- 默认显示浏览器窗口，方便处理 Pixiv 可能出现的人机验证
- 支持在终端交互式输入账号和密码
- 自动跳过安全设置提示页面（Passkeys / 2FA 提醒）
- 多选择器兼容 Pixiv 登录表单变化

---

## 🚀 安装方式

### 1. 克隆项目

```bash
git clone https://github.com/shitianyaa/pixiv-token.git
cd pixiv-token
```

### 2. 安装依赖

推荐 Python 版本：`>=3.8`

```bash
pip install -r requirements.txt
playwright install chromium
```

如果本机已经安装 Chrome 或 Edge，本 fork 会在 Windows 上自动尝试使用系统浏览器。也可以手动指定浏览器路径：

```powershell
$env:PIXIV_BROWSER_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
```

依赖示例：

```txt
requests==2.32.2
playwright>=1.51.0
```

---

## ⚙️ 使用方法

### 命令行方式

```bash
# 显示浏览器窗口（默认），工具会提示输入账号和密码
python pixiv_token_fetcher.py

# 也可以显式传入账号密码
python pixiv_token_fetcher.py -u "你的邮箱" -p "你的密码"

# 无头模式
python pixiv_token_fetcher.py --headless

# 自定义超时和输入速度
python pixiv_token_fetcher.py \
  --capture-timeout 90 \
  --input-timeout 5000 \
  --navigation-timeout 90000 \
  --request-timeout 45 \
  --typing-delay 0.05
```

### 作为模块调用

```python
from pixiv_token_fetcher import PixivTokenError, PixivTokenFetcher

fetcher = PixivTokenFetcher(
    username="你的Pixiv账号",
    password="你的Pixiv密码",
    headless=False,  # 设为 True 隐藏浏览器窗口
    capture_timeout=60,  # 等待 OAuth 回调捕获的秒数
    input_timeout=3000,  # 每个登录输入框选择器的等待毫秒数
    navigation_timeout=60000,  # 登录页导航等待毫秒数
    request_timeout=30,  # token HTTP 请求等待秒数
    typing_delay=0.08,  # 每个字符之间的输入间隔秒数
)
code = fetcher.fetch_code()
if code:
    try:
        token_info = fetcher.exchange_token(code)
    except PixivTokenError as exc:
        raise RuntimeError(f"Token 交换失败：{exc}") from exc

    print("Access Token:", token_info.get("access_token"))
    print("Refresh Token:", token_info.get("refresh_token"))

# 后续可以复用已有 refresh token 获取新的 access token。
refreshed_info = fetcher.refresh_token("已有的_refresh_token")
print("New Access Token:", refreshed_info.get("access_token"))
```

---

## 🔧 工作原理

1. **PKCE 生成** — 生成 `code_verifier` 和 `code_challenge` 用于 OAuth PKCE 流程
2. **浏览器启动** — 优先使用系统 Chrome / Edge，找不到时回退到 Playwright Chromium
3. **自动登录** — 以缓慢输入方式填写邮箱和密码，模拟真人操作
4. **授权码捕获** — 从 CDP 网络/导航事件、Playwright 请求/响应/Frame 事件，以及页面注入脚本中捕获 `pixiv://account/login?code=...` 回调
5. **安全提示处理** — 若 Pixiv 弹出 Passkeys/2FA 设置页面，自动点击"稍后提醒"/"跳过"
6. **手动兜底** — 如果自动捕获失败，可以在终端粘贴完整回调 URL 或原始授权码
7. **资源清理** — 即使登录或捕获过程失败，也会在 `finally` 中关闭浏览器上下文和浏览器
8. **Token 交换 / 刷新** — 通过 Pixiv OAuth API 将授权码换取 access token 和 refresh token，或使用已有 refresh token 刷新 access token，并带有 HTTP 超时、状态码检查和 JSON 校验

---

## 📌 注意事项

- ⚠️ 请勿在生产环境中硬编码账号密码，建议使用环境变量或密钥管理工具。
- 🔐 如果在交互式终端中省略 `--username` 或 `--password`，工具会提示输入；密码输入不会回显。
- ❌ 本项目非 Pixiv 官方 SDK，Pixiv 页面结构变化可能影响运行。
- 🛡 使用时请遵守 Pixiv 的服务条款。
- 🔁 Refresh token 有效期很长，通常只需运行一次即可。
- ⏱ 如果 Pixiv 登录较慢或需要额外验证，可以增大 `--navigation-timeout` 或 `--capture-timeout`。
- 🧩 如果在其他项目中导入本工具，可以在你的应用中配置 Python `logging` 来控制状态输出。

---

## 🧪 示例输出

```
Opening Pixiv login page...
Login URL: https://app-api.pixiv.net/web/v1/login?...
Username input completed
Password input completed
Login submitted
  Clicking 'Remind me later' to skip security prompt
Code captured from console script: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Access Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Refresh Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 📝 授权协议

MIT License

---

## 🙋‍♀️ 贡献与反馈

欢迎提交 Pull Request 和 Issue！

---

## 🙏 上游项目

原项目：[piglig/pixiv-token](https://github.com/piglig/pixiv-token)

---

## 📫 联系方式

- GitHub: [shitianyaa](https://github.com/shitianyaa)
