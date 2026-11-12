# Findings log

## 2026-11-12 Step 0: reconciling Robinhood Chain's share (DefiLlama revenue breakdown)

Source: api.llama.fi/summary/fees/uniswap?dataType=dailyRevenue, chain/version breakdown.
Robinhood Chain fee-switch revenue first appears 2026-07-27 (v3 only; v4 shows fees but no revenue).

| Window | Total protocol revenue | Robinhood Chain | Share |
|---|---|---|---|
| Since fee switch (2025-12-28) | $64.7M | $16.0M | 25% |
| Since 2026-07-01 | $40.4M | $16.0M | 40% |
| Last 90 days | $32.9M | $13.5M | 41% |
| Last 30 days | $8.1M | $1.4M | 17% |
| Last 7 days | $1.4M | $0.2M | 18% |

Monthly:

| Month | Total | Robinhood | Share |
|---|---|---|---|
| 2026-07 | $4.4M | $0.8M | 17% |
| 2026-08 | $9.3M | $4.2M | 45% |
| 2026-09 | $15.5M | $8.7M | 56% |
| 2026-10 | $8.5M | $1.8M | 21% |
| 2026-11 (12 days) | $2.6M | $0.5M | 19% |

Reconciliation: the press figures of 60-69% were daily or weekly snapshots around the early-September
peak (Robinhood DEX volume crossed $3B/day on 2026-09-04). September's monthly share was 56%.
Our 41% is the 90-day average. All three are consistent; they differ by window.

The more important observation: total burn revenue fell 45% from September to October, and the
November run-rate (~$6.6M/month) is 57% below September. Most of the drop is Robinhood Chain:
its revenue fell 80% from September to October. The burn is concentrated and volatile, which is
exactly the durability question the post is about. Whether the September spike was arbitrage
flow (hypothesis) or organic tokenized-stock demand is now the central empirical question.

## 2026-11-12 Step 2: what kind of trading funds the burn on Robinhood Chain (sampled swaps)

Method: public RPC (no account), all Uniswap v3 Swap events in 84 ten-minute windows
(14 days Aug 5 to Oct 28, six windows per day), 1,185,619 swaps in 449,704 v3 pools.
USD from the USDG leg, or the WETH leg at the window's WETH/USDG price (99% priced).
Protocol take per UNIfication schedule: 1/4 of LP fee on 0.01%/0.05% tiers, 1/6 on 0.30%/1%.

Reconciliation: sampled protocol fees of $94,902 over 14 sampled hours scale to about $163k/day,
or $15.0M over Aug-Oct, against $14.7M of Robinhood Chain v3 revenue reported by DefiLlama (+2%).

### Who pays the burn-funding fees (share of protocol fee)
| Transaction class | Swaps | Volume | Protocol fee share |
|---|---|---|---|
| Single swap via a router used by many users | 797k | $345M | 58% |
| Round trip (same token bought and sold in one tx: atomic arbitrage) | 334k | $78M | 30% |
| Multi-hop (one trade through several pools) | 23k | $16M | 9% |
| Single swap from a private bot contract | 32k | $59M | 4% |

Atomic arbitrage plus private bots: about 34% of burn funding. The rest went through routers,
which includes the Robinhood app path and aggregators; some bots use routers too, so 34% is a floor.

### What is being traded (share of protocol fee)
Categories by token address against Robinhood's own asset registry (api.robinhood.com/rhj/assets,
203 stock and ETF tokens on chain 4663), WETH/USDG and majors as crypto, everything else memecoin.

| Pair category | Swaps | Volume | LP fee | Protocol fee share |
|---|---|---|---|---|
| Memecoins (mostly X/WETH at the 1% tier) | 467k | $67M | $365k | 64% |
| Tokenized stocks and ETFs (203 registry tokens) | 256k | $73M | $120k | 23% |
| Crypto majors (almost all WETH/USDG at 0.01%) | 463k | $357M | $49k | 12% |

