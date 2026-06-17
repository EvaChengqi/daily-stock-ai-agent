import os
import random
import time
from datetime import datetime
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from google import genai
from google.genai.errors import ServerError

STOCKS = ['vrt', 'mvll', 'avgo', 'meta', 'nvda', 'mrvl', 'mu', 'lite', 'nbis']
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def get_quantitative_data():
    """高级量化层：抓取核心股票的实时价格、PEG、P/S 以及现金流盈利质量"""
    print("📈 正在从雅虎财经抓取多维度量化与核心财务指标...")
    data_summary = []
    
    for ticker in STOCKS:
        try:
            stock = yf.Ticker(ticker)
            # 1. 获取最新交易数据
            hist = stock.history(period="5d")
            if hist.empty:
                continue
                
            latest_close = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else latest_close
            pct_change = ((latest_close - prev_close) / prev_close) * 100
            volume = hist['Volume'].iloc[-1]
            
            # 2. 抓取基本面核心财务指标
            info = stock.info
            
            # PEG Ratio
            peg = info.get('pegRatio', None)
            # P/S Ratio
            ps = info.get('priceToSalesTrailing12Months', None)
            
            # 现金流盈利真实性：经营现金流 (CFO) / 净利润 (Net Income)
            # 比例越接近或大于 1，说明利润全是真金白银；比例太低说明全是应收账款或水分
            cfo_to_ni = None
            try:
                financials = stock.financials
                cashflow = stock.cashflow
                if not financials.empty and not cashflow.empty:
                    net_income = financials.loc['Net Income'].iloc[0]
                    operating_cash_flow = cashflow.loc['Operating Cash Flow'].iloc[0]
                    if net_income and net_income != 0:
                        cfo_to_ni = operating_cash_flow / net_income
            except:
                pass # 边缘个股若缺失财报项则跳过
            
            data_summary.append({
                "Ticker": ticker.upper(),
                "Close": round(latest_close, 2),
                "Change%": round(pct_change, 2),
                "PEG": round(peg, 2) if peg is not None else "N/A",
                "P/S": round(ps, 2) if ps is not None else "N/A",
                "CashFlow_Quality(CFO/NI)": round(cfo_to_ni, 2) if cfo_to_ni is not None else "N/A",
                "Volume": int(volume)
            })
        except Exception as e:
            print(f"⚠️ 无法完整获取 {ticker} 的量化指标: {e}")
            
    return pd.DataFrame(data_summary)

