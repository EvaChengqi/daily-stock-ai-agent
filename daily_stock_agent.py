import os
import random
from datetime import datetime
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from google import genai

# 从 GitHub Actions 的环境变量中安全读取 API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
STOCKS = ['vrt', 'mvll', 'avgo', 'meta', 'nvda', 'mrvl', 'mu', 'lite', 'nbis']

def get_quantitative_data():
    """量化层：使用 yfinance 抓取核心股票的真实交易数据"""
    print("📈 正在从雅虎财经抓取量化数据...")
    data_summary = []
    plot_data = {}
    
    for ticker in STOCKS:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")  # 抓取近5日数据计算波动
            if not hist.empty:
                latest_close = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else latest_close
                pct_change = ((latest_close - prev_close) / prev_close) * 100
                volume = hist['Volume'].iloc[-1]
                
                data_summary.append({
                    "Ticker": ticker.upper(),
                    "Close": round(latest_close, 2),
                    "Change%": round(pct_change, 2),
                    "Volume": int(volume)
                })
                plot_data[ticker.upper()] = pct_change
        except Exception as e:
            print(f"⚠️ 无法获取 {ticker} 的量化数据: {e}")
            
    return pd.DataFrame(data_summary), plot_data

def generate_chart(plot_data, today_str):
    """可视化层：自动绘制今日板块涨跌幅柱状图"""
    print("🎨 正在绘制今日板块走势图...")
    if not plot_data:
        return None
        
    df_plot = pd.Series(plot_data).sort_values()
    
    plt.figure(figsize=(10, 5))
    colors = ['#ef5350' if x < 0 else '#26a69a' for x in df_plot.values] # 红跌绿涨（美股标准）
    
    bars = plt.bar(df_plot.index, df_plot.values, color=colors, edgecolor='black', alpha=0.8)
    plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
    
    # 在柱状图上标注具体数值
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + (0.2 if yval >= 0 else -0.5), 
                 f"{yval:+.2f}%", ha='center', va='bottom', fontsize=9, fontweight='bold')
                 
    plt.title(f"AI Infrastructure & Semiconductor Sector Performance ({today_str})", fontsize=12, fontweight='bold')
    plt.ylabel("Daily Return (%)", fontsize=10)
    plt.grid(axis='y', linestyle=':', alpha=0.6)
    
    # 确保文件夹存在并保存图片
    os.makedirs("reports/assets", exist_ok=True)
    chart_path = f"reports/assets/{today_str}.png"
    plt.tight_layout()
    plt.savefig(chart_path, dpi=150)
    plt.close()
    return chart_path

def main():
    if not GEMINI_API_KEY:
        raise ValueError("❌ 错误: 缺少 GEMINI_API_KEY 环境变量。")
        
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 1. 执行量化层与可视化层
    df_quant, plot_data = get_quantitative_data()
    chart_path = generate_chart(plot_data, today_str)
    
    # 将量化表格转为纯文本格式喂给大模型，实现真正的“定量数据驱动定性分析”
    quant_table_str = df_quant.to_markdown(index=False) if not df_quant.empty else "暂无今日量化数据"
    
    # 2. 结合定性大模型层
    PROMPT = f"""
你是一个资深的硬科技与AI基础设施行业研究员（Data & Semiconductor Specialist）。
请结合我为你提供的今日【真实量化交易数据】，撰写一份定性与定量深度结合的半导体每日精炼报道。

📈 今日核心量化指标：
{quant_table_str}

请严格包含以下四个板块：
1. **盘面定量解码**：结合上表，指出今天谁领涨、谁领跌？特别关注是否存在异常成交量（Volume）或大幅度暴跌（超过-5%），并从数据科学/数据吞吐/HBM/1.6T光网络等行业底层逻辑解释其背后的定量催化剂。
2. **收并购与重大业务动态**：这些核心标的之间或行业内最新的并购传闻、官宣或战略合作。
3. **华尔街机构态度**：核心投行、评级机构对他们的最新评价、目标价调动。
4. **今日参考源 (References)**：列出你生成上述定性内容所依据的今日真实新闻出处。
"""

    client = genai.Client(api_key=GEMINI_API_KEY)
    print("🧠 正在呼叫 Gemini 进行定量+定性混合行业深度分析...")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=PROMPT,
    )
    
    # 3. 编排合并 Markdown 输出
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/{today_str}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 📊 AI Infrastructure & Data Stock Daily ({today_str})\n\n")
        
        # 在 Markdown 头部动态嵌入刚刚绘制的可视化图表
        if chart_path:
            # 使用相对路径，GitHub 网页端能直接完美渲染出图片
            f.write(f"### 📉 板块走势热力图\n")
            f.write(f"![Sector Performance](assets/{today_str}.png)\n\n")
            f.write(f"---\n\n")
            
        f.write(response.text)
        
    print(f"🎉 报告与可视化图表已成功生成并融合: {filename}")

if __name__ == "__main__":
    main()
