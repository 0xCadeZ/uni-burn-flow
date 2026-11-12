"""Classify sampled swaps per transaction and price them. Works on whatever windows exist.
Classes:
  round_trip : >=2 swaps in tx and some token is both bought and sold within the tx (atomic arbitrage)
  multi_hop  : >=2 swaps, no round trip (one trade routed through several pools)
  bot_direct : single swap whose sender contract is called by <=3 distinct EOAs in a 15-tx sample (private bot)
  via_router : single swap through a contract used by many distinct EOAs (routers, aggregators, app)
USD: USDG leg at 1.0; WETH leg at the window's median WETH/USDG price; stock/WETH via WETH; else unpriced.
Protocol fee (UNIfication v3 schedule, same pattern on Robinhood): 1/4 of LP fee on 0.01% and 0.05% tiers, 1/6 on 0.30% and 1%.
Pair category: stock (tokenized equity/ETF tickers), crypto (WETH/USDG, majors), meme (everything else).
Run: python3 -I scripts/03_classify.py"""
import sys, os, json, glob, statistics, csv
sys.path.insert(0, os.path.dirname(__file__)); from rpc import call
from collections import defaultdict, Counter
D = os.path.join(os.path.dirname(__file__), "..", "data")
pools = {p["pool"]: p for p in json.load(open(os.path.join(D, "robinhood_v3_pools.json")))}
USDG = "0x" + "0" * 40  # filled below from symbols
syms = json.load(open(os.path.join(D, "token_symbols.json")))
for a, s in syms.items():
    if s["symbol"] == "USDG": USDG = a
WETH = "0x0bd7d308f8e1639fab988df18a8011f41eacad73"
cache_f = os.path.join(D, "sender_kind.json")
sender_kind = json.load(open(cache_f)) if os.path.exists(cache_f) else {}

def kind_of(sender, txs):
    if sender in sender_kind: return sender_kind[sender]
    code = call("eth_getCode", [sender, "latest"])["result"]
    if len(code) <= 2: k = "eoa_direct"
    else:
        froms = set()
        for h in txs[:15]:
            froms.add(call("eth_getTransactionByHash", [h])["result"]["from"].lower())
        k = "bot_direct" if len(froms) <= 3 else "via_router"
    sender_kind[sender] = k; json.dump(sender_kind, open(cache_f, "w"), indent=1); return k

STOCKS = {"SPCX","NVDA","SPY","MSTR","GME","AMC","TSLA","AAPL","META","MSFT","AMZN","GOOGL","GOOG","QQQ","COIN","HOOD","PLTR","NFLX","AMD","QCOM","OPEN","CRCL","SOFI","IF","Index"}
CRYPTO = {"WETH","USDG","USDC","USDT","WBTC","cbBTC","VIRTUAL"}
def take(fee):  # protocol share of LP fee by tier
    return 0.25 if fee in (100, 500) else (1/6 if fee in (3000, 10000) else 0.25)
STOCK_ADDRS = set(json.load(open(os.path.join(D, "rh_stock_tokens.json"))))  # official Robinhood asset registry (203 tokens)
def category(t0, t1, a0=None, a1=None):
    if (a0 in STOCK_ADDRS) or (a1 in STOCK_ADDRS): return "stock"
    s = {t0, t1}
    if s <= CRYPTO: return "crypto"
    return "meme"