def generate_multi_charts(df_quant, today_str):
    """高级可视化层：绘制看板（左图：今日涨跌幅，右图：PEG与P/S分布）"""
    print("🎨 正在绘制多维度定量看板组合图...")
    if df_quant.empty:
        return None
        
    df_sorted_change = df_quant.sort_values(by="Change%")
    
    # 初始化一个 1行2列 的精美画布
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # ------------------ 左图：板块涨跌幅 ------------------
    colors = ['#ef5350' if x < 0 else '#26a69a' for x in df_sorted_change['Change%'].values]
    bars = ax1.bar(df_sorted_change['Ticker'], df_sorted_change['Change%'], color=colors, edgecolor='black', alpha=0.8)
    ax1.axhline(0, color='black', linewidth=0.8, linestyle='--')
    ax1.set_title("Daily Return (%)", fontsize=11, fontweight='bold')
    ax1.set_ylabel("Percentage (%)")
    ax1.grid(axis='y', linestyle=':', alpha=0.6)
    
    for bar in bars:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + (0.2 if yval >= 0 else -0.6), 
                 f"{yval:+.2f}%", ha='center', va='bottom', fontsize=8, fontweight='bold')

    # ------------------ 右图：PEG 与 P/S 交叉匹配 ------------------
    # 过滤掉无法画图的 N/A 字段
    df_valuation = df_quant[(df_quant['PEG'] != 'N/A') & (df_quant['P/S'] != 'N/A')].copy()
    if not df_valuation.empty:
        df_valuation['PEG'] = df_valuation['PEG'].astype(float)
        df_valuation['P/S'] = df_valuation['P/S'].astype(float)
        
        # 绘制散点图：横轴为 PEG（成长匹配度），纵轴为 P/S（营收效率）
        ax2.scatter(df_valuation['PEG'], df_valuation['P/S'], color='#3b82f6', s=150, edgecolors='black', alpha=0.8, zorder=3)
        ax2.axvline(1.0, color='#f59e0b', linewidth=1, linestyle=':', label='PEG = 1.0 (Fair Value)') # PEG=1 是公认估值锚点
        
        for i, txt in enumerate(df_valuation['Ticker']):
            ax2.annotate(txt, (df_valuation['PEG'].iloc[i], df_valuation['P/S'].iloc[i]), 
                         textcoords="offset points", xytext=(0,10), ha='center', fontsize=9, fontweight='bold')
                         
        ax2.set_title("Valuation Matrix: PEG vs P/S", fontsize=11, fontweight='bold')
        ax2.set_xlabel("PEG Ratio (Lower = Cheaper Growth)", fontsize=9)
        ax2.set_ylabel("Price-to-Sales (P/S) Ratio", fontsize=9)
        ax2.grid(linestyle=':', alpha=0.6)
        ax2.legend(loc='upper right')
    else:
        ax2.text(0.5, 0.5, "Insufficient Valuation Data For Plotting", ha='center', va='center')

    plt.suptitle(f"AI Infrastructure Quant & Valuation Dashboard ({today_str})", fontsize=14, fontweight='bold')
    
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
    
    # 1. 量化与多图表可视化
    df_quant = get_quantitative_data()
    chart_path = generate_multi_charts(df_quant, today_str)
    quant_table_str = df_quant.to_markdown(index=False) if not df_quant.empty else "暂无今日量化数据"
    
    # 2. 构造高密度多维度 Prompt
    PROMPT = f"""
你是一个资深的硬科技与AI基础设施行业研究员（Data & Semiconductor Specialist）。
请结合我为你提供的【多维度真实量化基本面指标表格】，撰写一份定性与定量深度结合的半导体每日精炼报道。

📈 今日多维度核心量化与基本面财务指标：
{quant_table_str}

请在文章中严格结合这些量化指标，输出以下四大板块：
1. **盘面与多维估值解码（定性+定量）**：
   - **PEG 维度**：揪出谁的 PEG 显著小于 1（代表性价比极高的高成长），谁的 PEG 过高（警惕估值透支）。
   - **P/S 维度**：针对早期或尚处于大规模研发投入阶段、利润不稳的公司（如无利润或低利润标的），用 P/S 评估其目前的收入规模扩张效率。
   - **现金流盈利真实性 (CFO/NI)**：重点穿透如 NVDA、META 等高利润巨头的 CFO/NI 比率。如果该值大于 1，证明利润非常健康、全是真金白银现金流入；若显著小于 1，警告读者其存在利润水分或应收账款积压。
2. **收并购与重大业务动态**：最新并购传闻、官宣或战略合作。
3. **华尔街机构态度**：核心投行、评级机构对他们的最新评价、目标价调动。
4. **今日参考源 (References)**：列出你生成上述定性内容所依据的今日真实新闻出处。
"""

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    response = None
    max_retries = 5
    base_delay = 4
    
    for attempt in range(max_retries):
        try:
            print(f"🧠 正在呼叫 Gemini 进行多维度量化+定性混合行业深度分析 (尝试第 {attempt + 1}/{max_retries} 次)...")
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=PROMPT,
            )
            break
        except ServerError as e:
            if attempt == max_retries - 1:
                raise e
            sleep_time = (base_delay ** (attempt + 1)) + random.uniform(1, 3)
            print(f"⚠️ Google 服务器拥堵 (503)。将在 {round(sleep_time, 1)} 秒后自动重试...")
            time.sleep(sleep_time)

    # 3. 保存并融合输出
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/{today_str}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 📊 AI Infrastructure & Data Stock Daily ({today_str})\n\n")
        if chart_path:
            f.write(f"### 📉 多维量化与估值分析看板\n")
            f.write(f"![Quant Dashboard](assets/{today_str}.png)\n\n")
            f.write(f"---\n\n")
        f.write(response.text)
        
    print(f"🎉 包含 PEG/PS/现金流分析的深度报告及组合图表已成功生成: {filename}")

if __name__ == "__main__":
    main()
