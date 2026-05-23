import base64
import hashlib
import os
import secrets
import sys
import requests
import time
import re
from urllib.parse import unquote
from playwright.sync_api import sync_playwright, TimeoutError

PIXIV_CLIENT_ID = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
PIXIV_CLIENT_SECRET = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"
PIXIV_TOKEN_URL = "https://oauth.secure.pixiv.net/auth/token"
REDIRECT_URI = "https://app-api.pixiv.net/web/v1/users/auth/pixiv/callback"
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
API_UA = "PixivAndroidApp/5.0.234 (Android 11; Pixel 5)"
CALLBACK_URL_PREFIX = "pixiv://account/login"
CONSOLE_CODE_PREFIX = "[PIXIV-CODE]"
CONSOLE_CALLBACK_PREFIX = "[PIXIV-CALLBACK]"
AUTH_CODE_PATTERN = re.compile(r"(?:^|[?&])code=([^&#\s\"'<>)]*)")

EMAIL_SELECTORS = [
    "input[autocomplete^='username']",
    "input[placeholder*='メールアドレス']",
    "input[type='email']",
]
PASSWORD_SELECTORS = [
    "input[autocomplete^='current-password']",
    "input[placeholder*='パスワード']",
    "input[type='password']",
]
SKIP_BUTTON_TEXTS = ["Remind me later", "Skip", "あとで", "スキップ"]
DEFAULT_BROWSER_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


class PixivTokenError(RuntimeError):
    """Raised when token exchange fails."""


