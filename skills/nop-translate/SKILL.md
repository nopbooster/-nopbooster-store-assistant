---
name: nop-translate
description: This skill should be used when the user wants missing translations filled in their nopCommerce store — "/nop-translate", "translate missing strings", "which products have no Arabic translation", "fill in the German texts". Finds untranslated content with Booster AI, drafts translations and applies them after preview.
argument-hint: "[language] [products|topics|resources]"
---

# Fill missing translations

Read `${CLAUDE_PLUGIN_ROOT}/skills/booster-ai-store/SKILL.md` first. Needs `content:read` to find gaps and `content:write` to save translations.

1. **Language.** Use the language the user named. If none, call `list_untranslated` and report the counts per language, then ask which to do first.
2. **Find what is missing** with `list_untranslated` for that language, and read the source texts with `get_localized_strings`.
3. **Translate** each string:
   - Keep product names, brand names, SKUs, codes, URLs and placeholders such as `{0}` or `%s` exactly as they are.
   - Keep HTML tags and their attributes unchanged; translate only the visible text.
   - Use the store's tone and, for right-to-left languages, the store's existing conventions.
   - If a term is ambiguous (for example a clothing size label), keep the original and list it for the user.
4. **Save in batches** of up to 50 strings with `set_localized_strings`. Show each preview as a table (key or product, source, translation) and apply only after the user approves it.
5. **Report** how many strings were translated, how many were left for a human, and any terms you kept untranslated.

Suggest a native speaker review for customer-facing pages such as checkout, returns and legal topics.
