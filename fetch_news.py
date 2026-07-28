import requests
import json
import os
import re
from datetime import datetime
import xml.etree.ElementTree as ET
import time

KEY_NEWS_KEYWORDS = ['招股书', '上市', '备案', '批文', '港交所', '科创板', '纳斯达克', 'IPO', 'filing', 'listed', 'stock exchange', 'NYSE', 'NASDAQ', 'HKEX', 'SEC filing', 'go public', 'regulatory approval', '获批', '许可证']
FUNDING_KEYWORDS = ['融资', '估值', 'A轮', 'B轮', 'C轮', 'D轮', '天使轮', '种子轮', '战略投资', '亿元', 'funding', 'raises', 'raised', 'million', 'billion', 'Series A', 'Series B', 'Series C', 'seed round', 'valuation', 'venture capital', 'acquisition', 'acquired', 'merger', 'investment']
FILTER_KEYWORDS = [
    'AI', '人工智能', '大模型', 'Agent', 'OpenAI', 'Anthropic', 'DeepMind',
    'GPT', 'Claude', 'Gemini', 'LLM', 'Copilot', 'Sora',
    '智谱', '月之暗面', '百川', 'MiniMax', '零一万物', '深度求索', 'DeepSeek',
    '科大讯飞', '商汤', '第四范式', 'Kimi', '豆包', '文心一言', '通义千问',
    '混元', '数字营销', 'MarTech', 'AIGC', '生成式', 'ChatGPT',
    'Midjourney', 'Runway', 'Perplexity',
    'xAI', 'Grok', 'Llama', 'Mistral',
    'machine learning', 'neural network', 'transformer', 'diffusion',
    '机器人', '自动驾驶', '智能', '算法'
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, application/json, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


def clean_html(text):
    if not text:
        return ''
    return re.sub(r'<.*?>', '', text).strip()


def format_date(date_str):
    if not date_str:
        return datetime.now().strftime('%Y-%m-%d')
    date_str = str(date_str).strip()
    formats = [
        '%a, %d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M:%S %Z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except:
            continue
    return datetime.now().strftime('%Y-%m-%d')


def fetch_rss(url, source_name):
    """通用RSS抓取"""
    items = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        print(f"[{source_name}] HTTP状态: {resp.status_code}")
        
        if resp.status_code != 200:
            return items
        
        content_type = resp.headers.get('Content-Type', '')
        
        # JSON格式（RSSHub）
        if 'json' in content_type or url.endswith('.json'):
            try:
                data = resp.json()
                articles = data if isinstance(data, list) else data.get('items', [])
                for a in articles[:25]:
                    title = a.get('title', '')
                    link = a.get('url', '') or a.get('link', '')
                    desc = a.get('content_text', '') or a.get('description', '') or a.get('summary', '')
                    date = a.get('date_published', '') or a.get('pubDate', '') or a.get('date', '')
                    if title and link:
                        items.append({
                            'title': title.strip(),
                            'link': link.strip(),
                            'source': source_name,
                            'summary': clean_html(str(desc))[:200],
                            'date': format_date(date)
                        })
                print(f"[{source_name}] 获取到 {len(items)} 条")
                return items
            except:
                pass
        
        # XML格式
        try:
            root = ET.fromstring(resp.content)
            for item in root.iter('item'):
                title = item.find('title')
                link = item.find('link')
                desc = item.find('description')
                pub_date = item.find('pubDate')
                
                title_text = title.text.strip() if title is not None and title.text else ''
                link_text = ''
                if link is not None:
                    link_text = (link.text or '').strip()
                    # 处理CDATA
                    if link_text.startswith('<![CDATA['):
                        link_text = link_text[9:-3]
                desc_text = desc.text.strip() if desc is not None and desc.text else ''
                date_text = pub_date.text.strip() if pub_date is not None and pub_date.text else ''
                
                if title_text and link_text:
                    items.append({
                        'title': title_text,
                        'link': link_text,
                        'source': source_name,
                        'summary': clean_html(desc_text)[:200],
                        'date': format_date(date_text)
                    })
        except ET.ParseError:
            pass
        
        print(f"[{source_name}] 获取到 {len(items)} 条")
    except Exception as e:
        print(f"[{source_name}] 异常: {type(e).__name__}: {str(e)[:100]}")
    return items


def fetch_with_fallback(urls, source_name):
    """多备用地址抓取"""
    for url in urls:
        items = fetch_rss(url, source_name)
        if items:
            return items
        time.sleep(1)
    return []


def main():
    print(f"\n{'='*60}")
    print(f"AI资讯抓取开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    all_items = []
    
    # ===== 中文源（通过RSSHub公共实例）=====
    
    # 36氪 AI频道
    print(">>> 36氪 AI频道...")
    all_items.extend(fetch_with_fallback([
        "https://rsshub.pseudoyu.com/36kr/information/ai",
        "https://rsshub.rssforever.com/36kr/information/ai",
        "https://rsshub.app/36kr/information/ai",
        "https://rsshub.fly.dev/36kr/information/ai",
    ], "36氪"))
    time.sleep(1)
    
    # 界面新闻 科技
    print("\n>>> 界面新闻 科技...")
    all_items.extend(fetch_with_fallback([
        "https://rsshub.pseudoyu.com/jiemian/list/4",
        "https://rsshub.rssforever.com/jiemian/list/4",
    ], "界面新闻"))
    time.sleep(1)
    
    # 品玩
    print("\n>>> 品玩...")
    all_items.extend(fetch_with_fallback([
        "https://rsshub.pseudoyu.com/pingwest/status",
        "https://rsshub.rssforever.com/pingwest/status",
    ], "品玩"))
    time.sleep(1)
    
    # 极客公园
    print("\n>>> 极客公园...")
    all_items.extend(fetch_with_fallback([
        "https://rsshub.pseudoyu.com/geekpark/breakingnews",
        "https://rsshub.rssforever.com/geekpark/breakingnews",
    ], "极客公园"))
    time.sleep(1)
    
    # 机器之心
    print("\n>>> 机器之心...")
    all_items.extend(fetch_with_fallback([
        "https://rsshub.pseudoyu.com/jiqizhixin/home",
        "https://rsshub.rssforever.com/jiqizhixin/home",
    ], "机器之心"))
    time.sleep(1)
    
    # 量子位
    print("\n>>> 量子位...")
    all_items.extend(fetch_with_fallback([
        "https://rsshub.pseudoyu.com/qbitai",
        "https://rsshub.rssforever.com/qbitai",
    ], "量子位"))
    time.sleep(1)
    
    # ===== 海外中文科技媒体 =====
    
    # 华尔街见闻 科技
    print("\n>>> 华尔街见闻 科技...")
    all_items.extend(fetch_with_fallback([
        "https://rsshub.pseudoyu.com/wallstreetcn/news/global",
    ], "华尔街见闻"))
    time.sleep(1)
    
    # ===== 英文源（作为补充，抓取AI大公司动态）=====
    
    print("\n>>> TechCrunch AI...")
    all_items.extend(fetch_rss("https://techcrunch.com/category/artificial-intelligence/feed/", "TechCrunch"))
    
    print(f"\n{'='*60}")
    print(f"所有源合计抓取: {len(all_items)} 条")
    
    # 过滤和分类
    filtered = filter_and_classify(all_items)
    print(f"关键词过滤后: {len(filtered)} 条")
    
    # 去重
    seen = set()
    unique = []
    for item in filtered:
        if item['link'] not in seen:
            seen.add(item['link'])
            unique.append(item)
    print(f"去重后: {len(unique)} 条")
    
    # 按日期倒序
    unique.sort(key=lambda x: x['date'], reverse=True)
    
    key_news = sum(1 for i in unique if i['category'] == 'key_news')
    funding = sum(1 for i in unique if i['category'] == 'funding')
    other = sum(1 for i in unique if i['category'] == 'other')
    print(f"分类: 重点资讯={key_news}, 投融资={funding}, 其他={other}")
    
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'news.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已保存至 {output_path}")
    print(f"{'='*60}\n")


# 注意：需要把 filter_and_classify 函数放回 main 之前
def filter_and_classify(items):
    results = []
    for item in items:
        text = (item['title'] + ' ' + item.get('summary', '')).lower()
        
        if not any(kw.lower() in text for kw in FILTER_KEYWORDS):
            continue
        
        matched_kw = [kw for kw in FILTER_KEYWORDS if kw.lower() in text]
        
        title_orig = item['title']
        if any(kw.lower() in title_orig.lower() for kw in KEY_NEWS_KEYWORDS):
            category = 'key_news'
        elif any(kw.lower() in title_orig.lower() for kw in FUNDING_KEYWORDS):
            category = 'funding'
        else:
            category = 'other'
        
        results.append({
            'title': item['title'],
            'link': item['link'],
            'source': item['source'],
            'category': category,
            'summary': item.get('summary', ''),
            'keywords': matched_kw[:5],
            'date': item.get('date', datetime.now().strftime('%Y-%m-%d'))
        })
    return results


if __name__ == '__main__':
    main()
