import os
import cloudscraper
import ddddocr
import base64
import smtplib
from email.mime.text import MIMEText
import requests
# 从 GitHub Secrets 读取敏感信息
LOGIN_EMAIL1 = os.environ.get('LOGIN_EMAIL1')
LOGIN_PASSWORD1 = os.environ.get('LOGIN_PASSWORD1')

def send_mail(subject, content):
    SENDER_EMAIL = os.environ.get('SENDER_EMAIL')  # 发送邮件的邮箱地址
    SENDER_EMAIL_AUTH = os.environ.get("SENDER_EMAIL_AUTH")  # 邮箱授权码
    RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL")  # 接收结果的邮箱
    """发送邮件通知"""
    if not all([SENDER_EMAIL, SENDER_EMAIL_AUTH, RECIPIENT_EMAIL]):
        print("⚠️ 邮件配置不完整，跳过发送")
        return False
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = SENDER_EMAIL
    message['To'] = RECIPIENT_EMAIL
    message['Subject'] = subject
    try:
        # 3. 使用 with 语句自动管理连接，离开代码块时会自动 quit()
        with smtplib.SMTP_SSL("smtp.qq.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_EMAIL_AUTH)
            smtp.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, message.as_string())
        print("📧 邮件通知发送成功")
    except Exception as e:
        print(f"📧 邮件通知发送失败: {e}")

def send_telegram(text):
    TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
    TG_CHAT_ID = int(os.environ.get("TG_CHAT_ID"))
    """发送 Telegram 机器人通知"""
    # 1. 校验必要配置
    if not all([TG_BOT_TOKEN, TG_CHAT_ID]):
        print("⚠️ Telegram 环境变量配置不完整，跳过发送")
        return
    # 2. 构建 API URL 和 请求载荷 (Payload)
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",  # 支持 HTML 或 Markdown 解析，让消息可以加粗、换行等
        "disable_web_page_preview": True  # 可选：关闭链接预览，避免消息太长
    }
    try:
        # 3. 发送 POST 请求，设置 10 秒超时防止程序卡死
        response = requests.post(url, json=payload, timeout=10)
        # 4. 检查 HTTP 响应状态码，如果不是 200 会抛出异常
        response.raise_for_status()
        print("✈️ Telegram 通知发送成功")
    except requests.exceptions.RequestException as e:
        print(f"✈️ Telegram 通知发送失败: {e}")


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
    final_msg = ""  # 用于记录准备发送给邮件的内容

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
            "account": LOGIN_EMAIL1,
            "password": LOGIN_PASSWORD1,
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
            final_msg = f"账号: {LOGIN_EMAIL1}\n签到结果: {response.text}"
            send_telegram("✅ 蓝通云签到任务成功\n"+response.text)
            
        else:
            print(f"❌ 登录失败: {login_res.get('message')}")
            final_msg = f"账号: {LOGIN_EMAIL1}\n登录失败，请检查验证码或密码。"
            send_telegram("❌ 蓝通云签到失败，登入失败\n")

    except Exception as e:
        print(f"🔥 脚本运行异常: {e}")
        error_info = f"运行异常: {str(e)}"
        send_mail("⚠️ 签到任务异常报错", error_info)

if __name__ == "__main__":
    if LOGIN_EMAIL1 and LOGIN_PASSWORD1:
        start_task()
    else:
        print("❌ 错误: 未在 GitHub Secrets 中设置登入账号密码系统变量")
