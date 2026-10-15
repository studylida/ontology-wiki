import urllib.request
import urllib.parse
import re
import os
import ssl
import sys
import html

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

out_dir = r'c:\Users\BISTelligence\ontology-wiki\sources\samsung'
os.makedirs(out_dir, exist_ok=True)

# List of target articles to download
target_articles = [
    # 8 Essential Processes Series (2017-2018 definitive edition)
    {
        'id': 'samsung_fab_00_overview',
        'title': '반도체 8대 공정 한 눈에 보기',
        'url': 'https://news.samsungsemiconductor.com/kr/반도체-백과사전-반도체-8대-공정-한-눈에-보기/'
    },
    {
        'id': 'samsung_fab_01_wafer',
        'title': '[반도체 8대 공정] 1탄, ‘웨이퍼’란 무엇일까요?',
        'url': 'https://news.samsungsemiconductor.com/kr/반도체-8대-공정-1탄-웨이퍼란-무엇일까요/'
    },
    {
        'id': 'samsung_fab_02_oxidation',
        'title': '[반도체 8대 공정] 2탄, 웨이퍼 표면을 보호하는 산화공정',
        'url': 'https://news.samsungsemiconductor.com/kr/반도체-8대-공정-2탄-웨이퍼-표면을-보호하는-산화공/'
    },
    {
        'id': 'samsung_fab_03_ic',
        'title': '[반도체 8대 공정] 3탄, 전자산업의 혁명! 집적회로',
        'url': 'https://news.samsungsemiconductor.com/kr/반도체-8대-공정-3탄-전자산업의-혁명-집적회로/'
    },
    {
        'id': 'samsung_fab_04_photolithography',
        'title': '[반도체 8대 공정] 4탄, 웨이퍼에 회로를 그려 넣는 포토공정',
        'url': 'https://news.samsungsemiconductor.com/kr/반도체-8대-공정-4탄-웨이퍼에-회로를-그려-넣는-포토/'
    },
    {
        'id': 'samsung_fab_05_etch',
        'title': '[반도체 8대 공정] 5탄, 반도체 회로패턴의 완성 ‘식각 공정’',
        'url': 'https://news.samsungsemiconductor.com/kr/반도체-8대-공정-5탄-반도체-회로패턴의-완성-식각-공/'
    },
    {
        'id': 'samsung_fab_06_deposition_ion',
        'title': '[반도체 8대 공정] 6탄, 반도체에 전기적 특성을 입히다! 증착&이온주입 공정',
        'url': 'https://news.samsungsemiconductor.com/kr/반도체-8대-공정-6탄-반도체에-전기적-특성을-입히다/'
    },
    {
        'id': 'samsung_fab_07_metal_interconnect',
        'title': '[반도체 8대 공정] 7탄, 전기가 통하는 길을 만드는 ‘금속 배선 공정’',
        'url': 'https://news.samsungsemiconductor.com/kr/반도체-8대-공정-7탄-전기가-통하는-길을-만드는-금/'
    },
    {
        'id': 'samsung_fab_08_eds',
        'title': '[반도체 8대 공정] 8탄, 완벽한 반도체로 태어나기 위한 첫 번째 테스트 ‘EDS공정’',
        'url': 'https://news.samsungsemiconductor.com/kr/반도체-8대-공정-8탄-완벽한-반도체로-태어나기-위한/'
    },
    {
        'id': 'samsung_fab_09_packaging',
        'title': '[반도체 8대 공정] 9탄, 외부환경으로부터 반도체를 보호하는 패키징 (Packaging) 공정',
        'url': 'https://news.samsungsemiconductor.com/kr/반도체-8대-공정-9탄-외부환경으로부터-반도체를-보호/'
    },
    # Key Glossary Articles
    {
        'id': 'samsung_glossary_bandochat_summary',
        'title': '[반도Chat 모아보기] 어려운 반도체 용어 완전 정복! 요약 모음.Zip',
        'url': 'https://news.samsungsemiconductor.com/kr/반도chat-모아보기-어려운-반도체-용어-완전-정복-요약/'
    },
    {
        'id': 'samsung_glossary_dram_a_to_z',
        'title': '[반도체 백과사전 Ep.8] 삼성전자 반도체와 완벽 정리하는 D램의 A to Z',
        'url': 'https://news.samsungsemiconductor.com/kr/반도체-백과사전-ep-8-삼성전자-반도체와-완벽-정리하/'
    },
    {
        'id': 'samsung_glossary_memory_a_to_z',
        'title': '[반도체 백과사전 Ep.7] 메모리 반도체의 A to Z 파헤치기!',
        'url': 'https://news.samsungsemiconductor.com/kr/반도체-백과사전-ep-7-세계-시장에서-대한민국이-압도/'
    },
    {
        'id': 'samsung_glossary_system_lsi',
        'title': '[반도체 백과사전 Ep.10] 시스템 반도체의 다양한 역할과 종류',
        'url': 'https://news.samsungsemiconductor.com/kr/반도체-백과사전-ep-10-전자기기의-두뇌-역할부터-인간/'
    },
    {
        'id': 'samsung_glossary_terms_ep3',
        'title': '[반도체 백과사전 Ep.3] 반도체 뉴스에 관심이 있다면 꼭 알아야 할 반도체 용어 모음 1편',
        'url': 'https://news.samsungsemiconductor.com/kr/반도체-백과사전-ep-3-반도체-뉴스에-관심이-있다면-꼭/'
    },
    {
        'id': 'samsung_glossary_terms_ep4',
        'title': '[반도체 백과사전 Ep.4] 전자기기의 뇌와 눈이 되는 반도체 전문 용어 모음 2편',
        'url': 'https://news.samsungsemiconductor.com/kr/반도체-백과사전-ep-4-전자기기의-뇌와-눈이-되는-반도/'
    }
]

