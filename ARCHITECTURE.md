# Architecture — Layered Output

How the Research Intelligence Engine produces and presents results.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│           SHARED MEMORY (sessions/[name]/journal.md)         │
│     Problem │ Hypotheses │ Synthesis │ Round Log (~90 lines) │
└─────────────────────────────┬───────────────────────────────┘
        ↑ read/write          │          ↑ read/write
        │                     │          │
┌───────┴───────┐      ┌─────┴──────┐   ┌┴────────────┐
│     DEEP      │      │   CRITIC   │   │  RESEARCHER │
│    ANALYST    │      │            │   │             │
│   (Opus 4.5)  │      │ ~150-250   │   │ ~300-450    │
│               │      │   lines    │   │   lines     │
│ ~150-250      │      │            │   │             │
│   lines       │      │ -Adversary │   │ - PubMed    │
│               │      │ -Steel-man │   │ - bioRxiv   │
│ - Perspective │      │ -Find gaps │   │ - OpenAlex  │
│   framework   │      │ -Challenge │   │ - Web search│
│ - Scientific  │      │            │   │             │
│   inquiry     │      │            │   │             │
└───────┬───────┘      └─────┬──────┘   └──────┬──────┘
        │                    │                  │
        │   all write to     │   round-N.md     │
        └────────────────────┼──────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │         round-N.md           │
              │     (full agent output)      │
              │       ~800-900 lines         │
              └──────────────┬───────────────┘
                             │
                             │  Synthesizer reads
                             │  round-N.md + journal.md
                             ▼
                   ┌─────────────────────┐
                   │    SYNTHESIZER      │
                   │    (Opus 4.5)       │
                   │                     │
                   │  Writes TWO outputs │
                   └──┬──────────────┬───┘
                      │              │
            ┌─────────┘              └──────────┐
            ▼                                   ▼
 ┌─────────────────────┐          ┌──────────────────────────┐
 │  round-N-brief.md   │          │  Synthesizer Detail      │
 │  (NEW FILE)         │          │  (appended to            │
 │  ~55 lines          │          │   round-N.md)            │
 │                     │   ◄───►  │                          │
 │  Student opens      │  cross-  │  Student opens for       │
 │  FIRST to decide    │  linked  │  DEPTH when curious      │
 └──────────┬──────────┘          └──────────────────────────┘
            │
            │  Orchestrator presents
            │  brief contents
            ▼
    ┌───────────────┐
    │    STUDENT    │
    │               │
    │  Reads ~55    │
    │  lines        │
    │  Chooses next │
    │  step         │
    └───────┬───────┘
            │
            │ decision
            ▼
    ┌───────────────┐        ┌─────────────────┐
    │  ORCHESTRATOR │───────►│ REPORT GENERATOR │
    │               │  (on   │   (Opus 4.5)     │
    │  Routes to    │  conv- │                   │
    │  next round   │  erge) │  Produces         │
    │  or converge  │        │  REPORT.md        │
    └───────────────┘        └─────────────────┘
```

---

## The Two-File Structure

Each round produces a **pair** of cross-linked files:

```
                 round-N-brief.md                    round-N.md
            ┌─────────────────────┐          ┌─────────────────────────┐
            │                     │          │                         │
            │  # Executive Brief  │          │  ## Agent Contributions │
            │  (3 sentences)      │          │    Critic output        │
            │                     │          │    Deep Analyst output  │
            │  ## What Happened   │          │    Researcher output    │
            │  (3 x 1 sentence)   │          │                        │
            │                     │          │  ─────────────────────  │
            │  ## Key Findings    │          │                        │
            │  (3-4 findings)     │          │  ## Synthesizer Detail │
            │                     │          │    Active Tensions     │
            │  ## Hyp. Movement   │          │    Evidence Quality    │
            │  (changes only)     │          │    Critic's Verdict    │
            │                     │          │    (Full)              │
            │  ## Critic's Verdict│          │                        │
            │  (1 sentence)       │          │  > Brief: round-N- ───┼──┐
            │                     │          │    brief.md            │  │
            │  ─────────────────  │          └─────────────────────────┘  │
            │                     │                    ▲                  │
            │  ## Your Decision   │                    │                  │
            │    Reflect First    │                    │ cross-reference  │
            │    (3 prompts)      │                    │                  │
            │    Options A-E      │                    │                  │
            │    ("Develops:")    │                    │                  │
            │                     │                    │                  │
            │  > Full delibera- ──┼────────────────────┘                  │
            │    tion: round-N.md │ ◄─────────────────────────────────────┘
            │                     │
            └─────────────────────┘

              ~55 lines                        ~800-900 lines
              DECISION-MAKING                  REFERENCE / LEARNING
