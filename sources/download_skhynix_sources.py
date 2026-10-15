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

out_dir = r'c:\Users\BISTelligence\ontology-wiki\sources\skhynix'
os.makedirs(out_dir, exist_ok=True)

target_articles = [
    # 1. Front-end process series by Jeong In-seong (6 parts)
    {'id': 'skhynix_frontend_02_oxidation', 'title': '[반도체 전공정 2편] 반도체 공정 개괄과 산화', 'url': 'https://news.skhynix.co.kr/jeonginseong-column-oxidation/'},
    {'id': 'skhynix_frontend_03_photo', 'title': '[반도체 전공정 3편] 반도체 패턴을 만드는 포토 공정', 'url': 'https://news.skhynix.co.kr/jeonginseong-column-photo/'},
    {'id': 'skhynix_frontend_04_etch', 'title': '[반도체 전공정 4편] 그려진 패턴을 파내는 ‘식각 공정’', 'url': 'https://news.skhynix.co.kr/jeonginseong-column-etch/'},
    {'id': 'skhynix_frontend_05_deposition', 'title': '[반도체 전공정 5편] 미세화를 위한 핵심 ‘증착 공정’', 'url': 'https://news.skhynix.co.kr/jeonginseong-column-deposition/'},
    {'id': 'skhynix_frontend_06_metal', 'title': '[반도체 전공정 6편] 반도체에 생명을 불어넣는 연결, ‘금속배선’', 'url': 'https://news.skhynix.co.kr/jeonginseong-column-metal/'},
    
    # 2. AI and Semiconductor Series (7 parts)
    {'id': 'skhynix_ai_01_gpu', 'title': '[인공지능과 반도체 1편] 프로그래밍과 인공지능, GPU의 등장', 'url': 'https://news.skhynix.co.kr/jeonginseong-column-ai-1/'},
    {'id': 'skhynix_ai_02_hbm', 'title': '[인공지능과 반도체 2편] 연산을 높여준 최고 성능 D램 HBM', 'url': 'https://news.skhynix.co.kr/jeonginseong-column-ai-2/'},
    {'id': 'skhynix_ai_03_nand_ssd', 'title': '[인공지능과 반도체 3편] 고속 저장소 낸드플래시와 SSD', 'url': 'https://news.skhynix.co.kr/jeonginseong-column-ai-3/'},
    {'id': 'skhynix_ai_04_cxl', 'title': '[인공지능과 반도체 4편] 메모리 공유를 통한 성능향상 CXL', 'url': 'https://news.skhynix.co.kr/jeonginseong-column-ai-4/'},
    {'id': 'skhynix_ai_05_pim_pnm', 'title': '[인공지능과 반도체 5편] 차세대 지능형 메모리 PIM과 PNM', 'url': 'https://news.skhynix.co.kr/jeonginseong-column-ai-5/'},
    {'id': 'skhynix_ai_06_neuromorphic', 'title': '[인공지능과 반도체 6편] 뇌 구조의 반도체 뉴로모픽', 'url': 'https://news.skhynix.co.kr/jeonginseong-column-ai-6/'},
    {'id': 'skhynix_ai_07_summary', 'title': '[인공지능과 반도체 7편] AI 시대 메모리 반도체의 위상', 'url': 'https://news.skhynix.co.kr/jeonginseong-column-ai-7/'},

    # 3. Packaging & Advanced HBM & Tech Notes
    {'id': 'skhynix_pkg_01_chiplet', 'title': '[패키징X파일 1편] 반도체 산업의 새로운 챕터, 칩렛', 'url': 'https://news.skhynix.co.kr/packaging-x-files-ep1/'},
    {'id': 'skhynix_pkg_02_3d_heterogeneous', 'title': '[패키징X파일 2편] 3D 이종집적기술', 'url': 'https://news.skhynix.co.kr/packaging-x-files-ep2/'},
    {'id': 'skhynix_tech_hybrid_bonding', 'title': '[Tech Note] 성능 향상을 위한 기본 기술, 하이브리드 본딩', 'url': 'https://news.skhynix.co.kr/tech-note-series-ep2/'},
    {'id': 'skhynix_tech_tsv_mr_muf', 'title': '[미래인재 CLASS] HBM의 진화: TSV와 MR-MUF', 'url': 'https://news.skhynix.co.kr/future-talents-class-ep1/'},
    {'id': 'skhynix_hypidia_tsv', 'title': '[하이피디아] HBM 핵심 패키지 기술 초고속 엘리베이터 TSV', 'url': 'https://news.skhynix.co.kr/ambassador-hypidia-2/'},
    {'id': 'skhynix_hypidia_tat', 'title': '[하이피디아] 팹 양산관리 핵심 지표 TAT (Turn Around Time)', 'url': 'https://news.skhynix.co.kr/ambassador-hypidia-4/'},
    {'id': 'skhynix_hypidia_reliability', 'title': '[하이피디아] 반도체 신뢰성 평가 및 품질', 'url': 'https://news.skhynix.co.kr/ambassador-hypidia-5/'},
    {'id': 'skhynix_research_cti_nand', 'title': '[Research Inside] 고성능 초고층 3D 낸드 CTI 혁신 기술', 'url': 'https://news.skhynix.co.kr/research-inside-ep1/'},
    {'id': 'skhynix_research_computational_nand', 'title': '[Research Inside] 저장하던 낸드가 연산을 시작했다', 'url': 'https://news.skhynix.co.kr/research-inside-ep2/'}
]