def clean_html_to_markdown(raw_html):
    # Extract entry content if present
    content_match = re.search(r'<div class="entry-content[^"]*">(.*?)</div>\s*<!-- \.entry-content -->', raw_html, re.DOTALL)
    if not content_match:
        content_match = re.search(r'<div class="entry-content[^"]*">(.*?)</article>', raw_html, re.DOTALL)
    
    body = content_match.group(1) if content_match else raw_html

    # Replace headings
    body = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', body, flags=re.DOTALL)
    body = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', body, flags=re.DOTALL)
    body = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', body, flags=re.DOTALL)
    body = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n#### \1\n', body, flags=re.DOTALL)

    # Paragraphs and linebreaks
    body = re.sub(r'<br\s*/?>', '\n', body)
    body = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', body, flags=re.DOTALL)
    body = re.sub(r'<li[^>]*>(.*?)</li>', r'\n- \1', body, flags=re.DOTALL)

    # Bold and strong
    body = re.sub(r'<(?:strong|b)>(.*?)</(?:strong|b)>', r'**\1**', body, flags=re.DOTALL)

    # Strip remaining html tags
    body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
    body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
    body = re.sub(r'<[^>]+>', '', body)

    # Unescape html entities
    body = html.unescape(body)

    # Clean empty lines
    lines = [line.strip() for line in body.split('\n')]
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        if not line:
            if not prev_empty:
                cleaned_lines.append('')
                prev_empty = True
        else:
            cleaned_lines.append(line)
            prev_empty = False

    return '\n'.join(cleaned_lines).strip()

print(f'Starting download of {len(target_articles)} official Samsung Semiconductor articles...')

for i, item in enumerate(target_articles, 1):
    file_path = os.path.join(out_dir, f"{item['id']}.md")
    print(f"[{i}/{len(target_articles)}] Downloading: {item['title']}...")
    try:
        encoded_url = urllib.parse.quote(item['url'], safe=':/?&=#')
        req = urllib.request.Request(encoded_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            raw_html = resp.read().decode('utf-8', errors='ignore')
        
        md_content = clean_html_to_markdown(raw_html)
        
        # Prepend metadata header
        header = f"""---
title: "{item['title']}"
source_url: "{item['url']}"
publisher: "Samsung Semiconductor"
source_id: "{item['id']}"
type: "official_educational_series"
---

# {item['title']}

"""
        full_doc = header + md_content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_doc)
        print(f"  -> Saved {len(full_doc):,} chars to {os.path.basename(file_path)}")
    except Exception as e:
        print(f"  -> ERROR: {e}")

print('All downloads finished!')
