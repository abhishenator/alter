"""Generate Moneytaur trading lessons PDF from synthesized research."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, black, grey
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, ListFlowable, ListItem,
)

OUT = "/home/user/alter/moneytaur_research/Moneytaur_Trading_Playbook.pdf"

styles = getSampleStyleSheet()
H_TITLE = ParagraphStyle("HTitle", parent=styles["Title"], fontSize=26,
                         textColor=HexColor("#0a2540"), spaceAfter=14,
                         alignment=TA_CENTER)
H_SUB = ParagraphStyle("HSub", parent=styles["Normal"], fontSize=12,
                       textColor=HexColor("#6b7280"), spaceAfter=22,
                       alignment=TA_CENTER)
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=18,
                    textColor=HexColor("#0a2540"), spaceBefore=18, spaceAfter=10)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14,
                    textColor=HexColor("#0f766e"), spaceBefore=12, spaceAfter=6)
BODY = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=10.5,
                      leading=15, alignment=TA_JUSTIFY, spaceAfter=8)
QUOTE = ParagraphStyle("Quote", parent=BODY, leftIndent=18, rightIndent=18,
                       textColor=HexColor("#374151"), fontName="Helvetica-Oblique",
                       backColor=HexColor("#f3f4f6"), borderPadding=8,
                       spaceBefore=6, spaceAfter=10)
BULLET = ParagraphStyle("Bullet", parent=BODY, leftIndent=14, bulletIndent=2,
                        spaceAfter=3)

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=2.2*cm, rightMargin=2.2*cm,
                        topMargin=2.0*cm, bottomMargin=2.0*cm,
                        title="Moneytaur Trading Playbook",
                        author="Research compiled from public sources")

story = []


def p(text, style=BODY):
    story.append(Paragraph(text, style))


def bullets(items, style=BULLET):
    lst = ListFlowable(
        [ListItem(Paragraph(i, style), leftIndent=10) for i in items],
        bulletType="bullet", start="circle",
    )
    story.append(lst)
    story.append(Spacer(1, 4))


# ---------- COVER ----------
p("Moneytaur Trading Playbook", H_TITLE)
p("Decoded from @Moneytaur_ — Style, Strategy, Risk &amp; Lessons", H_SUB)

p(
    "This document synthesizes the publicly-available trading philosophy of "
    "<b>@Moneytaur_</b> — a technical crypto/futures trader known on X/Twitter "
    "for free educational threads on price action, risk management, and market "
    "structure. Source material was aggregated from Thread Reader App indexes, "
    "public search results, third-party repostings, and community GitHub "
    "projects that catalog his tweet archive (e.g. <i>vadimbacalov/moneytaurproject</i> "
    "and <i>SheikhEl6/moneytaur-pipeline</i>).",
    BODY,
)
p(
    "<b>Scope note.</b> X/Twitter is auth-gated and cannot be scraped without a "
    "logged-in session. The observations below are distilled from publicly "
    "indexed snippets and summaries of his threads, not a full tweet-by-tweet "
    "dump. Treat this as an interpretation of his style — not investment advice.",
    QUOTE,
)

story.append(Spacer(1, 10))
tbl = Table(
    [
        ["Handle", "@Moneytaur_"],
        ["Markets", "Crypto spot &amp; perpetual futures (BTC, ETH, majors, alts)"],
        ["Approach", "Technical — price action + selective indicators"],
        ["Style", "Trend-follower with sniper-precision entries ('refining')"],
        ["Leverage", "Comfortable at 20x+ because of tight stops"],
        ["Teaching posture", "Free content; combative toward 'TA experts'"],
    ],
    colWidths=[4.2*cm, 12.0*cm],
)
tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (0, -1), HexColor("#0a2540")),
    ("TEXTCOLOR",  (0, 0), (0, -1), HexColor("#ffffff")),
    ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
    ("FONTSIZE",   (0, 0), (-1, -1), 10),
    ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
    ("BOX",        (0, 0), (-1, -1), 0.5, grey),
    ("INNERGRID",  (0, 0), (-1, -1), 0.25, grey),
    ("LEFTPADDING",  (0, 0), (-1, -1), 8),
    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ("TOPPADDING",    (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
story.append(tbl)

story.append(PageBreak())

# ---------- 1. CORE PHILOSOPHY ----------
p("1. Core Trading Philosophy", H1)
p(
    "Moneytaur's worldview starts from a blunt premise: <b>crypto markets are "
    "engineered environments where wealthy participants extract fiat from "
    "retail</b>. He is openly skeptical of the 'Bitcoin as pure freedom money' "
    "narrative and treats price action as a game with identifiable rules that "
    "favor well-trained, disciplined operators.",
    BODY,
)
p("From that, three convictions follow", H2)
bullets([
    "<b>Edge is technical and learnable.</b> He rejects the idea that trading "
    "is luck. Edge comes from repetition, level-mapping and emotional control.",
    "<b>All-weather skill over directional bet.</b> 'If you possess the skills "
    "to profit in any market condition, you won't get REKT when the top is in.'",
    "<b>Free teaching as signal.</b> He is confrontational toward paid-group "
    "'TA experts' who, in his view, get stopped out on 2R trades.",
])

# ---------- 2. TRADING STYLE ----------
p("2. Trading Style", H1)

p("2.1 Trend Trader — on every timeframe at once", H2)
p(
    "Moneytaur describes markets as a <b>nest of simultaneous trends</b> "
    "across timeframes. His job is to identify the dominant trend on the "
    "timeframe he is operating on, align lower-timeframe entries with it, and "
    "refuse to fight higher-timeframe direction.",
    BODY,
)

p("2.2 Price Action First, Indicators for Confirmation", H2)
p(
    "Raw price structure — swing highs/lows, wicks, reclaims, rejections — "
    "is the primary input. Indicators are used to confirm, not to decide. He "
    "specifically calls out <b>USDT Dominance (USDT.D)</b> as a 'blatant signal "
    "with massive market impact' — rising USDT.D = risk-off for alts, falling "
    "USDT.D = risk-on.",
    BODY,
)

p("2.3 Levels, Not Signals", H2)
p(
    "He trades <b>zones</b>, not triggers. Rather than rigid entry/exit rules, "
    "his framework is: map the key levels, wait for price to come to them, "
    "then ride the move with a trailing stop. 'Find levels and ride market "
    "moves while trailing stops' — not fixed entries and exits.",
    QUOTE,
)

# ---------- 3. THE "REFINING" METHOD ----------
p("3. The 'Refining' Method — his signature edge", H1)
p(
    "Across his threads, Moneytaur names <b>refining</b> (and its upgraded "
    "form <b>ultra-refining</b>) as the single most life-changing skill in "
    "trading. It is the art of progressively zooming into lower timeframes "
    "to tighten the invalidation on a trade while keeping the target intact.",
    BODY,
)

p("3.1 Why refining matters mechanically", H2)
bullets([
    "<b>Smaller stop → bigger R:R.</b> A 4R trade refined to a tighter "
    "invalidation can become 10R+ at the same target.",
    "<b>Smaller stop → higher usable leverage.</b> Because dollar risk stays "
    "constant, a tighter stop means position size can grow — this is how he "
    "justifies comfortable use of 20x+ without blowing up.",
    "<b>Leverage is a function of stop, not confidence.</b> You do not use "
    "20x because you are sure; you use 20x because your stop is 0.2% away.",
])

p("3.2 How he says to learn it", H2)
bullets([
    "Study content, then <b>recreate the charts yourself</b> on your own "
    "TradingView account — don't just read.",
    "Expect <b>weeks to months</b> of dedicated practice. 'Don't expect to "
    "perform at elite level in 1-2 months if you're not even a profitable "
    "trader yet.'",
    "Start with the higher-timeframe bias, then zoom down 2-3 timeframes to "
    "find the cleanest structural invalidation.",
])

p("3.3 A refined entry looks like…", H2)
p(
    "1) Identify the HTF key level (daily / 4H support or resistance).<br/>"
    "2) Wait for price to arrive at the level — never chase.<br/>"
    "3) Drop to 15m / 5m and look for a <b>reclaim, sweep, or structure "
    "break</b> that defines an invalidation wick.<br/>"
    "4) Place the stop just beyond that wick. That is the refined entry.<br/>"
    "5) Scale size from the new, tighter risk — not from conviction.",
    BODY,
)

story.append(PageBreak())

# ---------- 4. RISK & MONEY MANAGEMENT ----------
p("4. Risk &amp; Money Management", H1)

p("4.1 Stop-loss is non-negotiable", H2)
p(
    "Every trade has a stop. The stop is defined by <b>structure</b>, not a "
    "round percentage. If structure invalidates 0.25% away, that's your stop; "
    "if it's 2%, that's your stop — and you size accordingly.",
    BODY,
)

p("4.2 Partial take-profits — the 35% rule", H2)
p(
    "Rather than bringing a full position to the 'best case scenario' (BCS) "
    "target, Moneytaur advises <b>taking ~35% off while the trade is still "
    "running</b>. This does three things:",
    BODY,
)
bullets([
    "Locks in realized P&amp;L so the trade cannot round-trip to a loss.",
    "Leaves a meaningful runner for the extended move.",
    "Creates <b>ammunition to add back</b> if a new key level forms inside "
    "the trading range — he re-enters with <i>already-realized profit</i>, not "
    "fresh risk capital.",
])

p("4.3 Trailing stops over fixed targets", H2)
p(
    "For the remaining 65% runner, the exit is managed with a trailing stop "
    "behind structure — each new higher-low (longs) or lower-high (shorts) "
    "drags the stop up. You do not predict the top; you let the market take "
    "you out.",
    BODY,
)

p("4.4 Leverage as a derived variable", H2)
tbl2 = Table(
    [
        ["Variable", "Moneytaur's framing"],
        ["Account risk", "Fixed — e.g. 0.5–2% per idea"],
        ["Stop distance", "Determined by structure (refining tightens this)"],
        ["Position size", "Risk ÷ stop distance"],
        ["Leverage", "Whatever size requires — often 20x+ because stops are tight"],
    ],
    colWidths=[4.5*cm, 11.5*cm],
)
tbl2.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0f766e")),
    ("TEXTCOLOR",  (0, 0), (-1, 0), HexColor("#ffffff")),
    ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE",   (0, 0), (-1, -1), 10),
    ("BOX",        (0, 0), (-1, -1), 0.5, grey),
    ("INNERGRID",  (0, 0), (-1, -1), 0.25, grey),
    ("LEFTPADDING",  (0, 0), (-1, -1), 8),
    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ("TOPPADDING",    (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))
story.append(tbl2)

# ---------- 5. MACRO / MARKET STRUCTURE LENSES ----------
p("5. Macro &amp; Market-Structure Lenses", H1)

p("5.1 USDT.D as the dominant regime filter", H2)
p(
    "Moneytaur treats <b>USDT Dominance</b> as the single most actionable macro "
    "chart for crypto. Rising USDT.D signals capital parking in stables — a "
    "bearish regime for alts. Falling USDT.D signals capital rotating out of "
    "stables — a bullish regime. Most of his alt longs require USDT.D to be "
    "breaking down or printing weakness.",
    BODY,
)

p("5.2 BTC Dominance &amp; TOTAL3", H2)
p(
    "He uses BTC.D to time rotations (BTC-led legs vs alt legs) and TOTAL3 "
    "(market cap ex-BTC &amp; ex-ETH) to read the alt-coin risk-on pulse. Alt "
    "setups improve when BTC.D rolls over while TOTAL3 holds higher-lows.",
    BODY,
)

p("5.3 Skepticism toward BTC narratives", H2)
p(
    "His critical view — that BTC is used by large players to extract fiat "
    "from retail — is not a thesis he trades directly. It's a <b>mental "
    "framing</b> that keeps him transactional rather than evangelistic, and "
    "comfortable shorting the very asset most of crypto refuses to short.",
    BODY,
)

story.append(PageBreak())

# ---------- 6. PSYCHOLOGY & BIASES ----------
p("6. Psychology &amp; Cognitive Biases", H1)
p(
    "Moneytaur's thread on biases in trading (widely reposted, including on "
    "Instagram) emphasizes that <b>your edge is mostly the absence of bias</b>. "
    "The biases he calls out most often:",
    BODY,
)
bullets([
    "<b>Confirmation bias</b> — seeking only charts/opinions that agree with "
    "your existing position. His counter: force yourself to write the bear "
    "case for your long, and the bull case for your short, before entering.",
    "<b>Recency bias</b> — over-weighting the last 3-5 candles or the last "
    "trade's outcome. One stopped trade does not invalidate a setup; one lucky "
    "winner does not validate breaking your rules.",
    "<b>Anchoring</b> — fixating on your entry price or a prior high. The "
    "market does not know or care where you got in.",
    "<b>Loss aversion / revenge trading</b> — the urge to 'win it back' after "
    "a loss. He explicitly flags this as a top account-killer.",
    "<b>FOMO</b> — chasing a move that already ran. If the level is gone, the "
    "trade is gone; wait for the next one.",
    "<b>Over-confidence after a win streak</b> — the most dangerous bias, "
    "because it scales up size right before a cluster of losses.",
])
p(
    "The practical antidote he repeats: <b>a written plan for every trade</b> "
    "— entry, invalidation, first TP, runner management — decided <i>before</i> "
    "you are in the position, when you are still rational.",
    BODY,
)

# ---------- 7. BACKTESTING & PROCESS ----------
p("7. Backtesting &amp; Deliberate Practice", H1)
p(
    "A recurring theme: most new traders refuse to backtest because it is "
    "'boring and difficult.' Moneytaur's position is that backtesting is "
    "<b>how you earn the right to trade a strategy live</b> — it is the only "
    "way to see, in concrete numbers, how the setup would have behaved over "
    "weeks and months of past data.",
    BODY,
)
p("His backtesting loop (reconstructed from his advice)", H2)
bullets([
    "Define the setup in writing — exact level criteria, trigger, stop, TP rules.",
    "Pick a representative period (bull leg, bear leg, chop) and replay bar-by-bar.",
    "Log every trade — R, outcome, what went wrong, what you'd refine.",
    "Compute hit rate, average R, max drawdown, and expectancy.",
    "Only size up live once the sample is statistically meaningful.",
])

# ---------- 8. WHAT HE AVOIDS ----------
p("8. What He Avoids", H1)
bullets([
    "<b>Chasing.</b> If price has already left the level, the trade is over.",
    "<b>Moving stops.</b> A moved stop is a new, worse trade.",
    "<b>Averaging down</b> without a pre-planned level to do so.",
    "<b>Paid signal groups</b> that ship trades without invalidation.",
    "<b>Conviction trading</b> — taking bigger size because 'this one's obvious'.",
    "<b>All-in spot-only posture</b> in ranging or bearish regimes — he "
    "prefers smaller, leveraged, refined trades in both directions.",
])

story.append(PageBreak())

# ---------- 9. A COMPOSITE TRADE, START TO FINISH ----------
p("9. A Composite Moneytaur Trade — Start to Finish", H1)
p(
    "A composite, not a specific call. This is how his rules chain together:",
    BODY,
)
bullets([
    "<b>Regime.</b> USDT.D printing lower-highs on 4H — alt risk-on bias.",
    "<b>HTF bias.</b> ETH/USDT daily reclaimed prior range low — bullish.",
    "<b>Level.</b> 4H demand zone at the old range low acts as the 'come-to' level.",
    "<b>Refine.</b> On 15m, a sweep of the local low + reclaim prints an "
    "invalidation wick 0.4% below entry.",
    "<b>Sizing.</b> 1% account risk ÷ 0.4% stop = 2.5x notional — executed "
    "on 20x-capable perp with plenty of margin headroom.",
    "<b>Management.</b> First TP at 3R closes 35%. Stop trails to BE, then "
    "behind each new 15m higher-low.",
    "<b>Re-entry.</b> If a new 15m demand forms inside the move, add using "
    "<i>realized</i> 35% profit — not fresh risk.",
    "<b>Exit.</b> Trailing stop takes the runner out. No prediction of the top.",
])

# ---------- 10. KEY LESSONS (CHEAT SHEET) ----------
p("10. Key Lessons — One-Page Cheat Sheet", H1)
bullets([
    "<b>Trade the level, not the candle.</b>",
    "<b>Refine until the stop is structurally small</b> — that is your edge.",
    "<b>Leverage is derived</b> from stop distance, not from conviction.",
    "<b>Take 35% off in-flight</b>, trail the rest, re-enter with realized P&amp;L.",
    "<b>USDT.D tells you the regime</b> — trade alts with it, not against it.",
    "<b>Every trade is a written plan</b> before you click.",
    "<b>Backtest before you scale.</b>",
    "<b>All-weather skill beats directional bet.</b>",
    "<b>Don't fight higher-timeframe trend.</b>",
    "<b>No chasing, no revenge trades, no moved stops.</b>",
])

# ---------- APPENDIX ----------
story.append(PageBreak())
p("Appendix A — Sources &amp; Methodology", H1)
p(
    "The material above was synthesized from the following public sources. "
    "No tweets were directly extracted from X/Twitter (which requires "
    "authentication) — instead, publicly indexed summaries, quotes, and "
    "third-party reposts were used:",
    BODY,
)
bullets([
    "Thread Reader App profile for @Moneytaur_ "
    "(threadreaderapp.com/user/Moneytaur_) — index of unrolled threads.",
    "<b>vadimbacalov/moneytaurproject</b> on GitHub — HTML directory of X "
    "search URLs bucketed by week from May 2021 to 2025; used to confirm "
    "posting cadence and topic continuity.",
    "<b>SheikhEl6/moneytaur-pipeline</b> on GitHub — Python template for an "
    "ingestion → ETL → enrichment → API pipeline scoped to Moneytaur data, "
    "indicating an active community archiving effort.",
    "Public search-engine snippets quoting specific Moneytaur lines on "
    "refining, leverage, R:R, USDT.D, partial TPs, and backtesting.",
    "Third-party reposts (e.g. Instagram reshare of his 'biases in trading' "
    "thread) corroborating the psychology content.",
])
p(
    "<b>Caveats.</b> (1) This is an interpretation — direct quotes are "
    "paraphrased from indexed snippets and may be phrased differently in the "
    "original threads. (2) Trading style evolves; this reflects the publicly "
    "visible cross-section through early 2026. (3) Nothing here is financial "
    "advice.",
    QUOTE,
)

p("Appendix B — Suggested Next Steps for Deeper Research", H1)
bullets([
    "Log in to X and systematically unroll the weekly threads linked from "
    "<i>moneytaurproject</i> — the richest first-party source.",
    "Subscribe to his Thread Reader App page and export full unrolls.",
    "Build a personal replay-journal in TradingView to backtest his level + "
    "refine + 35%-TP template on your preferred pairs.",
])

doc.build(story)
print(f"PDF generated: {OUT}")
