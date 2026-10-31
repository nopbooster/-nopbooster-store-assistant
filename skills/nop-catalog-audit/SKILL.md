---
name: nop-catalog-audit
description: This skill should be used when the user wants to find and fix catalogue quality problems in their nopCommerce store — "/nop-catalog-audit", "audit my products", "which products are missing SEO", "find products with no description", "clean up the catalogue". Finds gaps with Booster AI and proposes fixes as previews.
argument-hint: "[category or 'all']"
---

# Catalogue and SEO audit

Read `${CLAUDE_PLUGIN_ROOT}/skills/booster-ai-store/SKILL.md` first. Finding gaps needs `catalog:read` and `content:read`; fixing them needs `catalog:write` and/or `content:write`.

## 1. Find the gaps (read-only)

Work through the category the user named, or the whole catalogue in pages. For each product check, from `search_products` / `get_product` and `list_untranslated`:

| Check | Problem when |
|---|---|
| Short description | empty |
| Full description | empty or under about 50 words |
| Meta title | empty, or longer than about 60 characters |
| Meta description | empty, or longer than about 160 characters |
| Translations | `list_untranslated` reports missing languages |
| Published but price 0 | likely a mistake |
| Published but no category | hard for shoppers to find |

Report a summary table (check, number of products affected) and the 20 worst products. Ask which fixes the user wants before writing anything.

## 2. Propose fixes

- Write new meta titles, meta descriptions and short descriptions from the product's own name, specifications and existing description. Never invent features, materials, sizes or claims that are not in the product data.
- Match the store's existing tone and language.
- Send fixes in batches of up to 20 products with `update_seo` / `update_product`. Each batch returns a preview: show it (product, field, before, after) and apply only after the user approves that batch.

## 3. Close

Report what was changed, what was skipped and why, and what still needs a human (for example products with no data to write a description from).
