# Pixiv OAuth Token Fetcher

🌍 [English](README.md) | [简体中文](README.zh-CN.md)

A Python automation tool using Playwright to simulate Pixiv OAuth login, capture authorization code, and exchange it for an access token.

This fork is based on [piglig/pixiv-token](https://github.com/piglig/pixiv-token) and adds more robust OAuth callback capture for current Pixiv login behavior.

---

## 📦 Features

- ✅ Automated Pixiv login (username/password)
- ✅ Headless mode support
- ✅ Visible (non-headless) mode support
- ✅ Multi-source authorization code capture via CDP, Playwright events, injected page script, and manual fallback
- ✅ Optional system Chrome / Edge launch via auto-detection or `PIXIV_BROWSER_PATH`
- ✅ Access token & refresh token retrieval
- ✅ Slow typing to bypass bot detection
- ✅ Auto-skip security prompt pages (Passkeys / 2FA reminders)
- ✅ Multi-selector fallback for Pixiv login form compatibility

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/shitianyaa/pixiv-token.git
cd pixiv-token
```

### 2. Install dependencies

Recommended Python version: `>=3.8`

```bash
pip install -r requirements.txt
playwright install chromium
```

If Chrome or Edge is already installed, this fork will try to use it automatically on Windows. You can also set a custom browser executable:

```powershell
$env:PIXIV_BROWSER_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
```

Sample requirements.txt:

```txt
requests==2.32.2
playwright>=1.51.0
```

---

## ⚙️ Usage

### Command line

```bash
# Headless mode (default)
python pixiv_token_fetcher.py -u "your_email" -p "your_password"

# Visible browser mode
python pixiv_token_fetcher.py -u "your_email" -p "your_password" --no-headless
```

### As a module

```python
from pixiv_token_fetcher import PixivTokenFetcher

fetcher = PixivTokenFetcher(
    username="your_pixiv_email",
    password="your_pixiv_password",
    headless=True,  # Set to False to show browser window
)
code = fetcher.fetch_code()
if code:
    token_info = fetcher.exchange_token(code)
    print("Access Token:", token_info.get("access_token"))
    print("Refresh Token:", token_info.get("refresh_token"))
```

---

## 🔧 How It Works

1. **PKCE Generation** — Generates `code_verifier` and `code_challenge` for OAuth PKCE flow
2. **Browser Launch** — Uses system Chrome / Edge when available, otherwise falls back to Playwright Chromium
3. **Auto Login** — Fills in email/password with slow typing to mimic human input
4. **Code Capture** — Captures `pixiv://account/login?code=...` redirects from CDP network/navigation events, Playwright request/response/frame events, and an injected script that watches browser-side URL changes
5. **Security Prompt Handling** — Automatically clicks "Remind me later" / "Skip" if Pixiv shows a Passkeys/2FA setup page
6. **Manual Fallback** — If automatic capture fails, accepts a pasted callback URL or raw authorization code from the terminal
7. **Token Exchange** — Exchanges the authorization code for access & refresh tokens via Pixiv OAuth API

---

## 📌 Notes

- ⚠️ Do not hardcode credentials in production environments. Use environment variables or a secrets manager.
- ❌ This is not an official Pixiv SDK. Changes to Pixiv's login page may affect functionality.
- 🛡 Please comply with Pixiv's Terms of Service.
- 🔁 The refresh token is long-lived. You typically only need to run this tool once.

---

## 🧪 Example Output

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

## 📝 License

See the [LICENSE](LICENSE) file for license rights and limitations (MIT).

---

## 🙋‍♀️ Contribution & Issues

Pull Requests and Issues are welcome!

---

## 🙏 Upstream

Original project: [piglig/pixiv-token](https://github.com/piglig/pixiv-token)

---

## 📫 Contact

- GitHub: [shitianyaa](https://github.com/shitianyaa)
