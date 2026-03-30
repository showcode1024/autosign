import cloudscraper
import ddddocr
import base64
import os

# 从 GitHub Secrets 读取敏感信息
MY_EMAIL = os.environ.get('MY_EMAIL')
MY_PASSWORD = os.environ.get('MY_PASSWORD')

def start_task():
    # 1. 初始化
    scraper = cloudscraper.create_scraper()
    ocr = ddddocr.DdddOcr(show_ad=False)
    
    base_url = "https://ltyun.xyz"
    captcha_url = f"{base_url}/api/sysAuth/captcha"
    login_url = f"{base_url}/api/sysAuth/login"
    sign_url = f"{base_url}/api/userhome/usersign"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "Origin": base_url,
        "Referer": f"{base_url}/"
    }

    try:
        # 2. 获取并识别验证码
        captcha_res = scraper.get(captcha_url, headers=headers).json()
        code_id = captcha_res['result']['id']
        img_base64 = captcha_res['result']['img']
        if "," in img_base64:
            img_base64 = img_base64.split(",")[1]
        
        img_bytes = base64.b64decode(img_base64)
        captcha_code = ocr.classification(img_bytes)
        print(f"🤖 验证码识别结果: {captcha_code}")

        # 3. 模拟登录
        login_data = {
            "account": MY_EMAIL,
            "password": MY_PASSWORD,
            "codeId": code_id,
            "code": captcha_code
        }
        login_res = scraper.post(login_url, headers=headers, json=login_data).json()

        if login_res.get('code') == 200:
            # 4. 获取新 Token 并签到
            token = login_res.get('result', {}).get('accessToken')
            print("✅ 登录成功！正在发起签到...")
            
            sign_headers = headers.copy()
            sign_headers["Authorization"] = f"Bearer {token}"
            response = scraper.get(sign_url, headers=sign_headers)
            
            print(f"🎉 签到结果: {response.text}")
        else:
            print(f"❌ 登录失败: {login_res.get('message')}")

    except Exception as e:
        print(f"🔥 脚本运行异常: {e}")

if __name__ == "__main__":
    if MY_EMAIL and MY_PASSWORD:
        start_task()
    else:
        print("❌ 错误: 未在 GitHub Secrets 中设置 MY_EMAIL 和 MY_PASSWORD")
