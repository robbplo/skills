---
name: make-bot-ui
description: >-
  Use when building a custom UI (page, dashboard, buttons) that should wake a
  Grok Bot over a webhook, when the user must provide a webhook sender key, or
  when exposing that UI on Tailscale.
disable-model-invocation: true
---

# How to make a bot UI

In Claude Code, report `Skipped in Claude Code: webhook routine. Cursor Automations and secret requests are unavailable.` Stop this workflow because the UI depends on that routine and key.

In Cursor, read [the Cursor webhook procedure](references/cursor.md) and follow it. In other hosts, use the active host adapter. Do not claim the workflow ran when the host cannot create the routine and receive its wake.
