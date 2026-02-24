# Research Intelligence Engine

A multi-agent AI system for rigorous scientific literature review and hypothesis evaluation.

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
