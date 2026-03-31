import cloudscraper
import os
import cloudscraper
import ddddocr
import base64
import json
import smtplib
from email.mime.text import MIMEText
from email.header import Header
# 从 GitHub Secrets 读取敏感信息
MY_EMAIL = os.environ.get('MY_EMAIL')
MY_PASSWORD = os.environ.get('MY_PASSWORD')
EMAIL_PASS = os.environ.get("EMAIL_PASS")  # QQ邮箱授权码
RECEIVE_EMAIL = os.environ.get("SEND_EMAIL")  # 接收结果的邮箱


def send_mail(subject, content):
    """发送邮件通知"""
    if not EMAIL_PASS:
        print("⚠️ 未配置 EMAIL_PASS，跳过邮件发送")
        return

    sender = MY_EMAIL
    receivers = [RECEIVE_EMAIL]
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = sender
    message['To'] = RECEIVE_EMAIL
    message['Subject'] = Header(subject, 'utf-8')
    try:
        smtp_obj = smtplib.SMTP_SSL("smtp.qq.com", 465)
        smtp_obj.login(sender, EMAIL_PASS)
        smtp_obj.sendmail(sender, receivers, message.as_string())
        smtp_obj.quit()
        print("📧 邮件通知发送成功")
    except Exception as e:
        print(f"📧 邮件通知发送失败: {e}")


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
            final_msg = f"账号: {MY_EMAIL}\n签到结果: {response.text}"
            send_mail("✅ 签到任务成功通知", final_msg)
        else:
            print(f"❌ 登录失败: {login_res.get('message')}")
            final_msg = f"账号: {MY_EMAIL}\n登录失败，请检查验证码或密码。"
            send_mail("❌ 签到任务失败提醒", final_msg)

    except Exception as e:
        print(f"🔥 脚本运行异常: {e}")
        error_info = f"运行异常: {str(e)}"
        send_mail("⚠️ 签到任务异常报错", error_info)


if __name__ == "__main__":
    if MY_EMAIL and MY_PASSWORD:
        start_task()
    else:
        print("❌ 错误: 未在 GitHub Secrets 中设置系统变量")
