# NopBooster Store Assistant

Run your nopCommerce store from Claude. Ask for last week's sales, find orders that are stuck, audit your catalogue for missing SEO, fill in missing translations or update prices in bulk, in plain English. Every change is shown to you as a before-and-after preview, and nothing is written until you approve it.

The Store Assistant connects Claude to the **[MCP Server (Booster AI)](https://www.nopbooster.com/nopcommerce-mcp-server-booster-ai)** plugin on your own store, and adds ready-made tasks on top of it.

## What you need

- A nopCommerce store (4.60, 4.70, 4.80 or 4.90) on a public **https** address.
- The **MCP Server (Booster AI)** plugin installed on it, with a licence or the [free trial](https://www.nopbooster.com/mcp-server-booster-ai-trial-version).
- An **API key** created under **MCP Server > API keys** in your nopCommerce admin. Start with read-only scopes (`catalog:read`, `orders:read`, `reports:read`, `content:read`) and add write scopes when you are ready.

## Install

- **Claude Code:**
  ```text
  /plugin marketplace add nopbooster/-nopbooster-store-assistant
  /plugin install nopbooster-store-assistant@nopbooster-store
  ```
  Once it is approved in the Claude plugin directory, you can also install it from **/plugin → Discover**.
- **Claude app:** add it from the Plugins directory once listed, or add this repository as a marketplace in the Plugins area.

## Setup

1. Install this plugin.
2. When asked, enter:
   - **Store address**: e.g. `https://www.example.com` (no trailing slash)
   - **Booster AI API key**: the key from step 3 above. It is stored in your system's secure credential store, not in a settings file.
3. Ask Claude: *"Show last week's sales and my five lowest-stock products."*

Using Claude on the web or the desktop app? You can also connect the store as a custom connector with OAuth sign-in, as described on the [product page](https://www.nopbooster.com/nopcommerce-mcp-server-booster-ai).

## What's included

| | Name | What it does | Scopes needed |
|---|---|---|---|
| 🧠 | **booster-ai-store** | Loads automatically. Teaches Claude the store's tools, scopes, previews and limits so it works safely. | — |
| 📊 | **/nop-weekly-report** | Sales vs the previous period, bestsellers, low stock and orders needing attention, on one page. | `reports:read`, `orders:read` |
| 🔎 | **/nop-catalog-audit** | Finds products with missing descriptions, SEO titles, meta descriptions, translations or categories, and proposes fixes. | `catalog:read`, `content:read` (+ write to fix) |
| 🌍 | **/nop-translate** | Fills missing translations for products, topics and text resources, keeping names, codes and HTML intact. | `content:read`, `content:write` |
| 📦 | **/nop-stuck-orders** | Lists orders stuck in Pending or Processing, grouped by likely cause, and updates them on your say-so. | `orders:read` (+ `orders:write`) |
| 💲 | **/nop-price-update** | Bulk price and product changes by category or search, with rounding rules and batch previews. | `catalog:read`, `catalog:write` |

## Safety

- **You approve every change.** Product, order status, translation, topic and SEO changes come back as a preview with a single-use confirmation that expires after 10 minutes. If the data changed in the meantime, the change is refused and a new preview is shown.
- **Nothing can be deleted.** The server has no delete tools.
- **Customer data stays masked** (e-mail, phone, addresses) unless your key has the `customers:pii` scope.
- **Scoped, revocable keys.** Claude only sees the tools your key allows. Revoke a key under MCP Server > API keys and access stops immediately.
- **Your data.** Booster AI runs on your own server and sends nothing to NopBooster. What Claude reads from your store is part of your conversation with Claude and is handled under your Anthropic account terms.

## Testing

The plugin is tested end to end against a stand-in for the Booster AI server (`tests/mock_booster_ai.py`) that behaves like the real one: API-key check, previews with single-use confirmation tokens, no delete tools.

- `python tests/smoke_test.py` checks the stand-in server itself (runs in CI on every push).
- `python tests/e2e_test.py` runs Claude Code with this plugin against it and checks what reached the server: read-only report, preview without approval, apply after approval with the price actually changed, and a wrong key handled without invented figures. Needs Claude Code signed in and `pip install "mcp>=1.20,<2" uvicorn`.

## Support

[nopbooster.com](https://www.nopbooster.com/contactus) · sales@nopbooster.com. Please include your nopCommerce version, the plugin version and which Claude app you use.

## License

MIT © Creatrix Technologies (NopBooster). nopCommerce is a trademark of MazSoft LLC. Claude is a trademark of Anthropic, PBC. This plugin is independent and not affiliated with or endorsed by either.