```

---

## Student Reading Path

```
  1. OPEN BRIEF           2. DECIDE               3. (OPTIONAL) DEPTH
  ┌────────────────┐      ┌──────────────────┐    ┌────────────────────┐
  │ round-N-       │─────►│ Choose A/B/C/D/E │───►│ round-N.md         │
  │ brief.md       │      │                  │    │                    │
  │                │      │ State WHY in     │    │ Full agent         │
  │ ~55 lines      │      │ 1-2 sentences    │    │ reasoning          │
  │                │      │                  │    │ ~800-900 lines     │
  │ Everything     │      │                  │    │                    │
  │ needed to      │      │                  │    │ HOW they got       │
  │ decide         │      │                  │    │ there — where the  │
  │                │      │                  │    │ learning lives     │
  └────────────────┘      └──────────────────┘    └────────────────────┘
```

---

## Session File Structure

```
sessions/[session-name]/
│
├── journal.md              Always read by agents (~90 lines)
│                           Hypotheses, synthesis, round log
│
├── round-1.md              Round 1 full agent output
├── round-1-brief.md        Round 1 executive brief + checkpoint
│
├── round-2.md              Round 2 full agent output
├── round-2-brief.md        Round 2 executive brief + checkpoint
│
├── round-N.md              Round N full agent output
├── round-N-brief.md        Round N executive brief + checkpoint
│
├── evidence.md             Running evidence table (append-only)
│
└── REPORT.md               Final polished report (after convergence)
```

---

## Brief Contents (55-line budget)

| Section | Content | Purpose |
|---------|---------|---------|
| **Executive Brief** | 3 sentences | What happened, what's established, what decision this creates |
| **What Happened** | 1 sentence per agent | Quick orientation |
| **Key Findings** | 3-4 findings with confidence | Most decision-relevant results |
| **Hypothesis Movement** | Changed hypotheses only | What shifted and why |
| **Critic's Verdict** | Converge? + top concern | Go/no-go signal |
| **Reflect First** | 3 selected prompts | Metacognitive pause before deciding |
| **Options A-E** | Each with "Develops:" | What each choice teaches |

---

## Detail Contents (appended to round-N.md)

| Section | Content | Purpose |
|---------|---------|---------|
| **Active Tensions** | Full table with status and impact | Unresolved debates worth tracking |
| **Evidence Quality** | Strongest, weakest, key gap | Where the evidence base stands |
| **Critic's Verdict (Full)** | Blocking concerns with descriptions | Complete convergence assessment |

---

## Agent Budget Guidelines

| Agent | Budget | Rationale |
|-------|--------|-----------|
| Critic | ~150-250 lines | 5-step framework is the value |
| Deep Analyst | ~150-250 lines | Analytical depth is the value |
| Researcher | ~300-450 lines | Full citations are the audit trail |
| Synthesizer (brief) | **55 lines hard limit** | Compression layer — constrain strictly |
| Synthesizer (detail) | No hard limit | Appended to round file for reference |

---

## Design Rationale

1. **Separate file, not "checkpoint at top"** — A 55-line file feels different from a 1000-line file. Psychological weight matters.
2. **3 reflection prompts, not 5** — Prevents checklist fatigue. Synthesizer picks the 3 most relevant to THIS round.
3. **"Develops:" annotations kept** — Compressed to 10 words max. The distinctive pedagogical feature.
4. **Agent summaries: 1 sentence each** — Students who want more open the detail file.
5. **Tensions + Evidence Quality moved to detail** — Important context but not decision-relevant.
6. **Hypothesis table shows only changes** — Unchanged hypotheses get a single-line note. Full table lives in journal.md.
7. **Soft budgets for agents, hard budget for brief** — Agent depth is the value; the brief is the compression layer.
