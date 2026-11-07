---
name: booster-ai-store
description: This skill should be used whenever the user works with their nopCommerce store through their store's MCP Server (Booster AI) connection — questions about sales, orders, products, stock, customers, translations, topics or SEO ("how did we sell last week", "which orders are stuck", "update these prices", "what's missing a translation"). It explains the tools, scopes, previews and limits so changes are made safely.
---

# Working with a nopCommerce store through Booster AI

The store's tools come from its own MCP Server (Booster AI) plugin at `<store>/mcp/admin`, which the user connects to Claude themselves (usually named `booster-ai`, as a Claude Code MCP server or a custom connector in the Claude app). This plugin does not include the connection.

If none of the store tools below are available, the store is not connected yet: say so, and point the user to the Setup section of the plugin's README (Claude Code: `claude mcp add --transport http booster-ai https://<store>/mcp/admin --header "Authorization: Bearer <api key>"`; Claude app: add `https://<store>/mcp/admin` as a custom connector). Never ask the user to paste their API key into the chat. Everything below comes from how that plugin behaves; when a tool's schema (from the server's tool list) disagrees with this file, follow the schema.

## Tools and scopes

The key only exposes tools for the scopes it was given. If a tool the task needs is missing, tell the user which scope to add to the key under **MCP Server > API keys** in their nopCommerce admin, rather than trying another route.

| Area | Read tools (scope) | Write tools (scope) |
|---|---|---|
| Catalogue | `search_products`, `get_product`, `list_categories` (`catalog:read`) | `create_product`, `update_product`, `bulk_update_products` (`catalog:write`) |
| Orders | `search_orders`, `get_order` (`orders:read`) | `update_order_status`, `add_order_note` (`orders:write`) |
| Customers | `find_customer` (`customers:read`); `get_customer_orders` (`customers:read` + `orders:read`) | — |
| Content | `get_localized_strings`, `list_untranslated` (`content:read`) | `set_localized_strings`, `update_topic`, `update_seo` (`content:write`) |
| Reports | `sales_report`, `bestsellers_report`, `low_stock_report` (`reports:read`) | — |

There are no delete tools. Never suggest that something can be deleted through this connection.

## Changes: always preview, then confirm

1. A write tool called without a confirmation returns a **preview** with before and after values and a single-use confirmation token valid for **10 minutes**.
2. Show the preview to the user as a short table (item, field, before, after). For bulk changes, show the count plus the first 10 rows and say how many more there are.
3. Apply only after the user clearly approves **that** preview, by calling the tool again with the token.
4. If the apply is refused because the data changed or the token expired, say so and show the new preview. Never retry an apply on your own.
5. One preview per logical change. Do not chain a second write before the user has approved the first.

Internal order notes are added immediately (no preview). A customer-visible order note is previewed first because it sends the customer an e-mail: say that before asking for approval.

## Limits

- About 60 calls per minute per key: batch reads with filters instead of calling `get_product` item by item when a search can return what is needed.
- Bulk tools take at most 200 items per call: split larger changes into batches, each with its own preview and approval.
- Each call times out after 30 seconds: narrow date ranges or filters if a report times out.

## Personal data

Customer e-mail, phone and addresses are masked unless the key has `customers:pii`. Work with masked values; do not ask the user to add `customers:pii` unless the task truly needs contact details, and then explain why.

## Answering well

- Lead with the answer and the number ("Sales last week: 18,420 USD from 96 orders, up 12% on the week before"), then a compact table.
- Use the store's currency and dates as returned; say which date range you used.
- When a question is ambiguous (which week, gross or net), pick the store's usual meaning, say which you chose, and offer the other.
- If a tool errors with an authorisation message, the key is missing, expired, revoked or the licence has lapsed: tell the user what the server said and where to fix it (MCP Server > API keys, or MCP Server > Configure for the licence).
