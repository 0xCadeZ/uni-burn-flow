"""Step 1: Uniswap protocol fees and revenue (the burn funding) from DefiLlama, daily, by chain and version.
Reconciles the 30-day revenue to tokenbuybacks.app. Run: python3 -I notebooks/01_fee_series.py"""
import csv, json, datetime as dt
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "data"
rev = json.load(open(D / "llama_uniswap_revenue.json"))
fee = json.load(open(D / "llama_uniswap_fees.json"))

def series(d):
    return {dt.date.fromtimestamp(t).isoformat(): v for t, v in d["totalDataChart"]}

def breakdown(d):
    out = {}
    for t, by_chain in d["totalDataChartBreakdown"]:
        day = dt.date.fromtimestamp(t).isoformat()
        for chain, vers in by_chain.items():
            for ver, v in vers.items():
                out[(day, chain, ver)] = v
    return out

r, f = series(rev), series(fee)
days = sorted(set(r) | set(f))
with open(D / "daily_fees_revenue.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["day", "fees_usd", "revenue_usd", "revenue_share"])
    for d in days:
        fv, rv = f.get(d, 0), r.get(d, 0)
        w.writerow([d, round(fv, 2), round(rv, 2), round(rv / fv, 4) if fv else ""])

rb, fb = breakdown(rev), breakdown(fee)
with open(D / "daily_by_chain_version.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["day", "chain", "version", "fees_usd", "revenue_usd"])
    for k in sorted(set(rb) | set(fb)):
        w.writerow([*k, round(fb.get(k, 0), 2), round(rb.get(k, 0), 2)])

last90 = days[-90:]
tot_f = sum(f.get(d, 0) for d in last90); tot_r = sum(r.get(d, 0) for d in last90)
print(f"Last 90 days: fees ${tot_f:,.0f}, revenue (burn funding) ${tot_r:,.0f}, share {tot_r/tot_f:.1%}")
print(f"Last 30 days revenue ${rev['total30d']:,.0f} vs tokenbuybacks 30d burn $8,190,000 -> diff {(rev['total30d']/8_190_000-1):+.1%}")
agg = {}
for (d, c, v), x in rb.items():
    if d in last90 and x: agg[(c, v)] = agg.get((c, v), 0) + x
print("\n90-day revenue by chain/version (where the burn comes from):")
for (c, v), x in sorted(agg.items(), key=lambda kv: -kv[1])[:10]:
    fees = sum(fb.get((d, c, v), 0) for d in last90)
    print(f"  {c:16} {v:11} revenue ${x:>12,.0f}  of fees ${fees:>13,.0f}  ({x/fees:.0%} take)" if fees else f"  {c:16} {v:11} ${x:,.0f}")