class PixivTokenFetcher:
    def __init__(self, username, password, headless=False):
        self.headless = headless
        self.username = username
        self.password = password
        self.code_verifier = secrets.token_urlsafe(64)
        self.code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(self.code_verifier.encode()).digest()
        ).rstrip(b'=').decode('ascii')

    def _launch_args(self):
        return ["--disable-blink-features=AutomationControlled"]

    def _browser_executable_path(self, playwright=None):
        for browser_path in DEFAULT_BROWSER_PATHS:
            if os.path.exists(browser_path):
                return browser_path

        if playwright is not None:
            try:
                bundled_path = playwright.chromium.executable_path
            except Exception:
                bundled_path = None
            if bundled_path and os.path.exists(bundled_path):
                return bundled_path
            print("⚠️ No browser found. Run: python -m playwright install chromium")

        return None

    def _get_login_url(self):
        return (
            "https://app-api.pixiv.net/web/v1/login?"
            f"code_challenge={self.code_challenge}&"
            "code_challenge_method=S256&client=pixiv-android"
        )

    def _extract_code(self, value):
        if not value:
            return None

        candidates = [value]
        try:
            candidates.append(unquote(value))
        except Exception:
            pass

        for candidate in candidates:
            if CALLBACK_URL_PREFIX in candidate:
                candidate = candidate[candidate.find(CALLBACK_URL_PREFIX):]

            match = AUTH_CODE_PATTERN.search(candidate)
            if match:
                return unquote(match.group(1))

        return None

    def _read_manual_code(self):
        if not sys.stdin.isatty():
            return None

        print("\nCode was not captured automatically.")
        print("Paste the full pixiv://account/login?code=... callback URL if you can find it.")
        print("You can also paste only the code value. Press Enter to skip.")

        manual_value = input("Paste callback URL or code: ").strip()
        if not manual_value:
            return None

        extracted_code = self._extract_code(manual_value)
        if extracted_code:
            return extracted_code

        if re.fullmatch(r"[A-Za-z0-9_-]+", manual_value):
            return manual_value

        print("⚠️ No authorization code was found in the input.")
        return None

    def _callback_capture_script(self):
        return r'''
(() => {
    const CODE_PREFIX = "[PIXIV-CODE]";
    const CALLBACK_PREFIX = "[PIXIV-CALLBACK]";
    const seen = new Set();

    function capture(value, source) {
        if (!value || typeof value !== "string") return;
        if (seen.has(source + value)) return;
        seen.add(source + value);

        const candidates = [value];
        try { candidates.push(decodeURIComponent(value)); } catch (_) {}

        for (const candidate of candidates) {
            const callbackMatch = candidate.match(/pixiv:\/\/account\/login[^\s"'<>)]*/i);
            const target = callbackMatch ? callbackMatch[0] : candidate;
            const codeMatch = target.match(/[?&]code=([^&#\s"'<>)]*)/);
            if (!codeMatch) continue;

            const code = decodeURIComponent(codeMatch[1]);
            console.log(CODE_PREFIX + code);
            console.log(CALLBACK_PREFIX + target);
            window.__PIXIV_OAUTH_CODE__ = code;
            window.__PIXIV_OAUTH_CALLBACK__ = target;
            break;
        }
    }

    function scan() {
        capture(location.href, "location.href");
        for (const entry of performance.getEntries()) {
            capture(entry.name, "performance");
        }
        for (const element of document.querySelectorAll("a[href], form[action]")) {
            capture(element.href || element.action, "dom");
        }
    }

    function patch(object, name, getValue) {
        try {
            const original = object[name];
            if (typeof original !== "function") return;
            object[name] = function (...args) {
                capture(String(getValue(args) || ""), name);
                return original.apply(this, args);
            };
        } catch (_) {}
    }

    patch(window, "open", args => args[0]);
    patch(Location.prototype, "assign", args => args[0]);
    patch(Location.prototype, "replace", args => args[0]);
    patch(history, "pushState", args => args[2]);
    patch(history, "replaceState", args => args[2]);

    document.addEventListener("click", event => {
        const link = event.target && event.target.closest ? event.target.closest("a[href]") : null;
        if (link) capture(link.href, "click");
    }, true);

    new MutationObserver(scan).observe(document.documentElement, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["href", "action"],
    });

    setInterval(scan, 250);
    scan();
})();
'''

    def _slow_type(self, page, selector, text, delay=0.08):
        page.focus(selector)
        for char in text:
            page.keyboard.insert_text(char)
            time.sleep(delay)

    def _find_input(self, page, selectors, timeout=3000):
        for selector in selectors:
            try:
                el = page.wait_for_selector(selector, timeout=timeout)
                if el and el.is_visible():
                    return selector
            except TimeoutError:
                continue
        return None

    def _perform_login(self, page):
        email_selector = self._find_input(page, EMAIL_SELECTORS)
        if not email_selector:
            print("⚠️ Username input not found")
            return

        self._slow_type(page, email_selector, self.username)
        print("📧 Username input completed")

        pwd_selector = self._find_input(page, PASSWORD_SELECTORS)
        if not pwd_selector:
            page.keyboard.press("Enter")
            time.sleep(2)
            pwd_selector = self._find_input(page, PASSWORD_SELECTORS)

        if not pwd_selector:
            print("⚠️ Password input not found")
            return

        self._slow_type(page, pwd_selector, self.password)
        print("🔒 Password input completed")

        login_btn = page.locator("button:has-text('ログイン')")
        if login_btn.count() > 0:
            login_btn.first.click()
        else:
            page.keyboard.press("Enter")
        print("🔑 Login submitted")

    def _skip_security_prompts(self, page):
        for btn_text in SKIP_BUTTON_TEXTS:
            btn = page.locator(f"button:has-text('{btn_text}')")
            if btn.count() > 0 and btn.first.is_visible():
                print(f"  Clicking '{btn_text}' to skip security prompt")
                btn.first.click()
                time.sleep(1)
                return True
        return False

    def fetch_code(self):
        with sync_playwright() as p:
            launch_options = {
                "headless": self.headless,
                "args": self._launch_args(),
            }
            browser_path = self._browser_executable_path(p)
            if browser_path:
                launch_options["executable_path"] = browser_path

            browser = p.chromium.launch(**launch_options)
            context = browser.new_context(
                user_agent=BROWSER_UA,
                viewport={"width": 1280, "height": 720},
                locale="ja-JP",
            )
            context.add_init_script(self._callback_capture_script())
            page = context.new_page()
            cdp_session = context.new_cdp_session(page)
            cdp_session.send("Network.enable")
            cdp_session.send("Page.enable")

            captured_code = {"value": None}

            def try_capture(value, source):
                if captured_code["value"]:
                    return

                code = self._extract_code(value)
                if not code:
                    return

                captured_code["value"] = code
                print("✅ Code captured:", code, flush=True)
                try:
                    page.close()
                except Exception:
                    pass

            def on_request_will_be_sent(event):
                if not isinstance(event, dict):
                    return

                request = event.get("request")
                if isinstance(request, dict):
                    try_capture(request.get("url", ""), "cdp request")
                try_capture(event.get("documentURL", ""), "cdp document")

            def on_console(message):
                text = message.text or ""
                if text.startswith(CONSOLE_CODE_PREFIX):
                    try_capture("code=" + text[len(CONSOLE_CODE_PREFIX):], "console script")
                elif text.startswith(CONSOLE_CALLBACK_PREFIX):
                    try_capture(text[len(CONSOLE_CALLBACK_PREFIX):], "console script")

            def on_page_navigation(event):
                if isinstance(event, dict):
                    try_capture(event.get("url", ""), "cdp navigation")

            cdp_session.on("Network.requestWillBeSent", on_request_will_be_sent)
            cdp_session.on("Page.frameScheduledNavigation", on_page_navigation)
            cdp_session.on("Page.frameRequestedNavigation", on_page_navigation)
            page.on("request", lambda request: try_capture(request.url, "request"))
            page.on("response", lambda response: try_capture(response.url, "response"))
            page.on("framenavigated", lambda frame: try_capture(frame.url, "frame navigation"))
            page.on("console", on_console)

            print("🚀 Opening Pixiv login page...")
            try:
                page.goto(self._get_login_url(), wait_until="domcontentloaded", timeout=60000)
            except TimeoutError:
                print("⚠️ Login page navigation timed out; continuing.")
            self._perform_login(page)

            for _ in range(60):
                if captured_code["value"] or page.is_closed():
                    break
                try:
                    self._skip_security_prompts(page)
                except Exception:
                    pass
                time.sleep(1)

            if not captured_code["value"]:
                print("⌛ Timeout: Code not captured.")
                captured_code["value"] = self._read_manual_code()

            browser.close()
            return captured_code["value"]

    def _post_token(self, data):
        try:
            resp = requests.post(
                PIXIV_TOKEN_URL,
                data=data,
                headers={"User-Agent": API_UA},
                timeout=30,
            )
        except requests.RequestException as exc:
            raise PixivTokenError(f"Token request failed: {exc}") from exc

        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            response_text = resp.text.strip()
            if len(response_text) > 500:
                response_text = response_text[:497] + "..."
            detail = f": {response_text}" if response_text else ""
            raise PixivTokenError(
                f"Token request failed with HTTP {resp.status_code}{detail}"
            ) from exc

        try:
            return resp.json()
        except ValueError as exc:
            raise PixivTokenError("Token response was not valid JSON") from exc

    def exchange_token(self, code):
        return self._post_token({
            "client_id": PIXIV_CLIENT_ID,
            "client_secret": PIXIV_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": self.code_verifier,
            "redirect_uri": REDIRECT_URI,
            "include_policy": "true",
        })

    def refresh_token(self, refresh_token):
        return self._post_token({
            "client_id": PIXIV_CLIENT_ID,
            "client_secret": PIXIV_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "include_policy": "true",
        })