def clean_html_to_markdown(raw_html):
    # SK hynix newsroom post body usually in article or .post-content or .entry-content
    match = re.search(r'<div class="post-content[^"]*">(.*?)</div>\s*<!--', raw_html, re.DOTALL)
    if not match:
        match = re.search(r'<article[^>]*>(.*?)</article>', raw_html, re.DOTALL)
    body = match.group(1) if match else raw_html

    body = re.sub(r'<h[1-4][^>]*>(.*?)</h[1-4]>', r'\n### \1\n', body, flags=re.DOTALL)
    body = re.sub(r'<br\s*/?>', '\n', body)
    body = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', body, flags=re.DOTALL)
    body = re.sub(r'<li[^>]*>(.*?)</li>', r'\n- \1', body, flags=re.DOTALL)
    body = re.sub(r'<(?:strong|b)>(.*?)</(?:strong|b)>', r'**\1**', body, flags=re.DOTALL)
    body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
    body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
    body = re.sub(r'<[^>]+>', '', body)
    body = html.unescape(body)

    lines = [line.strip() for line in body.split('\n')]
    cleaned = []
    prev_empty = False
    for line in lines:
        if not line:
            if not prev_empty:
                cleaned.append('')
                prev_empty = True
        else:
            cleaned.append(line)
            prev_empty = False
    return '\n'.join(cleaned).strip()

print(f"Starting download of {len(target_articles)} official SK hynix Newsroom articles...")

for i, item in enumerate(target_articles, 1):
    file_path = os.path.join(out_dir, f"{item['id']}.md")
    print(f"[{i:2d}/{len(target_articles)}] Downloading: {item['title']}...")
    try:
        encoded_url = urllib.parse.quote(item['url'], safe=':/?&=#')
        req = urllib.request.Request(encoded_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            raw_html = resp.read().decode('utf-8', errors='ignore')
        
        md_content = clean_html_to_markdown(raw_html)
        header = f"""---
title: "{item['title']}"
source_url: "{item['url']}"
publisher: "SK hynix Newsroom"
source_id: "{item['id']}"
type: "official_technical_column"
---

# {item['title']}

"""
        full_doc = header + md_content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_doc)
        print(f"  -> Saved {len(full_doc):,} chars to {os.path.basename(file_path)}")
    except Exception as e:
        print(f"  -> ERROR: {e}")

print("All SK hynix downloads finished!")
