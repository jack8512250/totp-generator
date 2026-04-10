# TOTP 驗證碼產生器

用 Python 自動產生 TOTP (Time-based One-Time Password) 六位數驗證碼，取代手機上的 Authenticator App。

## 這是什麼？

很多網站登入時會要求輸入「驗證碼」，通常你需要打開手機的 Google Authenticator 或 Microsoft Authenticator 查看六位數字。

這個工具讓你在電腦上直接產生驗證碼，不需要每次拿手機。

---

## 安裝

### 1. 安裝 Python

如果還沒裝 Python，到 [python.org](https://www.python.org/downloads/) 下載安裝。

安裝時記得勾選 **「Add Python to PATH」**。

### 2. 下載這個專案

```bash
git clone https://github.com/你的帳號/totp-generator.git
cd totp-generator
```

或直接下載 ZIP 解壓縮。

### 3. 安裝套件

```bash
pip install -r requirements.txt
```

---

## 取得 TOTP Secret Key

**這是最關鍵的一步。** Secret Key 是產生驗證碼的密鑰，通常在你第一次設定兩步驗證時會看到。

### 方法一：從 QR Code 取得（推薦）

1. 登入你要設定的網站，進入「安全性設定」或「兩步驟驗證」
2. 選擇「設定 Authenticator App」
3. 網站會顯示一個 **QR Code**
4. **不要用手機掃！** 找到 QR Code 旁邊的選項：
   - 「無法掃描 QR Code？」
   - 「手動輸入」
   - 「Show secret key」
   - 「顯示金鑰」
5. 你會看到一串英文+數字的字串，例如：`JBSWY3DPEHPK3PXP`
6. **這就是你的 Secret Key，複製保存下來**

### 方法二：從 QR Code 圖片解碼

如果網站只給 QR Code 圖片，沒有顯示文字：

1. 截圖 QR Code
2. 到 [webqr.com](https://webqr.com/) 上傳圖片解碼
3. 解碼結果會像這樣：
   ```
   otpauth://totp/網站名稱:你的帳號?secret=JBSWY3DPEHPK3PXP&issuer=網站名稱
   ```
4. `secret=` 後面到 `&` 之間的字串就是你的 Secret Key
5. 以上面為例，Secret Key 是 `JBSWY3DPEHPK3PXP`

### 方法三：從 Google Authenticator App 匯出

如果你已經在手機上設定了 Authenticator：

1. 打開 Google Authenticator App
2. 點右上角三個點 → 「匯出帳戶」
3. 會顯示一個 QR Code
4. 截圖後用方法二解碼
5. 匯出的 URL 裡包含 `secret=` 欄位

> **注意：** Secret Key 等同於密碼，請妥善保管，不要傳給別人或上傳到網路。

---

## 使用方式

### 方式一：直接傳入 Secret Key

```bash
python totp.py JBSWY3DPEHPK3PXP
```

輸出：
```
驗證碼: 482931
剩餘秒數: 18 秒
```

### 方式二：用 .env 檔案保存（推薦日常使用）

1. 複製範本：
   ```bash
   cp .env.example .env
   ```

2. 編輯 `.env`，填入你的 Secret Key：
   ```
   TOTP_SECRET=JBSWY3DPEHPK3PXP
   ```

3. 之後只要執行：
   ```bash
   python totp.py
   ```

### 方式三：從 QR Code 圖片自動解碼（推薦首次設定）

如果你有 Authenticator 的 QR Code 截圖：

```bash
python decode_qr.py qrcode.png
```

輸出：
```
==================================================
  QR Code 解碼結果
==================================================
  Secret Key : JBSWY3DPEHPK3PXP
  網站/服務  : MyWebsite
  帳號       : user@example.com
==================================================

使用方式:
  python totp.py JBSWY3DPEHPK3PXP

或存入 .env:
  TOTP_SECRET=JBSWY3DPEHPK3PXP
```

> **注意：** Windows 使用 decode_qr.py 需要額外安裝 [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

---

## 常見問題

### Q: 驗證碼不正確？

驗證碼跟時間有關，確認電腦的時間是準的。如果電腦時間差太多，驗證碼會對不上。

Windows 對時方式：設定 → 時間與語言 → 日期與時間 → 立即同步

### Q: Secret Key 長什麼樣？

通常是 16~32 個字元的英文大寫 + 數字，例如：
- `JBSWY3DPEHPK3PXP`
- `HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ`

如果你的 key 有空格，去掉空格即可。

### Q: 可以同時設定多個網站嗎？

目前這個工具一次只支援一組 Secret Key。如果需要多組，可以用不同的 .env 檔案或直接傳參數：

```bash
python totp.py SECRET_FOR_SITE_A
python totp.py SECRET_FOR_SITE_B
```

### Q: .env 檔案安全嗎？

`.env` 已經加入 `.gitignore`，不會被 git 推到 GitHub。但請確保你的電腦本身是安全的。

---

## 原理說明

TOTP (Time-based One-Time Password) 是一個基於時間的一次性密碼演算法 (RFC 6238)：

1. 你和伺服器共用一個 **Secret Key**
2. 用當前時間（每 30 秒一個區間）+ Secret Key 做 HMAC-SHA1 雜湊
3. 從雜湊結果取出 6 位數字
4. 因為雙方用同一個 Secret Key 和同一個時間，所以產生的驗證碼一樣

這就是為什麼你的電腦時間必須準確 — 差超過 30 秒就會產生不同的驗證碼。
