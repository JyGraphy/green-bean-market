"""database.sql → data/products.json 변환 스크립트 (최초 1회 실행)"""
import re, json, sys, os

SQL_FILE = os.path.join(os.path.dirname(__file__), '..', 'database.sql')
OUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'products.json')

with open(SQL_FILE, encoding='utf-8') as f:
    sql = f.read()

pattern = re.compile(
    r"\((\d+),'([^']+)','((?:[^'\\]|\\.)*)',(\d+),'([^']+)','([^']+)','([^']+)','((?:[^'\\]|\\.)*)','([^']+)',(\d+),(\d+),(\d+)\)"
)

products = []
for m in pattern.finditer(sql):
    products.append({
        "id":         int(m.group(1)),
        "store":      m.group(2),
        "name":       m.group(3).replace("\\'", "'"),
        "price":      int(m.group(4)),
        "origin":     m.group(5),
        "region":     m.group(6),
        "process":    m.group(7),
        "notes":      m.group(8).replace("\\'", "'"),
        "url":        m.group(9),
        "is_new":     bool(int(m.group(10))),
        "is_decaf":   bool(int(m.group(11))),
        "is_special": bool(int(m.group(12))),
    })

os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
with open(OUT_FILE, 'w', encoding='utf-8') as f:
    json.dump({"products": products}, f, ensure_ascii=False, indent=2)

print(f"✅ {len(products)}개 상품 → {OUT_FILE}")
