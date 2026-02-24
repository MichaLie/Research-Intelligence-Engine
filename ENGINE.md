# Research Intelligence Engine

A deliberative multi-agent research system that runs natively in Claude Code. Claude acts as the Orchestrator, spawning Opus 4.5 subagents via the Task tool. All state persists in your project folder.

---

## Quick Commands

| Command | Action |
|---------|--------|
| **"Call the engine"** | Start new investigation |
| **"Continue [topic]"** | Resume existing session |
| **"List sessions"** | Show all investigations |
| **"Analyze [topic]"** | Start new investigation (alias) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           SHARED MEMORY (sessions/[name]/journal.md)        │
│     Problem │ Analysis Log │ Evidence │ Open Questions      │
└─────────────────────────────┬───────────────────────────────┘
        ↑ read/write          │          ↑ read/write
        │                     │          │
┌───────┴───────┐      ┌──────┴─────┐   ┌┴────────────┐
│     DEEP      │      │   CRITIC   │   │  RESEARCHER │
│    ANALYST    │      │ (Opus 4.5) │   │  (Opus 4.5) │
│   (Opus 4.5)  │      │            │   │             │
│               │      │ -Adversary │   │ - PubMed    │
│ - Perspective │      │ -Steel-man │   │ - bioRxiv   │
│   framework   │      │ -Find gaps │   │ - OpenAlex  │
│ - Scientific  │      │ -Challenge │   │ - Web search│
│   inquiry     │      │            │   │             │
└───────────────┘      └────────────┘   └─────────────┘
        │                     │                │
        └─────────────────────┼────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │    SYNTHESIZER    │
                    │    (Opus 4.5)     │
                    │                   │
                    │ - Distill round   │
                    │ - Map tensions    │
                    │ - Frame decisions │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │ REPORT GENERATOR  │
                    │    (Opus 4.5)     │
                    │                   │
                    │ - Compile report  │
                    │ - Format findings │
                    │ - Cite sources    │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │    ORCHESTRATOR   │
                    │   (Claude Code)   │
                    │                   │
                    │ - Routes tasks    │
                    │ - Manages rounds  │
                    │ - Human checkpoint│
                    └─────────┬─────────┘
                              │
                           [HUMAN]
                     (approves/redirects)
```

---

## How to Operate

### 1. Initialize
- Read agent definitions from `agents/`
- Check `sessions/index.md` for existing sessions

### 2. For New Investigations
- Generate session name: `YYYY-MM-slug` (e.g., `2024-01-sleep-cognition`)
- Create session folder: `sessions/[session-name]/`
- Initialize `journal.md` with problem space
- Run the deliberation loop

### 3. For Continuing Investigations
- Load existing `journal.md`
- Review current state (rounds, status, open questions)
- Resume or extend the deliberation loop

### 4. Update Registry
- Always update `sessions/index.md` when:
  - Creating a new session
  - Completing a round
  - Changing status (active → converged)

---

## Session Naming Convention

Format: `YYYY-MM-slug`

Examples:
- `2024-01-sleep-cognition`
- `2024-01-mrna-vaccines`
- `2024-02-intermittent-fasting`

The slug should be lowercase, hyphen-separated, and descriptive.

---

## The Deliberation Loop

```
1. INITIALIZE
   - Read/create journal.md
   - Log the research question

2. PHASE 1: STRUCTURING (Round 1)
   - Spawn Deep Analyst → reframe problem, initial perspective rotation
     - REQUIRED: Deep Analyst MUST produce a structured Hypothesis Table
       with Support Criteria AND Refutation Criteria columns
   - Spawn Researcher → initial literature search (PubMed, OpenAlex, bioRxiv)
   - Update journal.md
     - Orchestrator copies Deep Analyst's Hypothesis Table into journal.md
       BEFORE spawning Synthesizer (ensures hypotheses are tracked from Round 1)
   - CHECKPOINT → Spawn Synthesizer → produce brief + detail files
   - HUMAN APPROVAL → Present `round-1-brief.md` to student, await decision

