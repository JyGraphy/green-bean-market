"""
data/products.json → data.js 변환 스크립트
GitHub Actions에서 스크래핑 후 자동 실행됨
"""
import json, os, re
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(__file__), '..')
JSON_FILE = os.path.join(ROOT, 'data', 'products.json')
DATA_JS   = os.path.join(ROOT, 'data.js')

# 기존 data.js에서 STORE_CLS, FLAG, extractProcess 블록 유지
with open(DATA_JS, encoding='utf-8') as f:
    original = f.read()

# PRODUCTS 배열 이전 부분(헤더) 추출
header_match = re.search(r'^(.*?const PRODUCTS\s*=\s*\[)', original, re.DOTALL)
footer_match = re.search(r'\];?\s*$', original, re.DOTALL)

if not header_match:
    print("❌ data.js에서 PRODUCTS 블록을 찾을 수 없습니다")
    exit(1)

header = header_match.group(1)

with open(JSON_FILE, encoding='utf-8') as f:
    data = json.load(f)

products = data['products']

def js_str(s):
    return s.replace('\\', '\\\\').replace("'", "\\'")

lines = []
for p in products:
    lines.append(
        f"  {{id:{p['id']},store:'{js_str(p['store'])}',name:'{js_str(p['name'])}',"
        f"price:{p['price']},origin:'{js_str(p['origin'])}',region:'{js_str(p['region'])}',"
        f"process:'{js_str(p['process'])}',notes:'{js_str(p['notes'])}',url:'{js_str(p['url'])}',"
        f"isNew:{'true' if p['is_new'] else 'false'},"
        f"isDecaf:{'true' if p['is_decaf'] else 'false'},"
        f"isSpecial:{'true' if p['is_special'] else 'false'}}}"
    )

product_block = ',\n'.join(lines)
updated_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

new_content = header + '\n' + product_block + '\n];\n'

# 마지막에 업데이트 시각 주석 추가
footer_content = original[original.find('];') + 2:]  # ]; 이후 내용 유지
new_content = header + '\n' + product_block + '\n];' + footer_content

# updated_at 주석 삽입 (파일 상단)
new_content = f'// 자동 생성: {updated_at}\n' + new_content

with open(DATA_JS, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ {len(products)}개 상품 → data.js 재생성 완료 ({updated_at})")
