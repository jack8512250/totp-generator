"""
QR Code 解碼器 — 從 Authenticator QR Code 圖片中提取 TOTP Secret Key

用法:
    python decode_qr.py qrcode.png
    python decode_qr.py C:\\Users\\你的名字\\Desktop\\screenshot.png
"""
import sys
from urllib.parse import urlparse, parse_qs

try:
    from pyzbar.pyzbar import decode
except ImportError:
    print("請先安裝 pyzbar: pip install pyzbar")
    print()
    print("Windows 還需要安裝 Visual C++ Redistributable:")
    print("  https://aka.ms/vs/17/release/vc_redist.x64.exe")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("請先安裝 Pillow: pip install Pillow")
    sys.exit(1)


def decode_qr(image_path: str) -> dict:
    """
    解碼 QR Code 圖片，回傳 TOTP 資訊。

    Returns:
        {
            "raw": "otpauth://totp/...",
            "secret": "JBSWY3DPEHPK3PXP",
            "issuer": "網站名稱",
            "account": "你的帳號",
        }
    """
    img = Image.open(image_path)
    results = decode(img)

    if not results:
        raise ValueError("找不到 QR Code，請確認圖片清晰且包含 QR Code")

    raw = results[0].data.decode("utf-8")

    # 解析 otpauth:// URL
    parsed = urlparse(raw)

    if parsed.scheme != "otpauth":
        return {"raw": raw, "secret": None, "issuer": None, "account": None}

    params = parse_qs(parsed.query)
    secret = params.get("secret", [None])[0]
    issuer = params.get("issuer", [None])[0]

    # 帳號在 path 中，格式: /Issuer:account 或 /account
    label = parsed.path.lstrip("/")
    account = label.split(":")[-1] if ":" in label else label

    return {
        "raw": raw,
        "secret": secret,
        "issuer": issuer,
        "account": account,
    }


def main():
    if len(sys.argv) < 2:
        print("用法: python decode_qr.py <QR Code 圖片路徑>")
        print()
        print("範例:")
        print("  python decode_qr.py qrcode.png")
        print("  python decode_qr.py C:\\Users\\user\\Desktop\\screenshot.png")
        sys.exit(1)

    image_path = sys.argv[1]

    try:
        result = decode_qr(image_path)
    except FileNotFoundError:
        print(f"錯誤: 找不到檔案 {image_path}")
        sys.exit(1)
    except ValueError as e:
        print(f"錯誤: {e}")
        sys.exit(1)

    print("=" * 50)
    print("  QR Code 解碼結果")
    print("=" * 50)

    if result["secret"]:
        print(f"  Secret Key : {result['secret']}")
        print(f"  網站/服務  : {result['issuer'] or '(未知)'}")
        print(f"  帳號       : {result['account'] or '(未知)'}")
        print("=" * 50)
        print()
        print("使用方式:")
        print(f"  python totp.py {result['secret']}")
        print()
        print("或存入 .env:")
        print(f"  TOTP_SECRET={result['secret']}")
    else:
        print("  這不是 TOTP QR Code")
        print(f"  原始內容: {result['raw']}")

    print()


if __name__ == "__main__":
    main()
