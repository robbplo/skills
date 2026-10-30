---
name: make-bot-ui
description: >-
  Use when building a custom UI (page, dashboard, buttons) that should wake a
  Grok Bot over a webhook, when the user must provide a webhook sender key, or
  when exposing that UI on Tailscale.
disable-model-invocation: true
---

# How to make a bot UI

Claude Code cannot create or receive Cursor Automation webhook routines or request a sender key through `SendToUser`. Report `Skipped in Claude Code: webhook routine. Cursor Automations and secret requests are unavailable.` Stop this workflow because the UI depends on that routine and key.
