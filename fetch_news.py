#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI行业每日资讯抓取脚本
从36氪、虎嗅、投资界抓取AI相关资讯，按关键词过滤并分类。
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta

import requests
from bs4 import BeautifulSoup

# ---------- 配置 ----------
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "news.json")

CST = timezone(timedelta(hours=8))
TODAY = datetime.now(CST).strftime("%Y-%m-%d")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com/",
}

# 关键词规则：(正则模式, 是否区分大小写)
KEYWORDS = [
    (r"大模型", False),
    (r"AI\s*agent", False),
    (r"上市", False),
    (r"招股书", False),
    (r"备案", False),
    (r"批文", False),
    (r"融资", False),
    (r"估值", False),
    (r"OpenAI", False),
    (r"Anthropic", False),
    (r"Google\s*DeepMind", False),
    (r"微软\s*AI", False),
    (r"Meta\s*AI", False),
    (r"港交所", False),
    (r"科创板", False),
]

# 分类规则
CATEGORY_ZHONGDIAN = [
    r"招股书", r"上市", r"备案", r"批文", r"港交所", r"科创板"
]
CATEGORY_TOURONG = [
    r"融资", r"估值", r"Pre-A", r"A轮", r"B轮", r"C轮"
]


def match_keywords(text: str) -> list[str]:
    """返回文本中命中的所有关键词标签（去重）。"""
    matched = []
    for pattern, ignore_case in KEYWORDS:
        flags = re.IGNORECASE if ignore_case else 0
        if re.search(pattern, text, flags):
            # 取模式中去掉转义和修饰符的可读版本
            label = pattern.replace(r"\s*", " ").strip()
            matched.append(label)
    return list(dict.fromkeys(matched))  # 保序去重


def classify(text: str) -> str:
    """根据文本内容返回分类标签。"""
    for pat in CATEGORY_ZHONGDIAN:
        if re.search(pat, text, re.IGNORECASE):
            return "重点资讯"
    for pat in CATEGORY_TOURONG:
        if re.search(pat, text, re.IGNORECASE):
            return "投融资"
    return "其他资讯"


