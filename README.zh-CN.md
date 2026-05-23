# Pixiv OAuth Token Fetcher

🌍 [English](README.md) | [简体中文](README.zh-CN.md)

使用 Python + Playwright 自动模拟 Pixiv OAuth 登录流程，提取授权码，并换取 access_token。

---

## 📦 功能亮点

- ✅ 自动化模拟 Pixiv 登录流程（用户名密码）
- ✅ 支持窗口模式与无头模式，并可在启动时交互选择
- ✅ 支持交互式输入账号密码（密码不回显）
- ✅ 多路捕获授权码：CDP 网络/导航事件、Playwright 请求/响应/Frame 事件、页面注入脚本，自动失败时支持终端粘贴回调 URL 兜底
- ✅ 自动检测系统 Chrome / Edge，找不到时回退到 Playwright 自带 Chromium
- ✅ 获取 access_token 与 refresh_token，并支持用已有 refresh_token 刷新
- ✅ 缓慢输入模拟真人操作，绕过机器人检测
- ✅ 自动跳过安全设置提示页面（Passkeys / 2FA 提醒）
- ✅ 多选择器兼容 Pixiv 登录表单变化
- ✅ Token 交换带 HTTP 超时、状态码检查和明确的错误异常
- ✅ Token 交换失败时可在终端选择重试，避免重新走完整登录流程

---

## 🚀 安装方式

### 1. 克隆项目

```bash
git clone https://github.com/piglig/pixiv-token.git
cd pixiv-token
```

### 2. 安装依赖

推荐 Python 版本：`>=3.8`

```bash
pip install -r requirements.txt
playwright install chromium
```

如果本机已经安装 Chrome 或 Edge，会在 Windows 上自动尝试使用系统浏览器；若没有系统浏览器，则会使用 Playwright 自带的 Chromium。

依赖示例：

```txt
requests==2.32.2
playwright>=1.51.0
```

---

## ⚙️ 使用方法

### 命令行方式

```bash
# 交互模式：依次提示输入账号、密码、是否打开浏览器窗口（Y/n，留空默认打开）
python pixiv_token_fetcher.py

# 显式传入账号密码
python pixiv_token_fetcher.py -u "你的邮箱" -p "你的密码"

# 强制无头模式（跳过交互询问）
python pixiv_token_fetcher.py --headless
```

### 作为模块调用

```python
from pixiv_token_fetcher import PixivTokenError, PixivTokenFetcher

fetcher = PixivTokenFetcher(
    username="你的Pixiv账号",
    password="你的Pixiv密码",
    headless=False,  # 设为 True 隐藏浏览器窗口
)
code = fetcher.fetch_code()
if code:
    try:
        token_info = fetcher.exchange_token(code)
    except PixivTokenError as exc:
        raise RuntimeError(f"Token 交换失败：{exc}") from exc

    print("Access Token:", token_info.get("access_token"))
    print("Refresh Token:", token_info.get("refresh_token"))

# 后续可以复用已有 refresh token 获取新的 access token
refreshed_info = fetcher.refresh_token("已有的_refresh_token")
print("New Access Token:", refreshed_info.get("access_token"))
```

---

## 🔧 工作原理

1. **PKCE 生成** — 生成 `code_verifier` 和 `code_challenge` 用于 OAuth PKCE 流程
2. **浏览器启动** — 优先使用系统 Chrome / Edge，找不到时回退到 Playwright 自带 Chromium；两者都没有时给出明确安装提示
3. **自动登录** — 以缓慢输入方式填写邮箱和密码，模拟真人操作
4. **授权码捕获** — 多路监听 `pixiv://account/login?code=...` 回调：CDP 网络与导航事件、Playwright 请求/响应/Frame 事件，以及一段注入到页面的 JS 脚本（监控 `location` / `history` / 点击 / DOM 变化）
5. **安全提示处理** — 若 Pixiv 弹出 Passkeys/2FA 设置页面，自动点击"稍后提醒"/"跳过"
6. **手动兜底** — 如果自动捕获失败，可以在终端粘贴完整回调 URL 或原始授权码
7. **Token 交换 / 刷新** — 通过 Pixiv OAuth API 将授权码换取 access token 和 refresh token，或使用已有 refresh token 刷新 access token，并带有 HTTP 超时、状态码检查和 JSON 校验

---

## 📌 注意事项

- ⚠️ 请勿在生产环境中硬编码账号密码，建议使用环境变量或密钥管理工具。
- 🔐 如果在交互式终端中省略 `--username` 或 `--password`，工具会提示输入；密码输入不会回显。
- ❌ 本项目非 Pixiv 官方 SDK，Pixiv 页面结构变化可能影响运行。
- 🛡 使用时请遵守 Pixiv 的服务条款。
- 🔁 Refresh token 有效期很长，通常只需运行一次即可。

---

## 🧪 示例输出

```
🚀 Opening Pixiv login page...
📧 Username input completed
🔒 Password input completed
🔑 Login submitted
  Clicking 'Remind me later' to skip security prompt
✅ Code captured: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
🎟️ Access Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
🔁 Refresh Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 📝 授权协议

MIT License

---

## 🙋‍♀️ 贡献与反馈

欢迎提交 Pull Request 和 Issue！

---

## 📫 联系方式

- GitHub: [piglig](https://github.com/piglig)
- Email: zhu1197437384@gmail.com
