# Investigator Prompt Template

Fill in the placeholders. Append the one category playbook `references/sources/<source>.md` for this investigator's evidence category (index: `references/source-playbook.md`). If the target code looks defensive (null checks, retry logic, timeout handling, rate limiting, feature flags, egress guards, OOM handlers), also append `references/sources/incident-postmortem.md` so the investigator runs incident-flavored queries inside its own source.

---

## The Question

> {QUESTION}

## The Code Anchor

**Target files:** {FILES_WITH_LINE_RANGES}

**Key symbols:** {SYMBOLS}

**Initial commits touching this code (most recent first):**
{COMMIT_LIST}

**PR numbers extracted from commit messages:** {PR_NUMBERS}

**Ticket IDs mentioned in commits or PR bodies (if any):** {TICKET_IDS}

## Your Assigned Source

{SOURCE_NAME}

{SOURCE_PLAYBOOK_SECTION}
