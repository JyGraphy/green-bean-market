"""
data/products.json → database.sql 변환 스크립트
GitHub Actions에서 스크래핑 후 자동 실행됨
"""
import json, os
from datetime import datetime, timezone

ROOT     = os.path.join(os.path.dirname(__file__), '..')
JSON_FILE = os.path.join(ROOT, 'data', 'products.json')
SQL_FILE  = os.path.join(ROOT, 'database.sql')

with open(JSON_FILE, encoding='utf-8') as f:
    data = json.load(f)

products = data['products']
updated_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

lines = [
    f'-- 자동 생성: {updated_at}',
    'CREATE TABLE IF NOT EXISTS products (',
    '  id INTEGER PRIMARY KEY,',
    '  store TEXT NOT NULL,',
    '  name TEXT NOT NULL,',
    '  price INTEGER NOT NULL,',
    '  origin TEXT,',
    '  region TEXT,',
    '  process TEXT,',
    '  notes TEXT,',
    '  url TEXT,',
    '  isNew INTEGER DEFAULT 0,',
    '  isDecaf INTEGER DEFAULT 0,',
    '  isSpecial INTEGER DEFAULT 0,',
    '  isSoldout INTEGER DEFAULT 0',
    ');',
    'DELETE FROM products;',
    'INSERT INTO products (id,store,name,price,origin,region,process,notes,url,isNew,isDecaf,isSpecial,isSoldout) VALUES',
]

def esc(s):
    return str(s).replace("'", "''")

rows = []
for p in products:
    rows.append(
        f"  ({p['id']},'{esc(p['store'])}','{esc(p['name'])}',"
        f"{p['price']},'{esc(p['origin'])}','{esc(p['region'])}',"
        f"'{esc(p['process'])}','{esc(p['notes'])}','{esc(p['url'])}',"
        f"{1 if p.get('is_new') else 0},"
        f"{1 if p.get('is_decaf') else 0},"
        f"{1 if p.get('is_special') else 0},"
        f"{1 if p.get('is_soldout') else 0})"
    )

lines.append(',\n'.join(rows) + ';')

with open(SQL_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')

soldout_count = sum(1 for p in products if p.get('is_soldout'))
print(f"✅ {len(products)}개 상품 → database.sql 재생성 완료 (품절 {soldout_count}개, {updated_at})")