3. PHASE 2: ITERATION (Rounds 2-N)
   For each round:
   - Spawn Critic → find weaknesses, gaps, counter-arguments
   - Spawn Deep Analyst → address weak points, deepen specific lenses
   - Spawn Researcher → targeted searches for identified gaps
   - Update journal.md
   - CHECKPOINT → Spawn Synthesizer → produce brief + detail files
   - HUMAN APPROVAL → Present `round-N-brief.md` to student with options:
     - Continue to next round (address Critic's concerns)
     - Deep dive on specific topic
     - Converge and synthesize
     - Redirect investigation
     - Stop

4. PHASE 3: SYNTHESIS (when human approves convergence)
   - Compile final output
   - Update journal.md status to "converged"
   - Update sessions/index.md
   - Present final synthesis to user

5. PHASE 4: REPORT GENERATION
   - Spawn Report Generator → read all session files
   - Produce polished REPORT.md in session folder
   - Present report location to user
```

### Human Checkpoint Flow

After each round, the Synthesizer produces **two files**:
- `round-N-brief.md` — Executive brief + checkpoint (~55 lines). This is what the Orchestrator presents to the student.
- Synthesizer Detail appended to `round-N.md` — Active Tensions, Evidence Quality Assessment, full Critic's Verdict.

The brief contains:
- 3-sentence executive summary
- Key findings with confidence levels
- Hypothesis movement (changes only)
- Critic's convergence verdict
- Decision options with "Develops:" annotations
- 3 selected reflection prompts

**The Orchestrator presents `round-N-brief.md` contents to the student.** The investigation does not continue without explicit approval.

This ensures:
- Human remains in control of the investigation direction
- No wasted rounds on paths the human doesn't value
- Opportunity to redirect based on emerging insights
- Clear decision points with full context
- Brief is self-contained for decision-making; detail file available for depth

---

## Agent Spawning Pattern

When spawning agents, use the Task tool with:
- `subagent_type`: "general-purpose"
- `model`: "opus" (ensures Opus 4.5)

Each agent should:
1. Read their role definition from `agents/[agent].md`
2. Read session state from `journal.md` (summary + hypotheses + current synthesis)
3. Read previous round from `round-[N-1].md` (if exists)
4. Perform their specific task
5. Write their analysis to `round-[N].md` (current round file)
6. Update `evidence.md` with any new sources found
7. Update `journal.md` hypothesis table and synthesis if needed

### Role Boundaries

Each agent has a defined scope. Do not allow agents to drift outside their role:

| Agent | CAN DO | CANNOT DO |
|-------|--------|-----------|
| Deep Analyst | Analyze, reframe, hypothesize, map tensions, navigate abstraction, reference evidence from Researcher | Search literature, run Python scripts, run WebSearch, cite sources not in evidence.md |
| Researcher | Search databases, evaluate sources, extract data, assign quality ratings, update evidence.md | Generate hypotheses, challenge arguments, add new analysis |
| Critic | Challenge claims, steel-man counter-arguments, audit assumptions and evidence quality | Search for new evidence, run database queries |
| Synthesizer | Distill round output, map tensions, frame decisions, present checkpoint to human | Add new analysis, search for evidence, generate hypotheses |
| Report Generator | Compile findings, format report, cite sources from evidence.md | Add new analysis, new evidence, or new hypotheses |

---

## Session File Structure

Each session folder contains:

```
sessions/[session-name]/
├── journal.md              # Summary file (always read by agents, ~90 lines)
│                           # Contains: problem space, hypotheses, open questions,
│                           # current synthesis, status
│
├── round-1.md              # Round 1 full agent output
├── round-1-brief.md        # Round 1 executive brief + checkpoint (~55 lines)
├── round-2.md              # Round 2 full agent output
├── round-2-brief.md        # Round 2 executive brief + checkpoint (~55 lines)
├── round-N.md              # Round N full agent output
├── round-N-brief.md        # Round N executive brief + checkpoint (~55 lines)
│
├── evidence.md             # Running evidence table (updated each round)
│
└── REPORT.md               # Final polished report (generated after convergence)
```

**Why this structure:**
- `journal.md` stays small (~2-3k tokens) - agents always read it
- `round-N-brief.md` is the student's primary reading — self-contained for decision-making (~55 lines)
- `round-N.md` is the reference document — full agent reasoning for depth
- The brief references the detail; the detail references the brief
- `evidence.md` is the shared evidence base - append-only
- Prevents context overflow on long investigations

**Agent reading pattern:**
- Always read: `journal.md` + `agents/[role].md`
- For Round 1: No previous round to read
- For Round 2+: Also read `round-[N-1].md` for continuity
- **Synthesizer writes two files:** `round-[N]-brief.md` (new file) AND appends Synthesizer Detail to `round-[N].md`

---

## Orchestrator Pre-Round Checklist

**Before spawning agents for any round, the Orchestrator MUST verify:**

1. **`evidence.md` exists** — If not, create it from `EVIDENCE_TEMPLATE` in `config.py`
2. **`round-[N].md` initialized** — Create from `ROUND_TEMPLATE` in `config.py`
3. **`journal.md` "Current Round" updated** — Set to the current round number

**After each round completes (before presenting checkpoint to human):**

4. **`evidence.md` updated** — Verify Researcher added all cited sources; if not, flag the gap
5. **`journal.md` Round Log updated** — Add row to the Round Log table with agents, outcome, and file reference
6. **Hypothesis table current** — Verify journal.md hypothesis table reflects any new or updated hypotheses from Deep Analyst (including Refutation Criteria column)
7. **Present `round-[N]-brief.md` to student** — After Synthesizer completes, present the brief file contents to the student (not the full round file)

---

## Convergence Criteria

The investigation converges when:
1. Critic finds no new substantial issues
2. Key hypotheses have been adequately tested
3. Open questions are either answered or identified as requiring empirical research
4. Evidence collected supports a coherent synthesis

### Guardrails

From `config.py`:
- **MAX_DELIBERATION_ROUNDS = 5**: Force convergence if not reached naturally
- **MIN_ROUNDS_BEFORE_CONVERGENCE = 2**: Ensure at least 2 rounds before allowing convergence

---

## File Locations

| File | Purpose |
|------|---------|
| `ENGINE.md` | This file - operating instructions |
| `sessions/index.md` | Registry of all sessions |
| `sessions/[name]/journal.md` | Summary: problem space, hypotheses, synthesis |
| `sessions/[name]/round-N.md` | Full agent output for round N |
| `sessions/[name]/round-N-brief.md` | Executive brief + checkpoint for round N (~55 lines) |
| `sessions/[name]/evidence.md` | Running evidence table |
| `sessions/[name]/REPORT.md` | Final polished report (after convergence) |
| `agents/deep_analyst.md` | Deep Analyst role & frameworks |
| `agents/critic.md` | Critic role & instructions |
| `agents/researcher.md` | Researcher role & search methods |
| `agents/synthesizer.md` | Synthesizer role & checkpoint format |
| `agents/report_generator.md` | Report Generator role & output template |
| `skills/*.py` | API helpers for literature search |
| `config.py` | Settings and API endpoints |

---

## Journal Structure Template

See individual session `journal.md` files for the full template. Key sections:
- Problem Space
- Analysis Log (by round)
- Evidence Collected
- Hypotheses
- Open Questions
- Current Synthesis
- Final Output (when converged)
