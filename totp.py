"""
TOTP 驗證碼產生器

用法:
    python totp.py                  # 從 .env 讀取 TOTP_SECRET
    python totp.py YOUR_SECRET_KEY  # 直接傳入 Secret Key
"""
import sys
import time

try:
    import pyotp
except ImportError:
    print("請先安裝 pyotp: pip install pyotp")
    sys.exit(1)


def generate_totp(secret: str) -> str:
    """產生 6 位 TOTP 驗證碼。"""
    totp = pyotp.TOTP(secret)
    return totp.now()


def get_remaining_seconds(secret: str) -> int:
    """取得目前驗證碼剩餘有效秒數。"""
    totp = pyotp.TOTP(secret)
    return totp.interval - (int(time.time()) % totp.interval)


def main():
    secret = None

    # 優先從命令列參數取得
    if len(sys.argv) > 1:
        secret = sys.argv[1]
    else:
        # 嘗試從 .env 讀取
        try:
            from dotenv import load_dotenv
            import os
            load_dotenv()
            secret = os.getenv("TOTP_SECRET")
        except ImportError:
            pass

    if not secret:
        print("錯誤: 請提供 TOTP Secret Key")
        print()
        print("用法:")
        print("  python totp.py YOUR_SECRET_KEY")
        print("  或在 .env 檔案中設定 TOTP_SECRET=YOUR_SECRET_KEY")
        print()
        print("如何取得 Secret Key? 請參閱 README.md")
        sys.exit(1)

    code = generate_totp(secret)
    remaining = get_remaining_seconds(secret)

    print(f"驗證碼: {code}")
    print(f"剩餘秒數: {remaining} 秒")


if __name__ == "__main__":
    main()