rows_out = []
for f in sorted(glob.glob(os.path.join(D, "samples", "2026-*.json"))):
    w = json.load(open(f)); sw = w["v3_swaps"]
    if not sw: continue
    # WETH price in window from WETH/USDG swaps (sqrtP^2 / 2^192 gives token1/token0 in raw units)
    px = []
    for s in sw:
        p = pools[s["pool"]]
        if {p["token0"], p["token1"]} == {WETH, USDG} and s["sqrtP"]:
            r = (s["sqrtP"] / 2**96) ** 2  # token1 per token0, raw
            px.append(r * 1e12 if p["token0"] == WETH else (1 / r) * 1e12)
    eth = statistics.median(px) if px else None
    by_tx = defaultdict(list)
    for s in sw: by_tx[s["tx"]].append(s)
    sender_txs = defaultdict(list)
    for tx, ss in by_tx.items():
        if len(ss) == 1: sender_txs[ss[0]["sender"]].append(tx)
    big = {s for s, t in sender_txs.items() if len(t) >= 30}
    for tx, ss in by_tx.items():
        if len(ss) >= 2:
            bought, sold = set(), set()
            for s in ss:
                p = pools[s["pool"]]
                for tok, amt in ((p["token0"], s["a0"]), (p["token1"], s["a1"])):
                    (sold if amt > 0 else bought).add(tok)   # amt>0: pool received -> user sold it
            cls = "round_trip" if bought & sold else "multi_hop"
        else:
            snd = ss[0]["sender"]
            cls = kind_of(snd, sender_txs[snd]) if snd in big else "via_router"
        for s in ss:
            p = pools[s["pool"]]; usd = None
            if USDG in (p["token0"], p["token1"]):
                usd = abs(s["a0"] if p["token0"] == USDG else s["a1"]) / 1e6
            elif eth and WETH in (p["token0"], p["token1"]):
                usd = abs(s["a0"] if p["token0"] == WETH else s["a1"]) / 1e18 * eth
            t0, t1 = syms.get(p["token0"], {}).get("symbol", p["token0"][:8]), syms.get(p["token1"], {}).get("symbol", p["token1"][:8])
            lpf = (usd * p["fee"] / 1e6) if usd is not None else None
            rows_out.append({"day": w["day"], "hour": w["hour"], "tx": tx, "class": cls, "pool": s["pool"], "pair": f"{t0}/{t1}",
                             "cat": category(t0, t1, p["token0"], p["token1"]), "fee": p["fee"], "usd": usd, "lp_fee_usd": lpf,
                             "proto_fee_usd": (lpf * take(p["fee"])) if lpf is not None else None})
with open(os.path.join(D, "swaps_classified.csv"), "w", newline="") as fh:
    wr = csv.DictWriter(fh, fieldnames=list(rows_out[0].keys())); wr.writeheader(); wr.writerows(rows_out)

def table(keyf, title, limit=40):
    agg = defaultdict(lambda: [0, 0.0, 0.0, 0.0, 0])
    for r in rows_out:
        a = agg[keyf(r)]; a[0] += 1
        if r["usd"] is None: a[4] += 1
        else: a[1] += r["usd"]; a[2] += r["lp_fee_usd"]; a[3] += r["proto_fee_usd"]
    tot = sum(a[3] for a in agg.values()) or 1
    print(f"\n{title}")
    print(f"{'key':<36}{'swaps':>8}{'volume $':>14}{'lp fee $':>11}{'proto $':>10}{'share':>7}{'unpriced':>9}")
    for k, (n, v, f, pf, u) in sorted(agg.items(), key=lambda kv: -kv[1][3])[:limit]:
        print(f"{str(k):<36}{n:>8}{v:>14,.0f}{f:>11,.0f}{pf:>10,.0f}{pf/tot:>7.0%}{u:>9}")
windows = len({(r['day'], r['hour']) for r in rows_out})
print(f"windows {windows}, swaps {len(rows_out)}")
table(lambda r: r["class"], "BY CLASS (all windows)")
table(lambda r: r["cat"], "BY PAIR CATEGORY")
table(lambda r: (r["cat"], r["class"]), "BY CATEGORY AND CLASS")
table(lambda r: (r["day"][:7], r["class"]), "BY MONTH AND CLASS")
table(lambda r: (r["day"][:7], r["cat"]), "BY MONTH AND CATEGORY")
table(lambda r: r["day"], "BY SAMPLE DAY", 20)
table(lambda r: r["pair"], "TOP PAIRS", 25)
