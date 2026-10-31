---
name: nop-stuck-orders
description: This skill should be used when the user wants to find and handle orders that are not moving — "/nop-stuck-orders", "which orders are stuck", "orders pending too long", "clean up processing orders". Lists stuck orders from the nopCommerce store through Booster AI and, on approval, updates their status or adds notes.
argument-hint: "[days, default 3]"
---

# Stuck orders

Read `${CLAUDE_PLUGIN_ROOT}/skills/booster-ai-store/SKILL.md` first. Finding orders needs `orders:read`; updating them needs `orders:write`.

1. **Find** with `search_orders`: orders in Pending or Processing placed more than N days ago (default 3). Include the payment and shipping status if the tool returns them.
2. **Show** a table, oldest first: order number, placed, age (days), order status, payment status, shipping status, total. Customer details stay masked unless the key allows otherwise.
3. **Group** them by likely cause, using only what the data shows:
   - Paid but not shipped → needs fulfilment.
   - Not paid after several days → payment follow-up or cancellation decision.
   - Shipped but still Processing → status probably just needs updating.
4. **Act only on instruction.** For each group the user wants handled:
   - Status change: `update_order_status` → show the preview → apply after approval.
   - Internal note (applied immediately, visible only to staff): `add_order_note`.
   - Customer-visible note: say clearly that it e-mails the customer, show the preview, apply after approval.
5. **Report** what changed per order. Never change payment status or cancel an order unless the user explicitly asks for that specific order.
