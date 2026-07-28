import requests
import json
import os
import re
import time
from datetime import datetime
import xml.etree.ElementTree as ET

# ============ 分类关键词 ============
KEY_NEWS_KEYWORDS = ['招股书', '上市', '备案', '批文', '港交所', '科创板', '纳斯达克', 'IPO', '过会', '提交申请', '挂牌']
FUNDING_KEYWORDS = ['融资', '估值', 'Pre-A', 'A轮', 'B轮', 'C轮', 'D轮', '天使轮', '种子轮', '战略投资', '亿元', '千万级', '百万级']
FILTER_KEYWORDS = [
    '大模型', 'AI agent', 'AI Agent', '人工智能', 'OpenAI', 'Anthropic', 'Google DeepMind',
    '微软AI', 'Meta AI', '智谱', '月之暗面', '百川', 'MiniMax', '零一万物', '深度求索',
    'DeepSeek', '科大讯飞', '商汤', '第四范式', '字节AI', '腾讯AI', '百度AI', '阿里AI',
    'Agent', 'LLM', 'GPT', 'Claude', 'Gemini', '文心一言', '通义千问', '混元',
    '数字营销', 'MarTech', 'AIGC', '生成式', 'Copilot', 'Sora', 'Kimi', '豆包'
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/json,application/xml,*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


def clean_html(text):
    if not text:
        return ''
    return re.sub(r'<.*?>', '', text)


def format_date(date_str):
    if not date_str:
        return datetime.now().strftime('%Y-%m-%d')
    try:
        for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S']:
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
            except:
                continue
        return datetime.now().strftime('%Y-%m-%d')
    except:
        return datetime.now().strftime('%Y-%m-%d')


def fetch_36kr_web():
    """36氪 - 通过网页接口"""
    items = []
    try:
        url = "https://www.36kr.com/api/search/article?q=AI&per_page=20&page=1"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        print(f"[36氪-搜索] HTTP状态: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            articles = data.get('data', {}).get('items', [])
            for a in articles[:15]:
                title = a.get('title', '') or a.get('widget_title', '')
                aid = a.get('id', '')
                summary = a.get('summary', '') or a.get('widget_content', '')
                pub_time = a.get('published_at', '')[:10]
                if title and aid:
                    items.append({
                        'title': title.strip(),
                        'link': f'https://www.36kr.com/p/{aid}',
                        'source': '36氪',
                        'summary': clean_html(summary)[:200],
                        'date': pub_time or datetime.now().strftime('%Y-%m-%d')
                    })
            print(f"[36氪-搜索] 获取到 {len(items)} 条")
        else:
            print(f"[36氪-搜索] 返回内容: {resp.text[:200]}")
    except Exception as e:
        print(f"[36氪-搜索] 异常: {type(e).__name__}: {str(e)}")
    return items


def fetch_cls_ai():
    """财联社AI板块"""
    items = []
    try:
        url = "https://www.cls.cn/api/sw?app=CailianpressWeb&os=web&sv=8.4.6&sign=1&keyword=AI&type=telegram"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        print(f"[财联社] HTTP状态: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            articles = data.get('data', {}).get('telegram', {}).get('data', [])
            for a in articles[:15]:
                title = a.get('title', '') or a.get('brief', '')
                aid = a.get('id', '')
                summary = a.get('brief', '')
                pub_time = datetime.fromtimestamp(a.get('ctime', time.time())).strftime('%Y-%m-%d')
                if title and aid:
                    items.append({
                        'title': title.strip(),
                        'link': f'https://www.cls.cn/detail/{aid}',
                        'source': '财联社',
                        'summary': clean_html(summary)[:200],
                        'date': pub_time
                    })
            print(f"[财联社] 获取到 {len(items)} 条")
    except Exception as e:
        print(f"[财联社] 异常: {type(e).__name__}: {str(e)}")
    return items


def fetch_tmtpost():
    """钛媒体"""
    items = []
    try:
        url = "https://www.tmtpost.com/api/get-data?type=index_recommend"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        print(f"[钛媒体] HTTP状态: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            articles = data.get('data', [])[:15]
            for a in articles:
                title = a.get('title', '')
                aid = a.get('id', '')
                summary = a.get('summary', '')
                pub_time = a.get('time', '')[:10]
                if title and aid:
                    items.append({
                        'title': title.strip(),
                        'link': f'https://www.tmtpost.com/{aid}.html',
                        'source': '钛媒体',
                        'summary': clean_html(summary)[:200],
                        'date': pub_time or datetime.now().strftime('%Y-%m-%d')
                    })
            print(f"[钛媒体] 获取到 {len(items)} 条")
    except Exception as e:
        print(f"[钛媒体] 异常: {type(e).__name__}: {str(e)}")
    return items


def fetch_jiemian():
    """界面新闻科技频道"""
    items = []
    try:
        url = "https://www.jiemian.com/lists/4_1.html"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        print(f"[界面新闻] HTTP状态: {resp.status_code}")
        
        if resp.status_code == 200:
            # 简单正则提取
            pattern = r'<a[^>]*href="(/article/\d+\.html)"[^>]*title="([^"]*)"[^>]*>'
            matches = re.findall(pattern, resp.text)
            for href, title in matches[:15]:
                if title.strip():
                    items.append({
                        'title': title.strip(),
                        'link': f'https://www.jiemian.com{href}',
                        'source': '界面新闻',
                        'summary': '',
                        'date': datetime.now().strftime('%Y-%m-%d')
                    })
            print(f"[界面新闻] 获取到 {len(items)} 条")
    except Exception as e:
        print(f"[界面新闻] 异常: {type(e).__name__}: {str(e)}")
    return items


def fetch_pedaily():
    """投资界 RSS"""
    items = []
    try:
        url = "https://www.pedaily.cn/rss/news.xml"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        print(f"[投资界RSS] HTTP状态: {resp.status_code}")
        
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item_elem in root.iter('item'):
                title = item_elem.find('title')
                link = item_elem.find('link')
                desc = item_elem.find('description')
                pub_date = item_elem.find('pubDate')
                
                title_text = title.text.strip() if title is not None and title.text else ''
                link_text = link.text.strip() if link is not None and link.text else ''
                desc_text = desc.text.strip() if desc is not None and desc.text else ''
                date_text = pub_date.text.strip() if pub_date is not None and pub_date.text else ''
                
                if title_text and link_text:
                    items.append({
                        'title': title_text,
                        'link': link_text,
                        'source': '投资界',
                        'summary': clean_html(desc_text)[:200],
                        'date': format_date(date_text)
                    })
            print(f"[投资界RSS] 获取到 {len(items)} 条")
    except Exception as e:
        print(f"[投资界RSS] 异常: {type(e).__name__}: {str(e)}")
    return items


def filter_and_classify(items):
    results = []
    for item in items:
        text = item['title'] + ' ' + item.get('summary', '')
        
        # 必须包含AI相关关键词
        if not any(kw.lower() in text.lower() for kw in FILTER_KEYWORDS):
            continue
        
        matched_kw = [kw for kw in FILTER_KEYWORDS if kw.lower() in text.lower()]
        
        # 分类
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
    print(f"\n{'='*60}")
    print(f"AI资讯抓取开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    all_items = []
    
    # 依次抓取各个源
    print(">>> 开始抓取 36氪...")
    all_items.extend(fetch_36kr_web())
    
    print("\n>>> 开始抓取 财联社...")
    all_items.extend(fetch_cls_ai())
    
    print("\n>>> 开始抓取 钛媒体...")
    all_items.extend(fetch_tmtpost())
    
    print("\n>>> 开始抓取 界面新闻...")
    all_items.extend(fetch_jiemian())
    
    print("\n>>> 开始抓取 投资界 RSS...")
    all_items.extend(fetch_pedaily())
    
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
    
    # 分类统计
    key_news = sum(1 for i in unique if i['category'] == 'key_news')
    funding = sum(1 for i in unique if i['category'] == 'funding')
    other = sum(1 for i in unique if i['category'] == 'other')
    print(f"分类: 重点资讯={key_news}, 投融资={funding}, 其他={other}")
    
    # 保存
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'news.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已保存至 {output_path}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
