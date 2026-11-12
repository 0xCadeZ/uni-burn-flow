"""Four SVG charts for the post, light theme, validated palette (blue/orange/aqua). Writes charts/*.html and *.svg."""
import json, os
D = os.path.join(os.path.dirname(__file__), "..", "data"); C = os.path.join(os.path.dirname(__file__), "..", "charts")
BLUE, ORANGE, AQUA, MUTED, INK, INK2, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#898781", "#0b0b0b", "#52514e", "#e1e0d9"
FONT = "font-family:system-ui,-apple-system,'Segoe UI',sans-serif"
def wrap(svg, title, sub, w, h):
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>body{{margin:0;background:#fcfcfb;{FONT};color:{INK}}}
.c{{width:{w}px;padding:20px 24px 16px;box-sizing:border-box}} h2{{font-size:17px;margin:0 0 2px;font-weight:600}} p{{margin:0 0 10px;color:{INK2};font-size:13px}}
.src{{color:{MUTED};font-size:11px;margin-top:6px}}</style></head><body><div class="c"><h2>{title}</h2><p>{sub}</p>{svg}<div class="src">Source: public RPC sample (84 ten-minute windows, Aug 5 to Oct 28 2026) and DefiLlama. Code and data: see repo.</div></div></body></html>'''
def fmtm(v): return f"${v/1e6:.1f}M" if v >= 1e6 else f"${v/1e3:.0f}k"

# Chart 1: monthly Uniswap protocol revenue, Robinhood vs other chains (DefiLlama)
months = ["2026-06","2026-07","2026-08","2026-09","2026-10","2026-11*"]
total = [5.13,4.41,9.33,15.49,8.53,2.65]; rh = [0,0.77,4.21,8.74,1.76,0.51]
W,H,L,R,T,B = 640,300,56,16,12,40; n=len(months); ymax=16
x=lambda i: L+(W-L-R)*(i+0.5)/n; y=lambda v: T+(H-T-B)*(1-v/ymax); bw=58
s=[f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" style="{FONT}">']
for v in range(0,17,4): s.append(f'<line x1="{L}" x2="{W-R}" y1="{y(v)}" y2="{y(v)}" stroke="{GRID}"/><text x="{L-6}" y="{y(v)+4}" text-anchor="end" font-size="11" fill="{MUTED}">${v}M</text>')
for i,m in enumerate(months):
    oth=total[i]-rh[i]
    s.append(f'<rect x="{x(i)-bw/2}" y="{y(oth)}" width="{bw}" height="{y(0)-y(oth)}" fill="{BLUE}" rx="0"/>')
    if rh[i]>0: s.append(f'<rect x="{x(i)-bw/2}" y="{y(total[i])}" width="{bw}" height="{y(oth)-y(total[i])-2}" fill="{ORANGE}" rx="3"/>')
    s.append(f'<text x="{x(i)}" y="{y(total[i])-6}" text-anchor="middle" font-size="12" font-weight="600" fill="{INK}">{fmtm(total[i]*1e6)}</text>')
    s.append(f'<text x="{x(i)}" y="{H-B+16}" text-anchor="middle" font-size="11" fill="{MUTED}">{m}</text>')
s.append(f'<rect x="{L}" y="{H-14}" width="10" height="10" fill="{ORANGE}" rx="2"/><text x="{L+14}" y="{H-5}" font-size="12" fill="{INK2}">Robinhood Chain</text>')
s.append(f'<rect x="{L+130}" y="{H-14}" width="10" height="10" fill="{BLUE}" rx="2"/><text x="{L+144}" y="{H-5}" font-size="12" fill="{INK2}">All other chains</text></svg>')
open(os.path.join(C,"1_monthly_revenue.html"),"w").write(wrap("".join(s),"Uniswap protocol revenue (UNI burn funding) by month","Robinhood Chain fee switch went live 27 July. *November is 12 days.",W+48,H+100))

# Chart 2: volume share vs protocol fee share by category, Robinhood Chain
cats=[("Crypto majors (WETH/USDG, 0.01% tier)",72,12,BLUE),("Tokenized stocks and ETFs",14,23,AQUA),("Memecoins (mostly 1% tier)",13,64,ORANGE)]
W,H,L,R,T,B=640,250,250,60,16,10; rowH=70
s=[f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" style="{FONT}">']
xx=lambda v: L+(W-L-R)*v/100
for i,(name,vol,fee,col) in enumerate(cats):
    yy=T+i*rowH
    s.append(f'<text x="{L-10}" y="{yy+16}" text-anchor="end" font-size="12" fill="{INK}">{name}</text>')
    s.append(f'<text x="{L-10}" y="{yy+44}" text-anchor="end" font-size="11" fill="{MUTED}">volume / protocol fee</text>')
    s.append(f'<rect x="{L}" y="{yy+4}" width="{xx(vol)-L}" height="18" fill="{col}" opacity="0.45" rx="3"/><text x="{xx(vol)+6}" y="{yy+17}" font-size="12" fill="{INK2}">{vol}% of volume</text>')
    s.append(f'<rect x="{L}" y="{yy+28}" width="{xx(fee)-L}" height="18" fill="{col}" rx="3"/><text x="{xx(fee)+6}" y="{yy+41}" font-size="12" font-weight="600" fill="{INK}">{fee}% of protocol fee</text>')
s.append('</svg>')
open(os.path.join(C,"2_volume_vs_fee.html"),"w").write(wrap("".join(s),"On Robinhood Chain, what trades is not what pays","Share of Uniswap v3 swap volume versus share of protocol fee (burn funding), Aug to Oct 2026 sample.",W+48,H+100))

# Chart 3: protocol fee by sample day, stacked by category
dc=json.load(open(os.path.join(D,"chart_day_cat.json"))); days=list(dc)
W,H,L,R,T,B=640,300,56,16,12,44; n=len(days); ymax=20000
x=lambda i: L+(W-L-R)*(i+0.5)/n; y=lambda v: T+(H-T-B)*(1-v/ymax); bw=30
s=[f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" style="{FONT}">']
for v in range(0,20001,5000): s.append(f'<line x1="{L}" x2="{W-R}" y1="{y(v)}" y2="{y(v)}" stroke="{GRID}"/><text x="{L-6}" y="{y(v)+4}" text-anchor="end" font-size="11" fill="{MUTED}">${v//1000}k</text>')
for i,d in enumerate(days):
    base=0
    for cat,col in (("crypto",BLUE),("stock",AQUA),("meme",ORANGE)):
        v=dc[d].get(cat,0)
        if v: s.append(f'<rect x="{x(i)-bw/2}" y="{y(base+v)}" width="{bw}" height="{max(0,y(base)-y(base+v)-1.5)}" fill="{col}"/>'); base+=v
    s.append(f'<text x="{x(i)}" y="{H-B+14}" text-anchor="middle" font-size="10" fill="{MUTED}">{d[5:]}</text>')
for j,(lab,col) in enumerate((("Memecoins",ORANGE),("Tokenized stocks",AQUA),("Crypto majors",BLUE))):
    s.append(f'<rect x="{L+j*150}" y="{H-12}" width="10" height="10" fill="{col}" rx="2"/><text x="{L+14+j*150}" y="{H-3}" font-size="12" fill="{INK2}">{lab}</text>')
s.append('</svg>')
open(os.path.join(C,"3_fee_by_day.html"),"w").write(wrap("".join(s),"The spike and the fade: sampled protocol fee per day, Robinhood Chain","Sum of six 10-minute windows per day. September's peak and October's collapse are mostly memecoin pools.",W+48,H+100))

# Chart 4: transaction class mix, Robinhood vs mainnet
cls=[("Single swap via shared router",58,61),("Round trip (atomic arbitrage)",30,26),("Multi-hop",9,13),("Private bot, direct",4,0)]
W,H,L,R,T,B=640,230,240,70,12,24; rowH=50
s=[f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" style="{FONT}">']
xx=lambda v: L+(W-L-R)*v/70
for i,(name,a,b) in enumerate(cls):
    yy=T+i*rowH
    s.append(f'<text x="{L-10}" y="{yy+20}" text-anchor="end" font-size="12" fill="{INK}">{name}</text>')
    s.append(f'<rect x="{L}" y="{yy+2}" width="{max(1,xx(a)-L)}" height="15" fill="{ORANGE}" rx="3"/><text x="{xx(a)+5}" y="{yy+14}" font-size="11" fill="{INK}">{a}%</text>')
    s.append(f'<rect x="{L}" y="{yy+20}" width="{max(1,xx(b)-L)}" height="15" fill="{BLUE}" rx="3"/><text x="{xx(b)+5}" y="{yy+32}" font-size="11" fill="{INK}">{b}%</text>')
s.append(f'<rect x="{L}" y="{H-12}" width="10" height="10" fill="{ORANGE}" rx="2"/><text x="{L+14}" y="{H-3}" font-size="12" fill="{INK2}">Robinhood Chain</text>')
s.append(f'<rect x="{L+140}" y="{H-12}" width="10" height="10" fill="{BLUE}" rx="2"/><text x="{L+154}" y="{H-3}" font-size="12" fill="{INK2}">Ethereum mainnet</text></svg>')
open(os.path.join(C,"4_class_mix.html"),"w").write(wrap("".join(s),"Who pays: transaction class share of protocol fee","Same classifier on both chains. Arbitrage share is a Uniswap property, not a Robinhood one.",W+48,H+100))
print("wrote 4 charts")
