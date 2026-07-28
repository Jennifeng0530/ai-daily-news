AI行业每日资讯
============

自动抓取并展示AI行业每日资讯，部署到 GitHub Pages，通过 GitHub Actions 每天自动更新。

数据来源
--------

- 36氪 AI频道: https://36kr.com/information/ai
- 虎嗅 AI: https://www.huxiu.com/channel/ai.html
- 投资界快讯: https://www.pedaily.cn/news/

项目结构
--------

.
├── .github/
│   └── workflows/
│       └── daily-fetch.yml   GitHub Actions 定时任务
├── data/
│   └── news.json             抓取结果（自动生成）
├── fetch_news.py             抓取脚本
├── index.html                展示网页
├── requirements.txt          Python 依赖
└── README.md

快速开始
--------

### 1. 克隆仓库

git clone https://github.com/<你的用户名>/<仓库名>.git
cd <仓库名>

### 2. 安装依赖

pip install -r requirements.txt

### 3. 手动运行抓取

python fetch_news.py

抓取结果保存在 data/news.json。可用浏览器直接打开 index.html 预览效果。

部署到 GitHub Pages
-------------------

1. 将代码推送到 GitHub 仓库。
2. 进入仓库 Settings - Pages。
3. Source 选择 Deploy from a branch，分支选择 main（或 master），目录选择 / (root)。
4. 点击 Save，稍等片刻即可通过 https://<用户名>.github.io/<仓库名>/ 访问。

自动化说明
----------

GitHub Actions 每天自动运行三次：

北京时间 08:00 / 12:00 / 18:00（UTC 00:00 / 04:00 / 10:00）

每次运行会执行 fetch_news.py，如有新资讯则自动 commit 并 push，从而触发 GitHub Pages 重新部署。

也可以在仓库的 Actions 页面手动点击 Run workflow 立即触发抓取。

关键词过滤
----------

抓取脚本只保留标题或摘要中包含以下任一关键词的文章（不区分大小写）：

大模型、AI agent、上市、招股书、备案、批文、融资、估值、OpenAI、Anthropic、Google DeepMind、微软AI、Meta AI、港交所、科创板

分类规则
--------

重点资讯（红色标签）: 含招股书/上市/备案/批文/港交所/科创板
投融资（蓝色标签）: 含融资/估值/Pre-A/A轮/B轮/C轮
其他资讯（灰色标签）: 其余

许可证
------

MIT
