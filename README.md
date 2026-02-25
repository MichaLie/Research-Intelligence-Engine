# Research Intelligence Engine

A multi-agent AI system that teaches research judgment. AI agents search, analyze, and challenge — you decide what matters, when to push deeper, and when to stop. Every checkpoint is a deliberate exercise in scientific reasoning under uncertainty.

> **This is a proof-of-concept designed to run inside Claude Code.** There is no Python orchestrator — Claude Code reads [ENGINE.md](ENGINE.md) and acts as the orchestrator directly. The "code" is prompt architecture: agent definitions, templates, and operating instructions that an LLM follows. This is deliberate. We're testing whether well-structured natural language instructions can reliably drive a multi-agent research loop. For known production gaps (TLS, retry logic, pagination, tests), see [TECH_DEBT.md](TECH_DEBT.md).

## What It Does

The Research Intelligence Engine conducts structured research investigations using specialized AI agents that:

- **Search** PubMed, OpenAlex, and bioRxiv systematically
- **Analyze** findings from multiple perspectives
- **Challenge** conclusions through adversarial review
- **Synthesize** evidence with explicit confidence levels
- **Produce** publication-ready research reports

## Quick Start

In Claude Code, simply say:

```
Call the engine
```

Then provide your research question when prompted.

## Commands

| Command | What It Does |
|---------|--------------|
| `Call the engine` | Start a new investigation |
| `Continue [topic]` | Resume an existing session |
| `List sessions` | Show all investigations |

## What You Get

After 2-4 rounds of deliberation, you receive:

1. **REPORT.md** - Polished research report with:
   - Executive summary
   - Key findings with confidence levels
   - Hypothesis rankings (Supported/Rejected/Unresolved)
   - Evidence quality assessments
   - Experimental predictions
   - Properly formatted references

2. **Full transparency** - All reasoning traces in round files; executive briefs (~55 lines) for quick decisions

## Example Output

Run your first investigation to generate example output in `sessions/`. Each round produces a brief (~55 lines) and a detail file — see [ARCHITECTURE.md](ARCHITECTURE.md) for the full output structure.

## How It Works

```
You → Research Question
         ↓
    [Round 1: Structuring]
    Deep Analyst → Reframes question, generates hypotheses
    Researcher   → Searches literature databases
         ↓
    [Rounds 2-N: Iteration]
    Critic       → Challenges findings, identifies gaps
    Deep Analyst → Addresses weaknesses
    Researcher   → Targeted evidence gathering
         ↓
    [Human checkpoint after each round]
         ↓
    [Convergence]
    Report Generator → Polished REPORT.md
         ↓
You ← Research Report
```

## Pedagogical Approach

This system is designed to **teach research judgment**, not just deliver literature summaries. The AI agents do the searching and structured analysis; the human practices the hardest skills in research — deciding what matters, when to push deeper, and when to stop.

### Design Principles

**1. The checkpoint is the curriculum.** After each round, the student faces a genuine decision: continue, dive deeper, converge, redirect, or stop. There is no "correct" answer. The system provides evidence and framing; the student exercises judgment. This is deliberate — research skill develops through repeated, reasoned decision-making under uncertainty, not through passive reading.

**2. Make the thinking visible.** Every agent output is labeled with the framework being applied and *why* it matters. When the Critic runs a Steel-Manning analysis, the output explains what steel-manning is and why it strengthens rather than weakens your position. When the Deep Analyst navigates abstraction levels, the output explains how cross-level connections reveal hidden mechanisms. Students don't just see conclusions — they see the reasoning patterns that produced them.

**3. Every option teaches something different.** Each checkpoint option includes a "Develops:" annotation explaining what skill that choice builds:
- *Continue* develops tolerance for sitting with unresolved tension
- *Deep dive* develops the skill of identifying which uncertainties matter most
- *Converge* develops recognizing when further rounds won't change the picture
- *Redirect* develops intellectual flexibility
- *Stop* develops recognizing sunk cost

These annotations make the pedagogical intent explicit. Students learn to choose *for reasons*, not by default.

**4. Reflection before action.** Each checkpoint includes 3 targeted reflection prompts (selected from a menu of 5) that force a metacognitive pause: *Is the evidence strong enough? Have all hypotheses been tested fairly? Am I seeing genuine progress or just spinning?* The prompts rotate across rounds to prevent checklist fatigue.

**5. Layered output respects cognitive load.** Each round produces two files: a brief (~55 lines) for decision-making and a detail file (~800-900 lines) for depth. The brief contains everything needed to decide. The detail file is where the deeper learning lives — students choose when they're ready for it. This prevents the "1000-line wall of text" problem where important insights get buried and students disengage.

**6. Adversarial design teaches epistemic humility.** The Critic agent is not a rubber stamp. It steel-mans counter-arguments, audits assumption stacks, and blocks premature convergence. Students learn that having their conclusions challenged is a feature, not a failure — and that surviving rigorous challenge is what makes conclusions trustworthy.

### What Students Practice

| Skill | How the System Develops It |
|-------|---------------------------|
| Evidence evaluation | Quality ratings, evidence hierarchy, counter-evidence searches |
| Hypothesis reasoning | Explicit support/refutation criteria, confidence calibration |
| Decision under uncertainty | Checkpoint choices with incomplete information |
| Metacognition | Reflection prompts, "state WHY" requirement |
| Knowing when to stop | Convergence criteria, diminishing returns recognition |
| Intellectual honesty | Adversarial review, steel-manning, assumption audits |

---

## Limitations

Be aware of what this system **cannot** do:

- **No primary data analysis** - Literature review only
- **No database queries** - Cannot query scRNA-seq, proteomics databases directly
- **AI synthesis** - May miss nuanced domain knowledge
- **Source access** - Cannot read full-text PDFs, only abstracts
- **Recency** - Knowledge has a cutoff date

The system is designed to **augment** your expertise, not replace it.

## Best Practices

1. **Be specific** - "Does X affect Y in context Z?" works better than "Tell me about X"
2. **Stay engaged** - Use checkpoints to redirect if needed
3. **Verify claims** - Check key citations yourself
4. **Iterate** - Run follow-up investigations on open questions

## Learn More

See [USER_GUIDE.md](USER_GUIDE.md) for:
- Detailed usage instructions
- Tips for formulating research questions
- Understanding the agents
- Interpreting confidence levels
- Troubleshooting

## File Structure

```
research_engine/
├── README.md          ← You are here
├── USER_GUIDE.md      ← Detailed documentation
├── ENGINE.md          ← Internal operating instructions
├── sessions/          ← Your investigations
│   └── [session]/
│       ├── journal.md
│       ├── round-N.md              ← Full agent output
│       ├── round-N-brief.md       ← Executive brief + checkpoint (~55 lines)
│       ├── evidence.md
│       └── REPORT.md
├── agents/            ← Agent definitions
└── skills/            ← Literature search APIs
```

---

*Built for researchers who want AI assistance without sacrificing rigor.*
