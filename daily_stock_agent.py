import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import google.generativeai as genai

# ==================== 1. 配置参数 ====================
# 建议在环境变量中设置这些密钥，或者直接替换（注意不要公开代码）
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "你的_GEMINI_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "你的发件邮箱@gmail.com")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "你的邮箱应用专用密码") 
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "你的收件邮箱@xxx.com")

# ==================== 2. 问 AI 的 Prompt ====================
PROMPT = """
请为我生成一份今日的“硬科技与AI基础设施”半导体股票每日报道。
重点关注以下股票: vrt, mvll, avgo, meta, nvda, mrvl, mu, lite, nbis。

请包含以下三个板块，并多从“数据科学/数据吞吐/HBM/光网络”的数据视角进行切入：
1. 他们直接的最新收并购信息与重大业务动态。
2. 他们的最新股票表现（市值、近期涨跌趋势、关键财务催化剂）。
3. 华尔街核心机构对他们的最新评价或评级调动。

请使用结构清晰的 Markdown 格式输出，保持专业、精炼。
"""

def get_daily_report():
    """呼叫 Gemini API 获取报告"""
    genai.configure(api_key=GEMINI_API_KEY)
    # 使用 2026 年主流的、速度快且擅长信息整理的 model
    model = genai.GenerativeModel('gemini-1.5-flash') 
    
    print("正在连接 Gemini 获取今日简报...")
    response = model.generate_content(PROMPT)
    return response.text

def send_email(content_markdown):
    """通过 SMTP 发送 HTML 邮件"""
    # 将 Markdown 转换为简单的 HTML（此处为了代码精简，直接放入 pre 标签，或使用 markdown 库转换）
    # 如果想更美观，可以 pip install markdown，然后使用 markdown.markdown(content_markdown)
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 8px;">
          📊 每日硬科技与数据基础设施简报
        </h2>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
          {content_markdown.replace('\n', '<br>')}
        </div>
        <p style="font-size: 12px; color: #777; margin-top: 20px;">
          * 本邮件由您的专属 AI Agent 自动生成发送。
        </p>
      </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "【Daily AI Agent】硬科技与半导体数据简报"
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))

    print("正在发送邮件...")
    # 以 Gmail SMTP 为例，如果是其他邮箱请修改 host 和 port
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    print("邮件发送成功！")

if __name__ == "__main__":
    try:
        report = get_daily_report()
        send_email(report)
    except Exception as e:
        print(f"运行失败: {e}")