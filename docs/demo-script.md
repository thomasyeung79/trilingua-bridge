# Demo Script — TriLingua Bridge

**Duration:** ~2 minutes  
**Audience:** Recruiters, hiring managers, software engineers  
**Goal:** Demonstrate the core value proposition — not just translation, but communication coaching

---

## Preparation

Before recording:

1. Ensure API keys are configured (OpenAI recommended for demo)
2. Clear the database or use a fresh instance
3. Set `DEPLOY_MODE = "demo"` in `.env` to show the ephemeral-storage banner
4. Open two browser tabs: one for the app, one for this script
5. Set screen resolution to 1440×900 or similar (not too wide, not too narrow)

---

## Script

### 0:00 — Intro (10 seconds)

**Narration:**

> "TriLingua Bridge is an AI communication coach for Mandarin, Cantonese, Korean, Japanese, and English. It helps you write messages that sound natural — not translated."

**Screen:** Home page. Show the hero section and language selector.

**Actions:**
- Hover over the app title briefly
- Point cursor to "5 languages" indicator

---

### 0:10 — Open Coach (15 seconds)

**Narration:**

> "The main feature is the Coach. Let me show you how it works. I'll type a real situation — I want to reply to a Korean coworker who said they're busy this weekend."

**Screen:** Navigate to Coach page.

**Actions:**
- Click "AI Chat Coach" card from Home
- Wait for Coach page to load

---

### 0:25 — Generate a reply (25 seconds)

**Narration:**

> "I set the source to auto-detect and the target to Korean. I'll type my situation and click Run."

**Screen:** Coach page with text input.

**Actions:**
- Type: "A coworker said they're busy this weekend but I want to reply in a friendly way without being pushy."
- Verify source=auto, target=한국어
- Click "Run"
- Wait for output

**Narration** (while waiting, ~5 seconds):

> "The AI generates three reply options with naturalness scores, tone analysis, and cultural notes — all in Korean."

**Screen:** AI result renders.

**Actions:**
- Scroll through the result card
- Point to the three reply options (briefly)
- Point to "Cultural Notes" section
- Point to the pronunciation guide

---

### 0:50 — Conversation Memory (20 seconds)

**Narration:**

> "Now watch this. The AI remembers our conversation. I'll follow up as if the coworker replied."

**Screen:** Still on Coach page, below the result.

**Actions:**
- Scroll down to show the Conversation History (now rendered at bottom)
- Type a follow-up: "They said '네, 다음에 봐요' — how should I respond?"
- Click Run
- Wait for output

**Narration** (while waiting):

> "The AI sees the previous four messages as context, so it knows this is a follow-up and provides a coherent next reply."

**Actions:**
- Scroll to show both conversation turns rendered in the history section

---

### 1:10 — Quick Language Swap (15 seconds)

**Narration:**

> "What if I want to switch languages mid-session? No need to go back to Home. I can swap directly."

**Screen:** Coach page, language bar.

**Actions:**
- Click ⇄ swap button (source ↔ target exchange)
- Show that Korean is now source and English is target
- Type: "Can I use this in a different language?"
- Click Run briefly (can stop early — this is just showing the swap works)

**Narration:**

> "One click swaps source and target. The conversation memory resets automatically when the language changes, so old context doesn't pollute new output."

---

### 1:25 — History page (15 seconds)

**Narration:**

> "Every AI result is saved automatically. The History page lets me search, filter by mode or language, and export as CSV."

**Screen:** Navigate to History page.

**Actions:**
- Click "History" from the workspace rail
- Show the filter dropdowns (mode, source, target)
- Show search input
- Show the CSV download button

---

### 1:40 — Review Book & Vocab Bank (15 seconds)

**Narration:**

> "Useful results can be saved to the Review Book for spaced revision, or added to the Vocab Bank as personal phrases."

**Screen:** Navigate to Review Book, then Vocab Bank.

**Actions:**
- Click "Review Book" from the workspace rail
- Show a saved item (if any exist from earlier demo)
- Click "Vocab Bank" and show the manual add form

**Narration:**

> "This turns the app from a one-shot translator into a learning system — your progress compounds over time."

---

### 1:55 — Outro (5 seconds)

**Narration:**

> "That's TriLingua Bridge. The code is on GitHub — contributions welcome."

**Screen:** Home page or a final card with the GitHub URL.

---

## Recording Tips

| Tip | Why |
|-----|-----|
| **Use a quiet room** | Voiceover quality matters more than video quality |
| **Record at 1440×900** | Wide enough to show columns, not so wide that text is tiny |
| **Pause between steps** | Easier to edit later. A 1-second gap = clean cut point |
| **Don't worry about AI latency** | Add a "speedup" note in the video if waiting is awkward |
| **Show cursor movement** | Don't jump — move the cursor purposefully between elements |
| **Close other tabs** | Keep the browser chrome clean (bookmarks bar hidden if possible) |

## What to show (and what to skip)

| Show | Skip |
|------|------|
| Coach with reply options | Account creation flow |
| Conversation memory | Grammar / Natural / Vocabulary pages |
| Quick Language Swap | Settings page |
| History page with filters | Screenshot analysis |
| Review Book / Vocab Bank | Learning Report chart |

The demo should feel like a **product walkthrough**, not a code review. Focus on the user experience and the problem it solves.

---

*Script ends.*
