"""
data/products.json → database.sql 변환 스크립트
GitHub Actions에서 스크래핑 후 자동 실행됨
"""
import json, os
from datetime import datetime, timezone

ROOT       = os.path.join(os.path.dirname(__file__), '..')
JSON_FILE  = os.path.join(ROOT, 'data', 'products.json')
SQL_FILE   = os.path.join(ROOT, 'database.sql')
DATES_FILE = os.path.join(ROOT, 'data', 'product_dates.json')
LOG_FILE   = os.path.join(ROOT, 'data', 'update_log.json')

with open(JSON_FILE, encoding='utf-8') as f:
    data = json.load(f)

products = data['products']
updated_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

# --- 상품 등록일 추적 ---
if os.path.exists(DATES_FILE):
    with open(DATES_FILE, encoding='utf-8') as f:
        product_dates = json.load(f)
    is_init = not product_dates  # 빈 dict이면 초기화 상태
else:
    product_dates = {}
    is_init = True

new_by_store = {}
for p in products:
    pid = str(p['id'])
    if pid not in product_dates:
        if is_init:
            product_dates[pid] = None  # 초기화 시: 기존 상품은 날짜 없음
        else:
            product_dates[pid] = today  # 이후: 신규 상품은 오늘 날짜
            store = p['store']
            new_by_store[store] = new_by_store.get(store, 0) + 1

# product_dates.json 저장 (영구 보관용)
with open(DATES_FILE, 'w', encoding='utf-8') as f:
    json.dump(product_dates, f, ensure_ascii=False)

# update_log.json 저장 (웹사이트 알림용)
update_log = {
    "updated_at": updated_at,
    "stores": [{"name": k, "new_count": v} for k, v in sorted(new_by_store.items())],
    "total_new": sum(new_by_store.values())
}
with open(LOG_FILE, 'w', encoding='utf-8') as f:
    json.dump(update_log, f, ensure_ascii=False, indent=2)

# --- SQL 생성 ---
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
    '  isSoldout INTEGER DEFAULT 0,',
    '  added_date TEXT DEFAULT NULL',
    ');',
    'DELETE FROM products;',
    'INSERT INTO products (id,store,name,price,origin,region,process,notes,url,isNew,isDecaf,isSpecial,isSoldout,added_date) VALUES',
]

def esc(s):
    return str(s).replace("'", "''")

rows = []
for p in products:
    added = product_dates.get(str(p['id']))
    added_sql = f"'{added}'" if added else 'NULL'
    rows.append(
        f"  ({p['id']},'{esc(p['store'])}','{esc(p['name'])}',"
        f"{p['price']},'{esc(p['origin'])}','{esc(p['region'])}',"
        f"'{esc(p['process'])}','{esc(p['notes'])}','{esc(p['url'])}',"
        f"{1 if p.get('is_new') else 0},"
        f"{1 if p.get('is_decaf') else 0},"
        f"{1 if p.get('is_special') else 0},"
        f"{1 if p.get('is_soldout') else 0},"
        f"{added_sql})"
    )

lines.append(',\n'.join(rows) + ';')

with open(SQL_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')

soldout_count = sum(1 for p in products if p.get('is_soldout'))
new_count = sum(new_by_store.values())
if is_init:
    print(f"✅ {len(products)}개 상품 → database.sql 초기화 완료 (품절 {soldout_count}개, {updated_at})")
else:
    print(f"✅ {len(products)}개 상품 → database.sql 재생성 완료 (품절 {soldout_count}개, 신규 {new_count}개, {updated_at})")
