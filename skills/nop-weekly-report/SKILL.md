---
name: nop-weekly-report
description: This skill should be used when the user asks for a store summary or report — "/nop-weekly-report", "weekly report", "how did the store do this week", "monthly summary", "sales and stock overview". Builds a one-page summary of sales, bestsellers, low stock and orders needing attention from the nopCommerce store through Booster AI.
argument-hint: "[period, default last 7 days]"
---

# Store summary report

Read `${CLAUDE_PLUGIN_ROOT}/skills/booster-ai-store/SKILL.md` first. This task is read-only; it needs `reports:read` and `orders:read`.

1. **Period.** Use the period the user gave; otherwise the last 7 full days. Also fetch the same-length period before it for comparison.
2. **Collect** with as few calls as possible:
   - `sales_report` for both periods.
   - `bestsellers_report` for the period, top 10.
   - `low_stock_report`, the 10 lowest.
   - `search_orders` for orders still Pending or Processing that were placed more than 3 days ago.
3. **Write the summary** in this order:
   - One line: revenue and order count for the period, with the change against the previous period in % and absolute terms.
   - Table: top bestsellers (product, units, revenue).
   - Table: low-stock products (product, stock left) — flag any bestseller that is also low on stock, since that is lost revenue next week.
   - Orders needing attention: count, oldest first, with order number, status and age in days.
   - Three short, specific suggestions drawn only from these numbers (e.g. "Reorder X: it sold 40 and has 6 left").
4. Offer to save it as a document or to draft a message to the team. Do not change anything in the store.
