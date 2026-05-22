# Pixiv OAuth Token Fetcher

🌍 [English](README.md) | [简体中文](README.zh-CN.md)

A Python automation tool using Playwright to simulate Pixiv OAuth login, capture authorization code, and exchange it for an access token.

This fork is based on [piglig/pixiv-token](https://github.com/piglig/pixiv-token) and adds more robust OAuth callback capture for current Pixiv login behavior.
Upstream credit and the original MIT license are preserved.

---

## 📦 Features

- ✅ Automated Pixiv login (username/password)
- ✅ Headless mode support
- ✅ Visible (non-headless) mode support
- ✅ Access token & refresh token retrieval
- ✅ Slow typing to reduce bot-detection friction

---

## 🔁 Fork Changes

This fork keeps the original project goal and adds practical compatibility improvements for current Pixiv login flows:

- Multi-source authorization code capture via CDP, Playwright events, injected page script, and manual fallback
- Optional system Chrome / Edge launch via auto-detection or `PIXIV_BROWSER_PATH`
- Access token refresh from an existing `refresh_token`
- Configurable navigation timeout, capture timeout, login input timeout, request timeout, and typing delay
- Explicit browser cleanup and token exchange error reporting
- Visible browser mode by default, because Pixiv may require manual verification
- Interactive terminal prompts for username and password
- Auto-skip security prompt pages (Passkeys / 2FA reminders)
- Multi-selector fallback for Pixiv login form compatibility

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
# Visible browser mode (default). The tool will prompt for username and password.
python pixiv_token_fetcher.py

# Or pass credentials explicitly
python pixiv_token_fetcher.py -u "your_email" -p "your_password"

# Headless mode
python pixiv_token_fetcher.py --headless

# Custom timeouts and typing speed
python pixiv_token_fetcher.py \
  --capture-timeout 90 \
  --input-timeout 5000 \
  --navigation-timeout 90000 \
  --request-timeout 45 \
  --typing-delay 0.05
```

### As a module

```python
from pixiv_token_fetcher import PixivTokenError, PixivTokenFetcher

fetcher = PixivTokenFetcher(
    username="your_pixiv_email",
    password="your_pixiv_password",
    headless=False,  # Set to True to hide the browser window
    capture_timeout=60,  # Seconds to wait for OAuth callback capture
    input_timeout=3000,  # Milliseconds to wait for each login input selector
    navigation_timeout=60000,  # Milliseconds to wait for login page navigation
    request_timeout=30,  # Seconds to wait for the token HTTP request
    typing_delay=0.08,  # Seconds between typed characters
)
code = fetcher.fetch_code()
if code:
    try:
        token_info = fetcher.exchange_token(code)
    except PixivTokenError as exc:
        raise RuntimeError(f"Token exchange failed: {exc}") from exc

    print("Access Token:", token_info.get("access_token"))
    print("Refresh Token:", token_info.get("refresh_token"))

# Later, reuse an existing refresh token to get a new access token.
refreshed_info = fetcher.refresh_token("your_existing_refresh_token")
print("New Access Token:", refreshed_info.get("access_token"))
```

---

## 🔧 How It Works

1. **PKCE Generation** — Generates `code_verifier` and `code_challenge` for OAuth PKCE flow
2. **Browser Launch** — Uses system Chrome / Edge when available, otherwise falls back to Playwright Chromium
3. **Auto Login** — Fills in email/password with slow typing to mimic human input
4. **Code Capture** — Captures `pixiv://account/login?code=...` redirects from CDP network/navigation events, Playwright request/response/frame events, and an injected script that watches browser-side URL changes
5. **Security Prompt Handling** — Automatically clicks "Remind me later" / "Skip" if Pixiv shows a Passkeys/2FA setup page
6. **Manual Fallback** — If automatic capture fails, accepts a pasted callback URL or raw authorization code from the terminal
7. **Resource Cleanup** — Closes browser context and browser in a `finally` block even if login or capture fails
8. **Token Exchange / Refresh** — Exchanges the authorization code for access & refresh tokens, or refreshes an existing refresh token, with HTTP timeout, status checks, and JSON validation

---

## 📌 Notes

- ⚠️ Do not hardcode credentials in production environments. Use environment variables or a secrets manager.
- 🔐 If `--username` or `--password` is omitted in an interactive terminal, the tool prompts for it. Password input is hidden.
- ❌ This is not an official Pixiv SDK. Changes to Pixiv's login page may affect functionality.
- 🛡 Please comply with Pixiv's Terms of Service.
- 🔁 The refresh token is long-lived. You typically only need to run this tool once.
- ⏱ If Pixiv login is slow or requires extra verification, increase `--navigation-timeout` or `--capture-timeout`.
- 🧩 If you import this tool from another project, configure Python `logging` in your application to control status output.

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
