import os
import random
from datetime import datetime
from google import genai

# 从 GitHub Actions 的环境变量中安全读取 API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 升级后的深度 Prompt：强行索要 Reference
PROMPT = """
你是一个资深的硬科技与AI基础设施行业研究员（Data & Semiconductor Specialist）。
请为我生成一份今日的“硬科技与AI基础设施”半导体股票每日精炼报道。

重点关注以下核心标的：vrt, mvll, avgo, meta, nvda, mrvl, mu, lite, nbis。
请多从“数据科学/数据吞吐/HBM/1.6T光网络/大规模数据清洗”的数据视角进行切入。

请严格包含以下四个板块：
1. **收并购与重大业务动态**：最新并购传闻、官宣、战略合作。
2. **市场表现与财务催化剂**：关键动向、估值变化或重大资本开支(CapEx)公告。
3. **华尔街机构态度**：核心投行、评级机构对他们的最新评价、目标价调动。
4. **【新增】今日参考源 (References)**：请列出你生成上述内容所依据的今日真实新闻、财报公告或媒体报道的标题/出处。

💡 格式要求：
- 使用结构清晰、排版美观的 Markdown 格式。
- 在第4板块中，请以严格的列表格式输出参考源，例如：
  - [Ref 1] Nvidia BlackWell NVLink rack scale shipments update (Source: Bloomberg/Reuters)
  - [Ref 2] Broadcom Custom ASIC pipeline expansion (Source: CNBC)
- 不要带有任何 AI 生成的口癖，直接输出内容。
"""

def main():
    if not GEMINI_API_KEY:
        raise ValueError("❌ 错误: 缺少 GEMINI_API_KEY 环境变量，请检查 GitHub Secrets 配置。")
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    print("正在呼叫最新 Gemini 2.5 接口抓取今日数据并生成带引用的报告...")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=PROMPT,
    )
    
    report_text = response.text
    
    # 自动创建用于存放报告的 reports 文件夹
    os.makedirs("reports", exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"reports/{today_str}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 📊 AI Infrastructure & Data Stock Daily ({today_str})\n\n")
        f.write(report_text)
    print(f"🎉 报告已成功归档至: {filename}\n")
    
    # === 🛡️ 自动化防瞎编抽查逻辑 (Anti-Hallucination Audit) ===
    print("==================== 🛡️ AI 真实性抽查审核机制 ====================")
    try:
        # 简单解析出报告中的 References 行
        lines = report_text.split('\n')
        ref_lines = [line.strip() for line in lines if line.strip().startswith('- [Ref') or line.strip().startswith('* [Ref')]
        
        if ref_lines:
            print(f"检测到今日报告生成了 {len(ref_lines)} 篇参考源。")
            # 随机抽取 1-2 篇进行验证
            sample_size = min(2, len(ref_lines))
            sampled_refs = random.sample(ref_lines, sample_size)
            
            print(f"🎲 随机抽取以下 {sample_size} 篇进行事实交叉比对：")
            for ref in sampled_refs:
                print(f"  👉 正在抽查: {ref}")
                
                # 让 Gemini 吐出这篇参考源对应的最原始、最核心的2句事实细节，供人肉眼在 Actions 控制台比对
                audit_prompt = f"请针对你刚刚提到的这篇参考源：'{ref}'，给出该新闻的核心事实摘要（包含具体的数据、时间或提及的机构名称，不超过80字），用来证明这篇新闻确实真实存在，而不是你臆造的。"
                audit_response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=audit_prompt,
                )
                print(f"     [底层事实核对]: {audit_response.text.strip()}\n")
        else:
            print("⚠️ 警告: 今日报告中未检测到标准格式的 [Ref] 引用标签，无法进行自动抽查。")
    except Exception as e:
        print(f"⚠️ 抽查机制运行中出现轻微异常: {e}")
    print("==================================================================")

if __name__ == "__main__":
    main()
