"""Ethereum mainnet baseline: same classification on Uniswap v3, 2 days x 6 windows x 30 min, via eth.drpc.org.
Run: python3 -I scripts/04_mainnet_baseline.py"""
import sys, os, json, time, calendar, statistics, csv, urllib.request
from collections import defaultdict, Counter
D = os.path.join(os.path.dirname(__file__), "..", "data"); os.makedirs(os.path.join(D, "mainnet"), exist_ok=True)
RPC = "https://eth.drpc.org"
SWAP = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
FACTORY = "0x1f98431c8ad98523631ae4a59f267346ea31f984"
WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
STABLES = {"0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": 6, "0xdac17f958d2ee523a2206206994597c13d831ec7": 6, "0x6b175474e89094c44da98b954eedeac495271d0f": 18}
DAYS = ["2026-09-04", "2026-10-14"]; HOURS = [2, 6, 10, 14, 18, 22]; WINDOW_S = 1800
CHUNK = 20
def call(m, p, retries=4):
    err = None
    for i in range(retries):
        try:
            req = urllib.request.Request(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), headers={"Content-Type": "application/json", "User-Agent": "frp-post/0.1"})
            with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
        except Exception as e: err = e; time.sleep(1.5 * (i + 1))
    raise err
def get_logs(a, b, topics):
    try:
        r = call("eth_getLogs", [{"fromBlock": hex(a), "toBlock": hex(b), "topics": topics}], retries=2)
    except Exception:
        r = {"error": "http"}
    if "error" in r:
        if b - a < 2: return []
        m = (a + b) // 2; return get_logs(a, m, topics) + get_logs(m + 1, b, topics)
    return r["result"]
_ts = {}
def ts(bn):
    if bn not in _ts: _ts[bn] = int(call("eth_getBlockByNumber", [hex(bn), False])["result"]["timestamp"], 16)
    return _ts[bn]
latest = int(call("eth_blockNumber", [])["result"], 16)
def block_at(t, lo=0, hi=None):
    hi = hi or latest
    while lo < hi:
        mid = (lo + hi) // 2
        if ts(mid) < t: lo = mid + 1
        else: hi = mid
    return lo
def s256(h): v = int(h, 16); return v - (1 << 256) if v >= (1 << 255) else v
pool_meta_f = os.path.join(D, "mainnet", "pools.json"); pool_meta = json.load(open(pool_meta_f)) if os.path.exists(pool_meta_f) else {}
def ecall(a, sig):
    r = call("eth_call", [{"to": a, "data": sig}, "latest"]); return r.get("result", "0x")
def symbol(a):
    h = ecall(a, "0x95d89b41")
    if len(h) <= 2: return "?"
    b = bytes.fromhex(h[2:])
    try:
        if len(b) >= 64: n = int.from_bytes(b[32:64], "big"); return b[64:64 + n].decode(errors="replace")
        return b.rstrip(b"\0").decode(errors="replace")
    except Exception: return "?"
def meta(pool):
    if pool in pool_meta: return pool_meta[pool]
    f = ecall(pool, "0xc45a0155")  # factory()
    if len(f) < 42 or "0x" + f[-40:] != FACTORY: pool_meta[pool] = None
    else:
        t0 = "0x" + ecall(pool, "0x0dfe1681")[-40:]; t1 = "0x" + ecall(pool, "0xd21220a7")[-40:]; fee = int(ecall(pool, "0xddca3f43"), 16)
        d0 = int(ecall(t0, "0x313ce567") or "0x12", 16) if t0 not in STABLES else STABLES[t0]
        d1 = int(ecall(t1, "0x313ce567") or "0x12", 16) if t1 not in STABLES else STABLES[t1]
        pool_meta[pool] = {"token0": t0, "token1": t1, "fee": fee, "d0": d0, "d1": d1, "s0": symbol(t0), "s1": symbol(t1)}
    json.dump(pool_meta, open(pool_meta_f, "w")); return pool_meta[pool]
sender_kind_f = os.path.join(D, "mainnet", "sender_kind.json"); sender_kind = json.load(open(sender_kind_f)) if os.path.exists(sender_kind_f) else {}
def kind_of(s, txs):
    if s in sender_kind: return sender_kind[s]
    code = call("eth_getCode", [s, "latest"])["result"]
    if len(code) <= 2: k = "eoa_direct"
    else:
        froms = {call("eth_getTransactionByHash", [h])["result"]["from"].lower() for h in txs[:15]}
        k = "bot_direct" if len(froms) <= 3 else "via_router"
    sender_kind[s] = k; json.dump(sender_kind, open(sender_kind_f, "w")); return k
