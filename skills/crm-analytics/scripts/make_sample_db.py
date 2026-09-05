#!/usr/bin/env python3
"""
make_sample_db.py — 生成用于自测/演示的样例 CRM SQLite 数据库。

产出 crm_sample.db，含：
  customers(id, name, signup_date, last_active_date, region)
  orders(id, customer_id, order_date, amount, product, stage)
  events(user_id, event, event_date)        # 用于 AARRR / AIPL
  nps_responses(user_id, score)             # 用于 NPS

用法:
  python make_sample_db.py [输出路径，默认 ./crm_sample.db]   # 生成 SQLite 样例库
  python make_sample_db.py --csv [输出目录，默认 .]          # 生成 CSV 样例文件
        （orders.csv / customers.csv / events.csv / nps.csv，供无数据库场景试玩）
"""
import csv
import os
import sqlite3
import sys
import random
from datetime import datetime, timedelta

random.seed(42)

CSV_MODE = len(sys.argv) > 1 and sys.argv[1] == "--csv"
OUT = (sys.argv[2] if len(sys.argv) > 2 else "./") if CSV_MODE else (
    sys.argv[1] if len(sys.argv) > 1 else "crm_sample.db")

PRODUCTS = ["手机", "耳机", "充电宝", "保护壳", "平板", "手表", "音箱", "键盘"]
REGIONS = ["华东", "华南", "华北", "西南", "东北"]

if not CSV_MODE:
    conn = sqlite3.connect(OUT)
    cur = conn.cursor()
    cur.executescript("""
DROP TABLE IF EXISTS customers; DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS events; DROP TABLE IF EXISTS nps_responses;
CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT, signup_date TEXT,
  last_active_date TEXT, region TEXT);
CREATE TABLE orders(id INTEGER PRIMARY KEY, customer_id INTEGER, order_date TEXT,
  amount REAL, product TEXT, stage TEXT);
CREATE TABLE events(user_id INTEGER, event TEXT, event_date TEXT);
CREATE TABLE nps_responses(user_id INTEGER, score INTEGER);
""")

N = 600
now = datetime(2026, 8, 15)
customers = []
orders = []
events = []
nps = []

for cid in range(1, N + 1):
    signup = now - timedelta(days=random.randint(30, 720))
    # 让客户活跃度有差异：30% 高价值高活跃，其余长尾
    tier = random.random()
    if tier < 0.3:
        n_orders = random.randint(8, 25)
        recency = random.randint(1, 40)          # 近期活跃
        avg_amt = random.uniform(800, 3000)
    elif tier < 0.7:
        n_orders = random.randint(3, 8)
        recency = random.randint(20, 120)
        avg_amt = random.uniform(300, 1200)
    else:
        n_orders = random.randint(1, 3)
        recency = random.randint(90, 400)        # 多数已静默（制造流失）
        avg_amt = random.uniform(100, 600)
    last_active = now - timedelta(days=recency)
    region = random.choice(REGIONS)
    customers.append((cid, f"客户{cid:04d}", signup.date().isoformat(),
                      last_active.date().isoformat(), region))
    # 订单分布在 signup ~ last_active 之间
    for _ in range(n_orders):
        od = signup + timedelta(days=random.randint(0, max(1, (last_active - signup).days)))
        if od > now:
            od = now
        amt = max(50, random.gauss(avg_amt, avg_amt * 0.3))
        prod = random.choice(PRODUCTS)
        stage = random.choices(["A", "I", "P", "L"], weights=[1, 2, 5, 3])[0]
        orders.append((cid, od.date().isoformat(), round(amt, 2), prod, stage))
        # 同步生成营销/增长事件
        events.append((cid, "signup", signup.date().isoformat()))
        if random.random() < 0.8:
            events.append((cid, "activate", (signup + timedelta(days=random.randint(1, 10))).date().isoformat()))
        if random.random() < 0.6:
            events.append((cid, "retain", (od - timedelta(days=random.randint(0, 30))).date().isoformat()))
        if stage in ("P", "L"):
            events.append((cid, "pay", od.date().isoformat()))
        if random.random() < 0.25:
            events.append((cid, "refer", (od + timedelta(days=random.randint(1, 60))).date().isoformat()))
    # NPS 评分：活跃高分，静默低分
    score = random.randint(9, 10) if recency < 60 else (random.randint(7, 8) if recency < 150 else random.randint(0, 6))
    nps.append((cid, score))

if CSV_MODE:
    os.makedirs(OUT, exist_ok=True)
    def dump(name, header, rows):
        with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
    dump("customers.csv", ["customer_id", "name", "signup_date", "last_active_date", "region"], customers)
    dump("orders.csv", ["customer_id", "order_date", "amount", "product", "stage"], orders)
    dump("events.csv", ["user_id", "event", "event_date"], events)
    dump("nps.csv", ["user_id", "score"], nps)
    print(f"[OK] 样例 CSV 已生成于: {OUT}")
else:
    cur.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", customers)
    # orders 无显式 id，用自增
    cur.executemany("INSERT INTO orders(customer_id, order_date, amount, product, stage) VALUES (?,?,?,?,?)", orders)
    cur.executemany("INSERT INTO events VALUES (?,?,?)", events)
    cur.executemany("INSERT INTO nps_responses VALUES (?,?)", nps)
    conn.commit()
    conn.close()
    print(f"[OK] 样例库已生成: {OUT}")
print(f"      客户 {N} 人，订单 {len(orders)} 笔，事件 {len(events)} 条，NPS {len(nps)} 条")
