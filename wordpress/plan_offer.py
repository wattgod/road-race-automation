"""The custom training plan offer, billed every 4 weeks (race_plan_4weekly).

Single source of truth for every price and term roadielabs.com shows for the
custom plan. It replaced the one-off plan ($15 a week, one payment) on
2026-11-13 (Matti; bbs-race-dataset research/SUBSCRIPTION_DESIGN.md §8.7).

The math mirrors the checkout server exactly
(wattgod/athlete-custom-training-plan-pipeline, webhook/race_plan_subscription.py:
BLOCK_PRICE_CENTS, WEEK_PRICE_CENTS, weeks_until, payment_plan,
REFUND_WINDOW_DAYS). Pages show the offer only as the rate, "$49.99 / four
weeks": never a total, a payment count or a per-race sum (Matti, 2026-11-17,
every brand). The math stays here because the questionnaire's pay button
states the one charge made today, which is below the block price when the
race is under four weeks out. tests/test_plan_offer.py pins the fixed cases
and runs the browser copy (plan_quote_js) in Node against this module.

The TrainingPeaks marketplace plans (data/tp-race-plan-links.json) are a
different product with their own fixed prices; nothing here applies to them.
"""

from __future__ import annotations

from datetime import date

CHECKOUT_PRODUCT = "race_plan_4weekly"
BLOCK_WEEKS = 4
BLOCK_PRICE_CENTS = 4999
# Last, shorter block: block price / 4 weeks, rounded up to the cent ($12.50).
WEEK_PRICE_CENTS = -(-BLOCK_PRICE_CENTS // BLOCK_WEEKS)
REFUND_WINDOW_DAYS = 14
DELIVERY_HOURS = 24


def money(cents: int) -> str:
    """"$49.99" style, always two decimals (the server's money())."""
    cents = int(cents)
    return f"${cents // 100:,}.{cents % 100:02d}"


BLOCK_PRICE = money(BLOCK_PRICE_CENTS)                       # "$49.99"
WEEK_PRICE = money(WEEK_PRICE_CENTS)                         # "$12.50"

# ── Copy. The rate only: "/ four weeks", never "/mo" or "monthly" (13
# payments a year), and never a total or payment count (Matti, 2026-11-17).
PRICE_UNIT = "four weeks"
PRICE_LINE = f"{BLOCK_PRICE} / {PRICE_UNIT}"                 # "$49.99 / four weeks"
PRICE_LINE_UPPER = PRICE_LINE.upper()                        # "$49.99 / FOUR WEEKS"
CTA_LABEL = f"BUILD MY PLAN &mdash; {PRICE_LINE_UPPER}"
# One line that fits under a button or in a meta description.
TERMS_SHORT = (
    f"{PRICE_LINE}, one 4-week block at a time. Ends after race week. "
    "Cancel any time from your plan page."
)
REFUND_LINE = (
    f"Full refund of your first payment within {REFUND_WINDOW_DAYS} days, "
    "from your plan page."
)


def weeks_until(race_date: date, today: date) -> int:
    """Whole weeks from today to the race, a part week counting as one.
    Same rule as the server; a race today or earlier has no plan."""
    days = (race_date - today).days
    if days <= 0:
        raise ValueError("Race date must be after today")
    return -(-days // 7)


def payment_plan(weeks: int) -> dict:
    """Payments and total for ``weeks`` of plan: full 4-week blocks at the
    block price, then one shorter block at the week price. No cap, no
    minimum. Same shape as the server's payment_plan."""
    if isinstance(weeks, bool) or not isinstance(weeks, int) or weeks < 1:
        raise ValueError("A plan needs at least one week")
    full_blocks, leftover_weeks = divmod(weeks, BLOCK_WEEKS)
    payments = [BLOCK_PRICE_CENTS] * full_blocks
    if leftover_weeks:
        payments.append(WEEK_PRICE_CENTS * leftover_weeks)
    total = sum(payments)
    return {
        "weeks": weeks,
        "full_blocks": full_blocks,
        "leftover_weeks": leftover_weeks,
        "payment_count": len(payments),
        "payments_cents": payments,
        "total_cents": total,
        "total_display": money(total),
        "first_payment_cents": payments[0],
    }


def plan_quote_js() -> str:
    """Browser copy of weeks_until + payment_plan.

    Defines ``rlPlanQuote(raceDateStr, todayStr)`` returning
    {weeks, firstCents, first}, or null
    for no date, a bad date, or a race today or earlier. ``todayStr`` is for
    tests; pages omit it and the visitor's local date is used. Days are
    counted with Math.round so a DST shift (N days +/- 1 hour) can't add a
    week. The server counts from its own UTC date, so near midnight UTC the
    count can differ by one week from what a visitor far from UTC sees.
    ``first`` is the one charge made at checkout: the block price, or less
    when the race is under four weeks out. There is deliberately no total or
    payment count, so no page can show one.
    """
    return (
        "function rlPlanMoney(c){c=Math.round(c);var d=Math.floor(c/100),r=c%100;"
        "return '$'+d.toLocaleString('en-US')+'.'+(r<10?'0':'')+r;}\n"
        "function rlPlanQuote(raceDateStr,todayStr){\n"
        "  var re=/^\\d{4}-\\d{2}-\\d{2}$/;\n"
        "  if(!raceDateStr||!re.test(raceDateStr))return null;\n"
        "  var race=new Date(raceDateStr+'T00:00:00');if(isNaN(race.getTime()))return null;\n"
        "  var today=todayStr&&re.test(todayStr)?new Date(todayStr+'T00:00:00'):new Date();\n"
        "  today.setHours(0,0,0,0);\n"
        "  var days=Math.round((race-today)/86400000);if(days<=0)return null;\n"
        "  var weeks=Math.ceil(days/7);\n"
        f"  var full=Math.floor(weeks/{BLOCK_WEEKS}),left=weeks%{BLOCK_WEEKS};\n"
        f"  var first=full?{BLOCK_PRICE_CENTS}:left*{WEEK_PRICE_CENTS};\n"
        "  return {weeks:weeks,firstCents:first,first:rlPlanMoney(first)};\n"
        "}\n"
    )


# Markers around the generated quote code inside web/training-plans-form.js;
# tests/test_plan_offer.py checks the block between them equals plan_quote_js().
JS_BEGIN_MARKER = "// BEGIN rlPlanQuote: generated by wordpress/plan_offer.py plan_quote_js(), do not hand-edit"
JS_END_MARKER = "// END rlPlanQuote"

