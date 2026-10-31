---
name: nop-price-update
description: This skill should be used when the user wants to change prices or other fields across many products in their nopCommerce store — "/nop-price-update", "raise prices by 5%", "set these products to 19.90", "put the summer category on sale", "publish all products in X". Prepares a bulk update through Booster AI and applies it only after preview.
argument-hint: "[what to change, e.g. 'Accessories +5%']"
---

# Bulk price and product updates

Read `${CLAUDE_PLUGIN_ROOT}/skills/booster-ai-store/SKILL.md` first. Needs `catalog:read` and `catalog:write`.

1. **Pin down the change** in one sentence and confirm it if anything is ambiguous: which products (category, search, list), which field (price, old price, published, stock-related fields the tool supports), and the rule (set to X, +/- %, +/- amount).
2. **Rounding.** For percentage changes, ask once how to round (e.g. to .90 or .99, or to 2 decimals) unless the user already said; default to 2 decimals.
3. **Select** the products with `search_products` and show the count. If it is more than 200, plan batches of 200.
4. **Preview** each batch with `bulk_update_products`: show the count, total effect (e.g. average price change), and a table of the first 10 (product, before, after). Flag anything odd: prices that would become 0 or negative, or that change by more than 50%.
5. **Apply** a batch only after the user approves that batch's preview. If the apply is refused because data changed, show the new preview.
6. **Report** what changed, and how to reverse it: the same tool with the old values, which you can prepare if asked.

For a temporary sale, if the tool supports the old-price field, suggest setting the current price as the old price so shoppers see the reduction, and note the date to revert.