The headline inversion: WETH/USDG is 72% of volume but 12% of fees, because it sits at the
0.01% tier. Memecoin pools at the 1% tier are 13% of volume but 64% of the burn funding.
Tokenized stocks, the chain's stated purpose, funded 23%.

Within tokenized stocks, round-trip (atomic arbitrage) transactions were 137k of 256k swaps and
40% of stock-pool protocol fees (9 of 23 points). Within memecoins, round trips were 19 of 64 points.

### Over time (protocol fee in the sample, by month and category)
| Month | Memecoin | Stock | Crypto |
|---|---|---|---|
| Aug | 24% | 1% | 1% |
| Sep | 36% | 19% | 8% |
| Oct | 4% | 4% | 4% |
(Shares of the whole 3-month sample. Both the September spike and the October collapse are mostly
memecoin, but tokenized stocks also spiked in September, 19 points, and fell to 4 in October.)

Peak sample day Sep 4: 19% of all sampled protocol fees. Oct 21 and Oct 28: 2% each.

### Reading
1. The UNI burn's biggest funder in Aug-Oct was not tokenized-stock trading but a memecoin
   launchpad cycle on Robinhood Chain, taxed at the 1% tier (64% of protocol fees). When the
   cycle faded in October, Robinhood revenue fell 80% and total burn revenue fell 45%.
2. Arbitrage is a meaningful but not dominant payer overall: round trips are 30% of burn funding
   (19 points memecoin, 9 points stock, 1 point crypto), private bots another 4%.
3. Tokenized stocks funded 23%, and 40% of that was atomic arbitrage: the 24-hour on-chain stock
   market does attract round-trip bots, as hypothesised, but the stock base is still a quarter
   of the total and it also spiked and fell with September.

### Limits (state in the post)
- Sampling: 14 of 92 days, 1 hour per day. Day-of-week and intraday effects are only partly covered.
- Router class mixes retail, the Robinhood app, aggregators and any bot that routes through them.
- Round-trip test catches atomic arbitrage only; CEX-DEX (non-atomic) arbitrage lands in the router class.
- Category assignment uses token symbols; unknown symbols default to memecoin. Top pairs were checked by hand.
- Protocol take assumed from the UNIfication schedule; DefiLlama's 26% average take for Robinhood is consistent.

## 2026-11-12 Step 3: Ethereum mainnet baseline (same classifier)

Two of the sampled days (Sep 4, Oct 14), six 30-minute windows each, via eth.drpc.org public RPC.
36,286 Uniswap v3 swaps (pools verified by factory() call). Pricing from USDC/USDT/DAI legs or WETH leg.

| Class | Robinhood Chain | Ethereum mainnet |
|---|---|---|
| Via router | 58% | 61% |
| Round trip (atomic arbitrage) | 30% | 26% |
| Multi-hop | 9% | 13% |
| Private bot direct | 4% | 0% |

| Category | Robinhood Chain | Ethereum mainnet |
|---|---|---|
| Crypto majors (WETH, stables, WBTC...) | 12% | 73% |
| Tokenized stocks | 23% | ~5% (NVDAon, TSLAon in "other") |
| Memecoins / long tail | 64% | ~22% |

Reading: the transaction-class mix is similar on both chains. Atomic arbitrage is roughly a quarter
to a third of burn funding everywhere; that is a property of Uniswap v3, not of Robinhood Chain.
What differs is what is traded: mainnet burn funding comes 73% from blue-chip pairs, Robinhood's
came 64% from memecoins. The durability difference is in the asset mix, not the bot share.

Scale check: sampled mainnet protocol fees imply ~$60k/day versus DefiLlama's 90-day average of
~$110k/day for Ethereum v3. The two sampled days were calmer than the period average (which includes
the October 10 liquidation day), and ~2% of swaps are unpriced; treat mainnet shares as indicative.
