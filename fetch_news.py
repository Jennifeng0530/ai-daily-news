import requests
import json
import os
from datetime import datetime
import xml.etree.ElementTree as ET
import re

# ============ 分类关键词 ============
KEY_NEWS_KEYWORDS = ['招股书', '上市', '备案', '批文', '港交所', '科创板', '纳斯达克', 'IPO', '过会', '提交申请']
FUNDING_KEYWORDS = ['融资', '估值', 'Pre-A', 'A轮', 'B轮', 'C轮', 'D轮', '天使轮', '种子轮', '战略投资', '亿元']
FILTER_KEYWORDS = ['大模型', 'AI agent', 'AI Agent', '人工智能', 'OpenAI', 'Anthropic', 'Google DeepMind',
                   '微软AI', 'Meta AI', '智谱', '月之暗面', '百川', 'MiniMax', '零一万物', '深度求索',
                   'DeepSeek', '科大讯飞', '商汤', '第四范式', '字节AI', '腾讯AI', '百度AI', '阿里AI',
                   'Agent', 'LLM', 'GPT', 'Claude', 'Gemini', '文心一言', '通义千问', '混元',
                   '数字营销', 'MarTech', '出海', 'AIGC', '生成式']

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_rss(url, source_name):
    """抓取RSS源"""
    items = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        
        for item_elem in root.iter('item'):
            title = item_elem.find('title')
            link = item_elem.find('link')
            description = item_elem.find('description')
            pub_date = item_elem.find('pubDate')
            
            title_text = title.text.strip() if title is not None and title.text else ''
            link_text = link.text.strip() if link is not None and link.text else ''
            desc_text = description.text.strip() if description is not None and description.text else ''
            date_text = pub_date.text.strip() if pub_date is not None and pub_date.text else datetime.now().strftime('%Y-%m-%d')
            
            if title_text and link_text:
                items.append({
                    'title': title_text,
                    'link': link_text,
                    'summary': clean_html(desc_text)[:200],
                    'date': format_date(date_text),
                    'source': source_name
                })
        print(f"[{source_name}] 抓取成功: {len(items)} 条")
    except Exception as e:
        print(f"[{source_name}] 抓取失败: {str(e)}")
    return items


def fetch_36kr_api(source_name="36氪"):
    """36氪资讯流API（备用）"""
    items = []
    try:
        url = "https://www.36kr.com/api/search/article?q=AI&per_page=20"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        data = resp.json()
        for article in data.get('data', {}).get('items', [])[:15]:
            title = article.get('title', '')
            link = f"https://www.36kr.com/p/{article.get('id', '')}"
            summary = article.get('summary', '')
            date = article.get('published_at', datetime.now().strftime('%Y-%m-%d'))[:10]
            if title:
                items.append({
                    'title': title,
                    'link': link,
                    'summary': clean_html(summary)[:200],
                    'date': date,
                    'source': source_name
                })
        print(f"[{source_name}] API抓取: {len(items)} 条")
    except Exception as e:
        print(f"[{source_name}] API抓取失败: {str(e)}")
    return items


def fetch_investment_news(source_name="投资界"):
    """投资界快讯"""
    items = []
    try:
        url = "https://www.pedaily.cn/rss/news.xml"
        items = fetch_rss(url, source_name)
    except Exception as e:
        print(f"[{source_name}] 抓取失败: {str(e)}")
    return items


def clean_html(text):
    """去除HTML标签"""
    if not text:
        return ''
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def format_date(date_str):
    """统一日期格式"""
    try:
        for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S']:
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
            except:
                continue
        return datetime.now().strftime('%Y-%m-%d')
    except:
        return datetime.now().strftime('%Y-%m-%d')


def filter_and_classify(items):
    """过滤和分类"""
    results = []
    for item in items:
        text = item['title'] + ' ' + item.get('summary', '')
        if not any(kw.lower() in text.lower() for kw in FILTER_KEYWORDS):
            continue
        
        matched_kw = [kw for kw in FILTER_KEYWORDS if kw.lower() in text.lower()]
        
        if any(kw in text for kw in KEY_NEWS_KEYWORDS):
            category = 'key_news'
        elif any(kw in text for kw in FUNDING_KEYWORDS):
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
    print(f"\n{'='*50}")
    print(f"AI资讯抓取开始 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")
    
    all_items = []
    
    # 1. 投资界 RSS
    all_items.extend(fetch_investment_news("投资界"))
    
    # 2. 36氪搜索API
    all_items.extend(fetch_36kr_api("36氪"))
    
    # 3. 如果有其他可用RSS源，在这里添加
    # 你可以让ChatGPT帮你添加更多源
    
    # 过滤和分类
    filtered = filter_and_classify(all_items)
    
    # 去重（按链接）
    seen = set()
    unique = []
    for item in filtered:
        if item['link'] not in seen:
            seen.add(item['link'])
            unique.append(item)
    
    # 按日期倒序
    unique.sort(key=lambda x: x['date'], reverse=True)
    
    # 保存
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'news.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}")
    print(f"总计抓取到 {len(unique)} 条AI相关资讯")
    print(f"已保存至 {output_path}")
    print(f"{'='*50}\n")

if __name__ == '__main__':
    main()
