import requests
import json
import os
import re
from datetime import datetime
import xml.etree.ElementTree as ET
import time

# ============ 分类关键词 ============
KEY_NEWS_KEYWORDS = ['招股书', '上市', '备案', '批文', '港交所', '科创板', '纳斯达克', 'IPO', '过会', '提交申请', '挂牌', '纽交所']
FUNDING_KEYWORDS = ['融资', '估值', 'Pre-A', 'A轮', 'B轮', 'C轮', 'D轮', '天使轮', '种子轮', '战略投资', '亿元', '千万级', '收购']
FILTER_KEYWORDS = [
    'AI', '人工智能', '大模型', 'Agent', 'OpenAI', 'Anthropic', 'DeepMind',
    'GPT', 'Claude', 'Gemini', 'LLM', 'Copilot', 'Sora', 'Stable Diffusion',
    '智谱', '月之暗面', '百川', 'MiniMax', '零一万物', '深度求索', 'DeepSeek',
    '科大讯飞', '商汤', '第四范式', 'Kimi', '豆包', '文心一言', '通义千问',
    '混元', '数字营销', 'MarTech', 'AIGC', '生成式', 'ChatGPT', 'Bard',
    'Midjourney', 'Runway', 'Perplexity', 'Character.AI', 'Cohere',
    'xAI', 'Grok', 'Llama', 'Mistral', 'Inflection', 'Synthesia'
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
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
            print(f"[{source_name}] 非200状态，跳过")
            return items
        
        content = resp.text
        
        # 尝试XML解析
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
            # JSON格式的RSS（如RSSHub）
            try:
                data = resp.json()
                articles = data if isinstance(data, list) else data.get('items', [])
                for a in articles[:20]:
                    title = a.get('title', '')
                    link = a.get('url', '') or a.get('link', '')
                    desc = a.get('content_text', '') or a.get('description', '') or a.get('summary', '')
                    date = a.get('date_published', '') or a.get('pubDate', '') or datetime.now().strftime('%Y-%m-%d')
                    if title and link:
                        items.append({
                            'title': title.strip(),
                            'link': link.strip(),
                            'source': source_name,
                            'summary': clean_html(str(desc))[:200],
                            'date': format_date(date)
                        })
            except json.JSONDecodeError:
                print(f"[{source_name}] 无法解析内容格式")
        
        print(f"[{source_name}] 获取到 {len(items)} 条")
    except Exception as e:
        print(f"[{source_name}] 异常: {type(e).__name__}: {str(e)[:100]}")
    return items


def fetch_techcrunch_ai():
    """TechCrunch AI板块 RSS"""
    return fetch_rss("https://techcrunch.com/category/artificial-intelligence/feed/", "TechCrunch AI")


def fetch_theverge_ai():
    """The Verge AI板块 RSS"""
    return fetch_rss("https://www.theverge.com/ai-artificial-intelligence/rss/index.xml", "The Verge AI")


def fetch_venturebeat_ai():
    """VentureBeat AI RSS"""
    return fetch_rss("https://venturebeat.com/category/ai/feed/", "VentureBeat AI")


def fetch_36kr_rsshub():
    """36氪通过RSSHub公共实例"""
    urls = [
        "https://rsshub.app/36kr/information/ai",
        "https://rsshub.rssforever.com/36kr/information/ai",
        "https://rsshub.pseudoyu.com/36kr/information/ai",
    ]
    for url in urls:
        items = fetch_rss(url, "36氪-RSSHub")
        if items:
            return items
    return []


def fetch_jiemian_rsshub():
    """界面新闻科技"""
    urls = [
        "https://rsshub.app/jiemian/list/4",
        "https://rsshub.rssforever.com/jiemian/list/4",
    ]
    for url in urls:
        items = fetch_rss(url, "界面新闻")
        if items:
            return items
    return []


def filter_and_classify(items):
    results = []
    for item in items:
        text = (item['title'] + ' ' + item.get('summary', '')).lower()
        
        if not any(kw.lower() in text for kw in FILTER_KEYWORDS):
            continue
        
        matched_kw = [kw for kw in FILTER_KEYWORDS if kw.lower() in text]
        
        title_orig = item['title']
        if any(kw in title_orig for kw in KEY_NEWS_KEYWORDS):
            category = 'key_news'
        elif any(kw in title_orig for kw in FUNDING_KEYWORDS):
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


def main():
    print(f"\n{'='*60}")
    print(f"AI资讯抓取开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    all_items = []
    
    # 海外源（GitHub Actions能稳定访问）
    print(">>> 抓取 TechCrunch AI...")
    all_items.extend(fetch_techcrunch_ai())
    time.sleep(1)
    
    print("\n>>> 抓取 The Verge AI...")
    all_items.extend(fetch_theverge_ai())
    time.sleep(1)
    
    print("\n>>> 抓取 VentureBeat AI...")
    all_items.extend(fetch_venturebeat_ai())
    time.sleep(1)
    
    # 国内源通过RSSHub
    print("\n>>> 抓取 36氪 (RSSHub)...")
    all_items.extend(fetch_36kr_rsshub())
    time.sleep(1)
    
    print("\n>>> 抓取 界面新闻 (RSSHub)...")
    all_items.extend(fetch_jiemian_rsshub())
    
    print(f"\n{'='*60}")
    print(f"所有源合计抓取: {len(all_items)} 条")
    
    filtered = filter_and_classify(all_items)
    print(f"关键词过滤后: {len(filtered)} 条")
    
    seen = set()
    unique = []
    for item in filtered:
        if item['link'] not in seen:
            seen.add(item['link'])
            unique.append(item)
    print(f"去重后: {len(unique)} 条")
    
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


if __name__ == '__main__':
    main()
