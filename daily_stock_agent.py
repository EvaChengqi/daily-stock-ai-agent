name: Daily Stock Agent (Save to Repo)

on:
  schedule:
    - cron: '30 23 * * *'
  workflow_dispatch:

jobs:
  build-and-run:
    runs-on: ubuntu-latest
    
    permissions:
      contents: write

    steps:
    # 1. 拉取仓库代码
    - name: Check out repository code
      uses: actions/checkout@v3

    # 2. 明确配置 Python 环境
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    # 3. 【核心修正】使用 python -m pip 确保依赖安装到当前 Python 环境的 Context 中
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        python -m pip install -r requirements.txt

    # 4. 运行 Agent 脚本
    - name: Execute Daily Agent Script
      env:
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      run: python daily_stock_agent.py

    # 5. 自动把新文件推送到你的 GitHub 仓库
    - name: Commit and Push Report
      run: |
        git config --local user.email "github-actions[bot]@users.noreply.github.com"
        git config --local user.name "github-actions[bot]"
        git add reports/*.md
        git diff --quiet && git diff --staged --quiet || (git commit -m "Add daily report $(date +'%Y-%m-%d')" && git push)