# ===================== 36氪 =====================
def scrape_36kr() -> list[dict]:
    """从36氪AI频道抓取文章。"""
    results = []
    try:
        # 36氪使用 API 加载数据，直接请求 JSON 接口
        api_url = "https://gateway.36kr.com/api/mis/newsflow/information/nav"
        payload = {
            "param": {
                "pageSize": 20,
                "pageNum": 1,
            }
        }
        resp = requests.post(
            api_url,
            json=payload,
            headers={**HEADERS, "Content-Type": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data", {}).get("data", {}).get("itemList", [])

        # 备用：解析 HTML
        if not items:
            html_url = "https://36kr.com/information/ai"
            resp2 = requests.get(html_url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp2.text, "lxml")
            items = soup.select(".information-flow-item, .article-item-wrapper, [data-item]")
            for item in items:
                title_el = item.select_one("a.item-title, .article-item-title a, a[href*='/p/']")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                link = title_el.get("href", "")
                if link and not link.startswith("http"):
                    link = "https://36kr.com" + link
                summary_el = item.select_one(".item-desc, .article-item-description")
                summary = summary_el.get_text(strip=True) if summary_el else ""
                combined = f"{title} {summary}"
                kw = match_keywords(combined)
                if kw:
                    results.append({
                        "title": title,
                        "link": link,
                        "source": "36氪",
                        "category": classify(combined),
                        "summary": summary,
                        "keywords": kw,
                        "date": TODAY,
                    })
            return results

        # 处理 API 返回的数据
        for item in items:
            tmpl = item.get("templateMaterial", item.get("itemMaterial", item))
            title = tmpl.get("widgetTitle", tmpl.get("title", ""))
            link_path = tmpl.get("widgetUrl", tmpl.get("url", tmpl.get("shareUrl", "")))
            link = link_path if link_path.startswith("http") else f"https://36kr.com{link_path}"
            summary = tmpl.get("widgetContent", tmpl.get("summary", tmpl.get("description", "")))
            if isinstance(summary, dict):
                summary = summary.get("text", "")
            combined = f"{title} {summary}"
            kw = match_keywords(combined)
            if kw:
                results.append({
                    "title": title,
                    "link": link,
                    "source": "36氪",
                    "category": classify(combined),
                    "summary": summary[:200] if summary else "",
                    "keywords": kw,
                    "date": TODAY,
                })
        print(f"[36氪] 抓取到 {len(results)} 条相关资讯")
    except Exception as e:
        print(f"[36氪] 抓取失败: {e}", file=sys.stderr)
    return results


# ===================== 虎嗅 =====================
def scrape_huxiu() -> list[dict]:
    """从虎嗅AI频道抓取文章。"""
    results = []
    try:
        # 虎嗅使用 API
        api_url = "https://www.huxiu.com/v2_action/article_list"
        params = {
            "page": 1,
            "pagesize": 30,
            "platform": "www",
        }
        resp = requests.get(api_url, params=params, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            # 备用：抓取 HTML
            html_url = "https://www.huxiu.com/channel/ai.html"
            resp2 = requests.get(html_url, headers=HEADERS, timeout=15)
            resp2.raise_for_status()
            soup = BeautifulSoup(resp2.text, "lxml")
            cards = soup.select(".article-item, .mod-b .mob-ctt, .article-wrap")
            for card in cards:
                title_el = card.select_one("h2 a, .mob-sub a, a[href*='/article/']")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                link = title_el.get("href", "")
                if link and not link.startswith("http"):
                    link = "https://www.huxiu.com" + link
                summary_el = card.select_one(".mob-sub, .article-content, p")
                summary = summary_el.get_text(strip=True) if summary_el else ""
                combined = f"{title} {summary}"
                kw = match_keywords(combined)
                if kw:
                    results.append({
                        "title": title,
                        "link": link,
                        "source": "虎嗅",
                        "category": classify(combined),
                        "summary": summary[:200],
                        "keywords": kw,
                        "date": TODAY,
                    })
            return results

        data = resp.json()
        articles = data.get("data", {}).get("dataList", [])
        for art in articles:
            title = art.get("title", "")
            aid = art.get("aid", "")
            link = f"https://www.huxiu.com/article/{aid}.html" if aid else art.get("share_url", "")
            summary = art.get("summary", art.get("description", ""))
            combined = f"{title} {summary}"
            kw = match_keywords(combined)
            if kw:
                results.append({
                    "title": title,
                    "link": link,
                    "source": "虎嗅",
                    "category": classify(combined),
                    "summary": summary[:200] if summary else "",
                    "keywords": kw,
                    "date": TODAY,
                })
        print(f"[虎嗅] 抓取到 {len(results)} 条相关资讯")
    except Exception as e:
        print(f"[虎嗅] 抓取失败: {e}", file=sys.stderr)
    return results


# ===================== 投资界 =====================
def scrape_pedaily() -> list[dict]:
    """从投资界快讯频道抓取文章。"""
    results = []
    try:
        html_url = "https://www.pedaily.cn/news/"
        resp = requests.get(html_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")
        items = soup.select(".news-list li, .news-item, .hot-news li, .info-list li")
        if not items:
            # 尝试更宽泛的选择器
            items = soup.select("a[href*='/news/'], a[href*='/p/']")
            seen = set()
            for a in items[:50]:
                title = a.get_text(strip=True)
                link = a.get("href", "")
                if not title or len(title) < 8:
                    continue
                if link in seen:
                    continue
                seen.add(link)
                if link and not link.startswith("http"):
                    link = "https://www.pedaily.cn" + link
                combined = title
                kw = match_keywords(combined)
                if kw:
                    results.append({
                        "title": title,
                        "link": link,
                        "source": "投资界",
                        "category": classify(combined),
                        "summary": "",
                        "keywords": kw,
                        "date": TODAY,
                    })
            return results

        for item in items[:30]:
            title_el = item.select_one("h3 a, .news-title a, a[href*='/news/'], a.title")
            if not title_el:
                title_el = item.find("a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            link = title_el.get("href", "")
            if link and not link.startswith("http"):
                link = "https://www.pedaily.cn" + link
            summary_el = item.select_one(".desc, .news-desc, p")
            summary = summary_el.get_text(strip=True) if summary_el else ""
            combined = f"{title} {summary}"
            kw = match_keywords(combined)
            if kw:
                results.append({
                    "title": title,
                    "link": link,
                    "source": "投资界",
                    "category": classify(combined),
                    "summary": summary[:200],
                    "keywords": kw,
                    "date": TODAY,
                })
        print(f"[投资界] 抓取到 {len(results)} 条相关资讯")
    except Exception as e:
        print(f"[投资界] 抓取失败: {e}", file=sys.stderr)
    return results


def deduplicate(articles: list[dict]) -> list[dict]:
    """按标题去重，保留先出现的。"""
    seen = set()
    unique = []
    for art in articles:
        norm = re.sub(r"\s+", "", art["title"]).lower()
        if norm not in seen:
            seen.add(norm)
            unique.append(art)
    return unique


def main():
    all_articles = []

    print("=" * 50)
    print(f"AI资讯抓取开始 - {TODAY}")
    print("=" * 50)

    # 逐个源抓取
    all_articles.extend(scrape_36kr())
    time.sleep(1)

    all_articles.extend(scrape_huxiu())
    time.sleep(1)

    all_articles.extend(scrape_pedaily())

    # 去重
    all_articles = deduplicate(all_articles)

    # 按分类排序：重点资讯 > 投融资 > 其他
    cat_order = {"重点资讯": 0, "投融资": 1, "其他资讯": 2}
    all_articles.sort(key=lambda x: cat_order.get(x["category"], 99))

    # 输出
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)

    print(f"\n总计抓取到 {len(all_articles)} 条AI相关资讯，已保存至 {OUTPUT_FILE}")

    # 统计
    cats = {}
    for a in all_articles:
        cats[a["category"]] = cats.get(a["category"], 0) + 1
    for cat, count in cats.items():
        print(f"  - {cat}: {count} 条")


if __name__ == "__main__":
    main()
