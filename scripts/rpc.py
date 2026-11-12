"""Minimal JSON-RPC helper for Robinhood Chain public RPC (rate limited, 10M blocks / 10k logs per request)."""
import json, time, urllib.request
RPC = "https://rpc.mainnet.chain.robinhood.com"
def call(method, params, retries=4):
    err = None
    for i in range(retries):
        try:
            req = urllib.request.Request(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
                                         headers={"Content-Type": "application/json", "User-Agent": "frp-post/0.1"})
            with urllib.request.urlopen(req, timeout=90) as r:
                out = json.load(r)
            if "error" in out and "limit" not in str(out["error"]) and "narrow" not in str(out["error"]):
                raise RuntimeError(out["error"])
            return out
        except Exception as e:
            err = e; time.sleep(1.5 * (i + 1))
    raise err
def get_logs(frm, to, topics, address=None, stats=None):
    """Adaptive splitting on the 10k-logs limit. Returns list of logs."""
    f = {"fromBlock": hex(frm), "toBlock": hex(to), "topics": topics}
    if address: f["address"] = address
    r = call("eth_getLogs", [f])
    if stats is not None: stats["calls"] = stats.get("calls", 0) + 1
    if "error" in r:
        if to - frm < 2: return []
        mid = (frm + to) // 2
        return get_logs(frm, mid, topics, address, stats) + get_logs(mid + 1, to, topics, address, stats)
    return r["result"]
