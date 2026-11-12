"""Sample Uniswap v3 Swap events on Robinhood Chain via public RPC.
14 days Aug-Oct 2026, 6 ten-minute windows per day. Writes data/samples/<day>_<hh>.json.
Run: python3 -I scripts/02_sample_swaps.py  (resumable; skips windows already saved)"""
import sys, json, time, calendar, os
sys.path.insert(0, os.path.dirname(__file__)); from rpc import call, get_logs
D = os.path.join(os.path.dirname(__file__), "..", "data")
SWAP = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
DAYS = ["2026-08-05","2026-08-12","2026-08-19","2026-08-26","2026-09-02","2026-09-04","2026-09-09","2026-09-16",
        "2026-09-23","2026-09-30","2026-10-07","2026-10-14","2026-10-21","2026-10-28"]
HOURS = [2, 6, 10, 14, 18, 22]
WINDOW_S = 600
pools = {p["pool"]: p for p in json.load(open(os.path.join(D, "robinhood_v3_pools.json")))}
latest = int(call("eth_blockNumber", [])["result"], 16)
_ts = {}
def ts(bn):
    if bn not in _ts: _ts[bn] = int(call("eth_getBlockByNumber", [hex(bn), False])["result"]["timestamp"], 16)
    return _ts[bn]
def block_at(target, lo=0, hi=None):
    hi = hi or latest
    while lo < hi:
        mid = (lo + hi) // 2
        if ts(mid) < target: lo = mid + 1
        else: hi = mid
    return lo
def s256(h):  # hex word -> signed int
    v = int(h, 16); return v - (1 << 256) if v >= (1 << 255) else v
t_all = time.time()
for day in DAYS:
    for hh in HOURS:
        out = os.path.join(D, "samples", f"{day}_{hh:02d}.json")
        if os.path.exists(out): continue
        t0 = calendar.timegm(time.strptime(day, "%Y-%m-%d")) + hh * 3600
        b0 = block_at(t0); b1 = block_at(t0 + WINDOW_S, b0, b0 + 20000)
        st = {}; logs = get_logs(b0, b1, [SWAP], None, st)
        rows = []
        for l in logs:
            a = l["address"].lower()
            if a not in pools: continue
            d = l["data"][2:]
            rows.append({"b": int(l["blockNumber"], 16), "tx": l["transactionHash"], "li": int(l["logIndex"], 16), "pool": a,
                         "sender": "0x" + l["topics"][1][-40:], "recipient": "0x" + l["topics"][2][-40:],
                         "a0": s256(d[0:64]), "a1": s256(d[64:128]), "sqrtP": int(d[128:192], 16)})
        json.dump({"day": day, "hour": hh, "from_block": b0, "to_block": b1, "all_swaps": len(logs), "v3_swaps": rows}, open(out, "w"))
        print(f"{day} {hh:02d}:00 blocks {b0}-{b1} swaps {len(logs)} v3 {len(rows)} calls {st.get('calls',0)} t={time.time()-t_all:.0f}s", flush=True)
print("done")