MAJORS = {"WETH", "USDC", "USDT", "DAI", "WBTC", "cbBTC", "wstETH", "weETH", "rETH", "USDe", "LINK", "UNI", "AAVE", "PEPE", "SHIB"}
def take(fee): return 0.25 if fee in (100, 500) else 1 / 6
rows = []
for day in DAYS:
    for hh in HOURS:
        out = os.path.join(D, "mainnet", f"{day}_{hh:02d}.json")
        if os.path.exists(out): sw = json.load(open(out))
        else:
            t0 = calendar.timegm(time.strptime(day, "%Y-%m-%d")) + hh * 3600
            b0 = block_at(t0); b1 = block_at(t0 + WINDOW_S, b0, b0 + 400)
            logs = []
            for a in range(b0, b1 + 1, CHUNK):
                logs += get_logs(a, min(a + CHUNK - 1, b1), [SWAP]); time.sleep(0.2)
            logs = [l for l in logs if len(l["data"]) == 322]
            sw = []
            for l in logs:
                m = meta(l["address"].lower())
                if not m: continue
                d = l["data"][2:]
                sw.append({"tx": l["transactionHash"], "pool": l["address"].lower(), "sender": "0x" + l["topics"][1][-40:], "a0": s256(d[0:64]), "a1": s256(d[64:128]), "sqrtP": int(d[128:192], 16)})
            json.dump(sw, open(out, "w")); print(f"{day} {hh:02d} blocks {b0}-{b1} v3 swaps {len(sw)} (raw {len(logs)})", flush=True)
        px = []
        for s in sw:
            m = pool_meta[s["pool"]]
            if m["token0"] == "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48" and m["token1"] == WETH and s["sqrtP"]:
                r = (s["sqrtP"] / 2 ** 96) ** 2; px.append(1 / r * 1e12)  # USDC per WETH
        eth = statistics.median(px) if px else None
        by_tx = defaultdict(list)
        for s in sw: by_tx[s["tx"]].append(s)
        sender_txs = defaultdict(list)
        for tx, ss in by_tx.items():
            if len(ss) == 1: sender_txs[ss[0]["sender"]].append(tx)
        big = {s for s, t in sender_txs.items() if len(t) >= 20}
        for tx, ss in by_tx.items():
            if len(ss) >= 2:
                bought, sold = set(), set()
                for s in ss:
                    m = pool_meta[s["pool"]]
                    for tok, amt in ((m["token0"], s["a0"]), (m["token1"], s["a1"])): (sold if amt > 0 else bought).add(tok)
                cls = "round_trip" if bought & sold else "multi_hop"
            else:
                snd = ss[0]["sender"]; cls = kind_of(snd, sender_txs[snd]) if snd in big else "via_router"
            for s in ss:
                m = pool_meta[s["pool"]]; usd = None
                for tok, amt, dec in ((m["token0"], s["a0"], m["d0"]), (m["token1"], s["a1"], m["d1"])):
                    if tok in STABLES: usd = abs(amt) / 10 ** dec
                if usd is None and eth:
                    for tok, amt in ((m["token0"], s["a0"]), (m["token1"], s["a1"])):
                        if tok == WETH: usd = abs(amt) / 1e18 * eth
                cat = "crypto" if {m["s0"], m["s1"]} <= MAJORS else "other"
                lpf = usd * m["fee"] / 1e6 if usd is not None else None
                rows.append({"day": day, "hour": hh, "tx": tx, "class": cls, "pair": f"{m['s0']}/{m['s1']}", "cat": cat, "fee": m["fee"], "usd": usd, "lp_fee_usd": lpf, "proto_fee_usd": lpf * take(m["fee"]) if lpf is not None else None})
with open(os.path.join(D, "mainnet", "swaps_classified.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
def table(keyf, title, limit=30):
    agg = defaultdict(lambda: [0, 0.0, 0.0, 0.0, 0])
    for r in rows:
        a = agg[keyf(r)]; a[0] += 1
        if r["usd"] is None: a[4] += 1
        else: a[1] += r["usd"]; a[2] += r["lp_fee_usd"]; a[3] += r["proto_fee_usd"]
    tot = sum(a[3] for a in agg.values()) or 1
    print(f"\n{title}\n{'key':<36}{'swaps':>8}{'volume $':>14}{'lp fee $':>11}{'proto $':>10}{'share':>7}{'unpriced':>9}")
    for k, (n, v, f, pf, u) in sorted(agg.items(), key=lambda kv: -kv[1][3])[:limit]:
        print(f"{str(k):<36}{n:>8}{v:>14,.0f}{f:>11,.0f}{pf:>10,.0f}{pf/tot:>7.0%}{u:>9}")
print(f"mainnet swaps {len(rows)}")
table(lambda r: r["class"], "MAINNET BY CLASS"); table(lambda r: r["cat"], "MAINNET BY CATEGORY")
table(lambda r: (r["cat"], r["class"]), "MAINNET BY CATEGORY AND CLASS"); table(lambda r: r["day"], "MAINNET BY DAY"); table(lambda r: r["pair"], "MAINNET TOP PAIRS", 20)
