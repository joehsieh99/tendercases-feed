"""把 feed 濃縮成一行一案，給排程任務快速分流。

用法：python3 tools/brief.py [feed/recent.json] [--after-event N]
輸出：健康狀態、候選案（一行一筆）、異動事件（一行一筆）。
"""
import json
import sys

path = next((a for a in sys.argv[1:] if a.endswith(".json")), "feed/recent.json")
after = 0
if "--after-event" in sys.argv:
    after = int(sys.argv[sys.argv.index("--after-event") + 1])
f = json.load(open(path, encoding="utf-8"))
h = f["health"]
print(f"# feed {f['generated_at']}  health={h['status']}  consecutive_degraded={h['consecutive_degraded']}  "
      f"open_total={f.get('open_total', len(f['candidates']))}  window={f['window']['from']}~{f['window']['to']}")
for i in h["issues"]:
    if i["level"] != "info":
        print(f"!  {i['level']} {i['code']} {i.get('day', '')} {i['msg']}")
def rank(c):
    return c.get("priority_rank") or 99


cands = sorted(f["candidates"], key=rank)
npri = sum(1 for c in cands if c.get("priority"))
def bond(b):
    if not b:
        return "未載明"
    if b.get("required") is False:
        return "免"
    if b.get("required") is True:
        a = b.get("amount")
        return f"需繳 {a:,} 元" if a else (f"需繳（{b['amount_text']}）" if b.get("amount_text") else "需繳（金額見招標文件）")
    return b.get("text") or "未載明"


print(f"\n## candidates ({len(cands)}, 優先 {npri})  doc_id | 優先 | stage | school | 機關 | 案名 | 預算 | 截止 | 招標方式 | 決標方式 | 押標金 | 履約保證金 | 分類 | 網址")
for c in cands:
    print(" | ".join(str(x) for x in (
        c["doc_id_hint"], ("★" + "、".join(c.get("priority_labels") or []) if c.get("priority") else "-"), c["stage"], "S" if c["school"] else "-",
        c["unit_name"], c["title"], c["budget"] if c["budget"] is not None else "未標示", c["deadline"] or "-",
        c.get("method") or "-", c.get("award_method") or "-", bond(c.get("bid_bond")), bond(c.get("perf_bond")), (c["category"] or "-")[:20], c.get("official_url") or "-")))
pay = [c for c in cands if c.get("payment_notes")]
if pay:
    print(f"\n## payment notes ({len(pay)})  doc_id | 履約期限 | 公告中的付款文字")
    for c in pay:
        print(f"{c['doc_id_hint']} | {c.get('perf_period') or '-'} | " + " / ".join(c["payment_notes"]))
ev = [e for e in f["changes"] if e["event_id"] > after and e["change_type"] != "new"]
print(f"\n## changes after event {after} ({len(ev)})  event_id | type | doc_id | 案名 | detail")
for e in ev:
    print(f"{e['event_id']} | {e['change_type']} | pcc-{e['job_number']} | {e['title']} | "
          f"{json.dumps(e['detail'], ensure_ascii=False)}")
print(f"\n# max_event_id={max([e['event_id'] for e in f['changes']] or [after])}")
