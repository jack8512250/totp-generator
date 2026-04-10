"""
QR Code 解碼器 — 從 Authenticator QR Code 圖片中提取 TOTP Secret Key

支援格式:
  - otpauth://totp/...          (標準 TOTP QR Code)
  - otpauth-migration://offline (Google Authenticator 匯出)

用法:
    python decode_qr.py qrcode.png
    python decode_qr.py C:\\Users\\你的名字\\Desktop\\screenshot.png
"""
import base64
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

def _read_qr(image_path: str) -> str:
    """讀取 QR Code，自動選擇可用的後端 (OpenCV → pyzbar)。"""
    raw_bytes = Path(image_path).read_bytes()

    # 後端 1: OpenCV (無額外 DLL 依賴)
    try:
        import cv2, numpy as np
        buf = np.frombuffer(raw_bytes, dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if img is not None:
            data, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
            if data:
                return data
    except ImportError:
        pass

    # 後端 2: pyzbar + Pillow
    try:
        from pyzbar.pyzbar import decode
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(raw_bytes))
        results = decode(img)
        if results:
            return results[0].data.decode("utf-8")
    except ImportError:
        pass

    # 兩個都沒有
    try:
        import cv2  # noqa: F811
    except ImportError:
        cv2_ok = False
    else:
        cv2_ok = True
    try:
        from pyzbar.pyzbar import decode as _  # noqa: F401, F811
    except ImportError:
        pyzbar_ok = False
    else:
        pyzbar_ok = True

    if not cv2_ok and not pyzbar_ok:
        print("需要安裝 QR 解碼套件，擇一即可:")
        print("  pip install opencv-python-headless")
        print("  pip install pyzbar Pillow")
        sys.exit(1)

    raise ValueError("找不到 QR Code，請確認圖片清晰且包含 QR Code")


def _parse_migration(data_param: str) -> list[dict]:
    """解析 otpauth-migration://offline?data=... 的 protobuf payload。"""
    raw = base64.b64decode(unquote(data_param))
    entries = []
    i = 0
    while i < len(raw):
        tag = raw[i]; i += 1
        field_num = tag >> 3
        wire_type = tag & 0x07
        if wire_type == 2:  # length-delimited
            length, i = _read_varint(raw, i)
            value = raw[i:i + length]; i += length
            if field_num == 1:
                entries.append(_parse_otp_params(value))
        elif wire_type == 0:
            _, i = _read_varint(raw, i)
    return entries


def _read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while True:
        b = buf[pos]; pos += 1
        result |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            break
        shift += 7
    return result, pos


def _parse_otp_params(value: bytes) -> dict:
    algo_map = {0: "UNSPECIFIED", 1: "SHA1", 2: "SHA256", 3: "SHA512"}
    digit_map = {0: "UNSPECIFIED", 1: "SIX", 2: "EIGHT"}
    type_map = {0: "UNSPECIFIED", 1: "HOTP", 2: "TOTP"}
    entry: dict = {}
    j = 0
    while j < len(value):
        inner_tag = value[j]; j += 1
        inner_field = inner_tag >> 3
        inner_wire = inner_tag & 0x07
        if inner_wire == 2:
            inner_len, j = _read_varint(value, j)
            inner_val = value[j:j + inner_len]; j += inner_len
            if inner_field == 1:
                entry["secret"] = base64.b32encode(inner_val).decode().rstrip("=")
            elif inner_field == 2:
                entry["account"] = inner_val.decode("utf-8")
            elif inner_field == 3:
                entry["issuer"] = inner_val.decode("utf-8")
        elif inner_wire == 0:
            v, j = _read_varint(value, j)
            if inner_field == 4:
                entry["algorithm"] = algo_map.get(v, str(v))
            elif inner_field == 5:
                entry["digits"] = digit_map.get(v, str(v))
            elif inner_field == 6:
                entry["type"] = type_map.get(v, str(v))
    return entry


def decode_qr(image_path: str) -> dict | list[dict]:
    """
    解碼 QR Code 圖片，回傳 TOTP 資訊。

    標準 otpauth:// 回傳單一 dict:
        {"raw", "secret", "issuer", "account"}

    Google Authenticator 匯出 (otpauth-migration://) 回傳 list[dict]:
        [{"secret", "account", "issuer", "algorithm", "digits", "type"}, ...]
    """
    raw = _read_qr(image_path)
    parsed = urlparse(raw)

    # Google Authenticator 匯出格式
    if parsed.scheme == "otpauth-migration":
        params = parse_qs(parsed.query)
        data_param = params.get("data", [None])[0]
        if not data_param:
            raise ValueError("otpauth-migration URL 缺少 data 參數")
        return _parse_migration(data_param)

    # 標準 otpauth://totp/ 格式
    if parsed.scheme == "otpauth":
        params = parse_qs(parsed.query)
        secret = params.get("secret", [None])[0]
        issuer = params.get("issuer", [None])[0]
        label = parsed.path.lstrip("/")
        account = label.split(":")[-1] if ":" in label else label
        return {"raw": raw, "secret": secret, "issuer": issuer, "account": account}

    return {"raw": raw, "secret": None, "issuer": None, "account": None}


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

    if isinstance(result, list):
        # otpauth-migration 格式 (可能有多組)
        for i, entry in enumerate(result, 1):
            if len(result) > 1:
                print(f"  [{i}]")
            print(f"  Secret Key : {entry.get('secret', '(無)')}")
            print(f"  網站/服務  : {entry.get('issuer', '(未知)')}")
            print(f"  帳號       : {entry.get('account', '(未知)')}")
            print(f"  類型       : {entry.get('type', '?')}")
            print(f"  演算法     : {entry.get('algorithm', '?')}")
            print(f"  位數       : {entry.get('digits', '?')}")
            if i < len(result):
                print("-" * 50)
        secret = result[0].get("secret") if result else None
    elif result.get("secret"):
        secret = result["secret"]
        print(f"  Secret Key : {secret}")
        print(f"  網站/服務  : {result['issuer'] or '(未知)'}")
        print(f"  帳號       : {result['account'] or '(未知)'}")
    else:
        secret = None
        print("  這不是 TOTP QR Code")
        print(f"  原始內容: {result['raw']}")

    print("=" * 50)
    if secret:
        print()
        print("使用方式:")
        print(f"  python totp.py {secret}")
        print()
        print("或存入 .env:")
        print(f"  TOTP_SECRET={secret}")
    print()


if __name__ == "__main__":
    main()
