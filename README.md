# Pixiv OAuth Token Fetcher

🌍 [English](README.md) | [简体中文](README.zh-CN.md)

A Python automation tool using Playwright to simulate Pixiv OAuth login, capture the authorization code, and exchange it for an access token.

---

## 📦 Features

- ✅ Automated Pixiv login (username/password)
- ✅ Visible and headless mode support, with an interactive prompt at startup
- ✅ Interactive credential entry (password is not echoed)
- ✅ Multi-source authorization code capture: CDP network/navigation events, Playwright request/response/frame events, an injected page script, and a manual paste fallback in the terminal
- ✅ Auto-detect system Chrome / Edge; fall back to bundled Playwright Chromium
- ✅ Access token & refresh token retrieval, plus refresh from an existing `refresh_token`
- ✅ Slow typing to reduce bot-detection friction
- ✅ Auto-skip security prompt pages (Passkeys / 2FA reminders)
- ✅ Multi-selector fallback for Pixiv login form compatibility
- ✅ Token exchange with HTTP timeout, status checks and clear error reporting
- ✅ Interactive retry prompt when token exchange fails, avoiding a full re-login

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/piglig/pixiv-token.git
cd pixiv-token
```

### 2. Install dependencies

Recommended Python version: `>=3.8`

```bash
pip install -r requirements.txt
playwright install chromium
```

If Chrome or Edge is already installed, the tool will try to use it automatically on Windows; otherwise it falls back to the bundled Playwright Chromium.

Sample requirements.txt:

```txt
requests==2.32.2
playwright>=1.51.0
```

---

## ⚙️ Usage

### Command line

```bash
# Interactive: prompts for username, password, and whether to open the browser window (Y/n, blank defaults to Y)
python pixiv_token_fetcher.py

# Pass credentials explicitly
python pixiv_token_fetcher.py -u "your_email" -p "your_password"

# Force headless mode (skips the browser-window prompt)
python pixiv_token_fetcher.py --headless
```

### As a module

```python
from pixiv_token_fetcher import PixivTokenError, PixivTokenFetcher

fetcher = PixivTokenFetcher(
    username="your_pixiv_email",
    password="your_pixiv_password",
    headless=False,  # Set to True to hide the browser window
)
code = fetcher.fetch_code()
if code:
    try:
        token_info = fetcher.exchange_token(code)
    except PixivTokenError as exc:
        raise RuntimeError(f"Token exchange failed: {exc}") from exc

    print("Access Token:", token_info.get("access_token"))
    print("Refresh Token:", token_info.get("refresh_token"))

# Reuse an existing refresh token to get a new access token
refreshed_info = fetcher.refresh_token("your_existing_refresh_token")
print("New Access Token:", refreshed_info.get("access_token"))
```

---

## 🔧 How It Works

1. **PKCE Generation** — Generates `code_verifier` and `code_challenge` for the OAuth PKCE flow
2. **Browser Launch** — Prefers system Chrome / Edge; falls back to the bundled Playwright Chromium; emits a clear install hint if neither is available
3. **Auto Login** — Fills in email/password with slow typing to mimic human input
4. **Code Capture** — Listens for `pixiv://account/login?code=...` from multiple sources: CDP network and navigation events, Playwright request/response/frame events, and an injected script that watches `location` / `history` / clicks / DOM mutations
5. **Security Prompt Handling** — Automatically clicks "Remind me later" / "Skip" if Pixiv shows a Passkeys/2FA setup page
6. **Manual Fallback** — If automatic capture fails, accepts a pasted callback URL or raw authorization code from the terminal
7. **Token Exchange / Refresh** — Exchanges the authorization code for access & refresh tokens, or refreshes an existing refresh token, with HTTP timeout, status checks, and JSON validation

---

## 📌 Notes

- ⚠️ Do not hardcode credentials in production environments. Use environment variables or a secrets manager.
- 🔐 If `--username` or `--password` is omitted in an interactive terminal, the tool prompts for it. Password input is hidden.
- ❌ This is not an official Pixiv SDK. Changes to Pixiv's login page may affect functionality.
- 🛡 Please comply with Pixiv's Terms of Service.
- 🔁 The refresh token is long-lived. You typically only need to run this tool once.

---

## 🧪 Example Output

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

## 📝 License

See the [LICENSE](LICENSE) file for license rights and limitations (MIT).

---

## 🙋‍♀️ Contribution & Issues

Pull Requests and Issues are welcome!

---

## 📫 Contact

- GitHub: [piglig](https://github.com/piglig)
- Email: zhu1197437384@gmail.com
