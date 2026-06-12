"""
data/products.json → database.sql 변환 스크립트
GitHub Actions에서 스크래핑 후 자동 실행됨
"""
import json, os
from datetime import datetime, timezone

ROOT      = os.path.join(os.path.dirname(__file__), '..')
JSON_FILE = os.path.join(ROOT, 'data', 'products.json')
SQL_FILE  = os.path.join(ROOT, 'database.sql')

with open(JSON_FILE, encoding='utf-8') as f:
    data = json.load(f)

products = data['products']

def sql_str(s):
    return str(s).replace("'", "''")

lines = []
for p in products:
    lines.append(
        "  ({},{},{},{},{},{},{},{},{},{},{},{},{})".format(
            p['id'],
            "'" + sql_str(p['store']) + "'",
            "'" + sql_str(p['name']) + "'",
            p['price'],
            "'" + sql_str(p['origin']) + "'",
            "'" + sql_str(p['region']) + "'",
            "'" + sql_str(p['process']) + "'",
            "'" + sql_str(p['notes']) + "'",
            "'" + sql_str(p['url']) + "'",
            1 if p['is_new'] else 0,
            1 if p['is_decaf'] else 0,
            1 if p['is_special'] else 0,
            1 if p.get('is_soldout') else 0,
        )
    )

updated_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
values_block = ',\n'.join(lines)

header = (
    "-- 자동 생성: " + updated_at + "\n"
    "CREATE TABLE IF NOT EXISTS products (\n"
    "  id INTEGER PRIMARY KEY,\n"
    "  store TEXT NOT NULL,\n"
    "  name TEXT NOT NULL,\n"
    "  price INTEGER NOT NULL,\n"
    "  origin TEXT NOT NULL,\n"
    "  region TEXT NOT NULL,\n"
    "  process TEXT NOT NULL,\n"
    "  notes TEXT DEFAULT '',\n"
    "  url TEXT NOT NULL,\n"
    "  isNew INTEGER DEFAULT 0,\n"
    "  isDecaf INTEGER DEFAULT 0,\n"
    "  isSpecial INTEGER DEFAULT 0,\n"
    "  isSoldout INTEGER DEFAULT 0\n"
    ");\n\n"
    "INSERT INTO products (id,store,name,price,origin,region,process,notes,url,isNew,isDecaf,isSpecial,isSoldout) VALUES\n"
)

with open(SQL_FILE, 'w', encoding='utf-8') as f:
    f.write(header + values_block + ";\n")

print("✅ {}개 상품 → database.sql 재생성 완료 ({})".format(len(products), updated_at))
