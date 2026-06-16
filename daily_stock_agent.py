import os
from datetime import datetime
from google import genai  # 👈 导入全新的统一 SDK

# 从 GitHub Actions 的环境变量中安全读取 API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

PROMPT = """
你是一个资深的硬科技与AI基础设施行业研究员（Data & Semiconductor Specialist）。
请为我生成一份今日的“硬科技与AI基础设施”半导体股票每日精炼报道。

重点关注以下核心标的：vrt, mvll, avgo, meta, nvda, mrvl, mu, lite, nbis。

请严格包含以下三个板块，并多从“数据科学/数据吞吐/HBM/1.6T光网络/大规模数据清洗”的数据视角进行切入：
1. **收并购与重大业务动态**：他们之间或行业内最新的并购传闻、官宣、战略合作。
2. **市场表现与财务催化剂**：最新股票的关键动向、估值变化或重大资本开支(CapEx)公告。
3. **华尔街机构态度**：核心投行、评级机构对他们的最新评价、目标价调动。

💡 格式要求：
- 使用结构清晰、排版美观的 Markdown 格式。
- 不要带有任何 AI 生成的口癖（如"好的，这是为您整理的..."），直接输出内容。
- 如果某只股票当天完全没有任何新闻，直接略过该股票，保持信息的高密度。
"""

def main():
    if not GEMINI_API_KEY:
        raise ValueError("❌ 错误: 缺少 GEMINI_API_KEY 环境变量，请检查 GitHub Secrets 配置。")
        
    # 使用新版 SDK 的标准客户端初始化方式
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    print("正在呼叫最新 Gemini 2.5 接口抓取今日数据...")
    # 升级到 2026 年最新主流的 gemini-2.5-flash 模型
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=PROMPT,
    )
    
    # 自动创建用于存放报告的 reports 文件夹
    os.makedirs("reports", exist_ok=True)
    
    # 获取今天日期并拼装文件名
    today_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"reports/{today_str}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# 📊 AI Infrastructure & Data Stock Daily\n\n")
        f.write(response.text)
    
    print(f"🎉 报告生成成功: {filename}")

if __name__ == "__main__":
    main()