if __name__ == "__main__":
    import argparse
    import getpass

    parser = argparse.ArgumentParser(description="Fetch Pixiv OAuth refresh token")
    parser.add_argument("--username", "-u", help="Pixiv account email or username")
    parser.add_argument("--password", "-p", help="Pixiv account password")
    parser.add_argument("--headless", action="store_true", help="Run without showing the browser window")
    parser.add_argument("--no-headless", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    username = args.username
    password = args.password
    if not username:
        if not sys.stdin.isatty():
            parser.error("--username is required when stdin is not interactive")
        username = input("Pixiv username/email: ").strip()
    if not password:
        if not sys.stdin.isatty():
            parser.error("--password is required when stdin is not interactive")
        password = getpass.getpass("Pixiv password: ")

    if args.headless and not args.no_headless:
        headless = True
    elif args.no_headless:
        headless = False
    elif sys.stdin.isatty():
        choice = input("Open browser window? (Y/n): ").strip().lower()
        headless = (choice == "n")
    else:
        headless = False

    fetcher = PixivTokenFetcher(username, password, headless=headless)
    code = fetcher.fetch_code()
    if not code:
        print("❌ Failed to retrieve authorization code.")
        sys.exit(1)

    while True:
        try:
            token_info = fetcher.exchange_token(code)
            break
        except PixivTokenError as exc:
            print(f"❌ Failed to exchange token: {exc}")
            if not sys.stdin.isatty():
                sys.exit(1)
            choice = input("Retry token exchange? (Y/n): ").strip().lower()
            if choice == "n":
                sys.exit(1)
            print("🔁 Retrying...")

    print(f"🎟️ Access Token: {token_info.get('access_token')}")
    print(f"🔁 Refresh Token: {token_info.get('refresh_token')}")
