# Research Intelligence Engine - User Guide

A comprehensive guide to using the Research Intelligence Engine for scientific literature review and hypothesis evaluation.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Formulating Research Questions](#formulating-research-questions)
4. [Understanding the Agents](#understanding-the-agents)
5. [The Deliberation Process](#the-deliberation-process)
6. [Human Checkpoints](#human-checkpoints)
7. [Interpreting Results](#interpreting-results)
8. [Understanding Confidence Levels](#understanding-confidence-levels)
9. [Working with Reports](#working-with-reports)
10. [Tips for Better Results](#tips-for-better-results)
11. [Limitations](#limitations)
12. [Troubleshooting](#troubleshooting)
13. [Example Session Walkthrough](#example-session-walkthrough)

---

## Introduction

The Research Intelligence Engine is a multi-agent AI system designed to help researchers conduct rigorous literature reviews. Unlike simple chatbot interactions, it employs multiple specialized AI agents that collaborate, challenge each other, and systematically search scientific databases.

### Why Use This System?

- **Systematic**: Follows a structured process, not ad-hoc searching
- **Adversarial**: Built-in skeptic challenges conclusions
- **Transparent**: All reasoning preserved for your review
- **Balanced**: Actively searches for counter-evidence
- **Citable**: Returns PMIDs, DOIs, and proper citations

### What Makes It Different?

Traditional AI assistance often suffers from:
- Confirmation bias (finding what you expect)
- Overconfidence (stating speculation as fact)
- Poor sourcing (vague or hallucinated references)

This system addresses these through:
- Mandatory counter-evidence searches
- Explicit confidence levels on all claims
- Real database searches with verifiable citations
- Adversarial review that challenges findings

---

## Getting Started

### Starting a New Investigation

In Claude Code, say:

```
Call the engine
```

You'll be prompted to provide your research question. The system will then:
1. Create a session folder
2. Initialize tracking files
3. Begin the first round of analysis

### Resuming an Investigation

```
Continue [topic keyword]
```

For example: `Continue PIN5` or `Continue senolytics`

### Viewing All Sessions

```
List sessions
```

Shows all active and completed investigations.

---

## Formulating Research Questions

The quality of your results depends heavily on how you frame your question.

### Good Questions

| Question Type | Example |
|---------------|---------|
| Mechanistic | "What is the molecular mechanism by which metformin affects aging?" |
| Comparative | "How do senolytics compare to caloric restriction for lifespan extension?" |
| Causal | "Does sleep deprivation cause neurodegeneration or is it correlational?" |
| Feasibility | "Is CRISPR-based gene therapy feasible for treating Huntington's disease?" |

### Less Effective Questions

| Avoid | Why | Better Version |
|-------|-----|----------------|
| "Tell me about CRISPR" | Too broad | "What are the current limitations of CRISPR for in vivo gene editing?" |
| "Is X good?" | Value judgment | "What does evidence show about X's efficacy for Y?" |
| "Latest research on Z" | No focus | "What mechanisms have been proposed for Z in the past 3 years?" |

### Tips for Question Formulation

1. **Specify the context**: "...in humans" vs "...in model organisms"
2. **Define success criteria**: What would a good answer include?
3. **Bound the scope**: Time period, organism, tissue type
4. **Include your hypothesis**: "I suspect X causes Y because Z - what's the evidence?"

---

## Understanding the Agents

The system employs five specialized AI agents, each with a distinct role.

### Deep Analyst

**Role**: Conceptual thinker and hypothesis generator

**What it does**:
- Reframes questions from multiple perspectives
- Generates and refines hypotheses
- Navigates between big-picture and mechanistic thinking
- Identifies conceptual gaps

**When it's most valuable**: Complex questions requiring creative thinking about mechanisms

### Researcher

**Role**: Evidence gatherer

**What it does**:
- Searches PubMed, OpenAlex, and bioRxiv
- Evaluates source quality
- Extracts key findings
- **Actively searches for counter-evidence**

**Databases searched**:
| Database | Strengths |
|----------|-----------|
| PubMed | Biomedical focus, MeSH terms, peer-reviewed |
| OpenAlex | Broad coverage, citation counts, open access |
| bioRxiv/medRxiv | Preprints, cutting-edge, not yet peer-reviewed |

### Critic

**Role**: Adversarial reviewer

**What it does**:
- Challenges weak arguments
- Identifies logical gaps
- Steel-mans alternative hypotheses
- Assesses when investigation should converge

**Why it matters**: Prevents the system from becoming an echo chamber that confirms your expectations

### Synthesizer

**Role**: Integration specialist

**What it does**:
- Distills each round's findings
- Maps tensions between viewpoints
- Produces checkpoint summaries
- Frames decisions for human review

### Report Generator

**Role**: Communication specialist

**What it does**:
- Compiles final polished report
- Structures findings for presentation
- Formats citations properly
- Ensures critical caveats are prominent

---

## The Deliberation Process

### Round 1: Structuring

**Agents involved**: Deep Analyst, Researcher

**What happens**:
1. Deep Analyst reframes your question 3 ways
2. Deep Analyst generates initial hypotheses
3. Researcher conducts broad literature search
4. Synthesizer produces brief (`round-1-brief.md`) + detail (appended to `round-1.md`)

**Typical duration**: 5-10 minutes

### Rounds 2-N: Iteration

**Agents involved**: Critic, Deep Analyst, Researcher

**What happens**:
1. Critic reviews Round N-1, identifies weaknesses
2. Deep Analyst addresses critiques
3. Researcher conducts targeted searches
4. Synthesizer produces brief (`round-N-brief.md`) + detail (appended to `round-N.md`)

**Human decision point** after each round — you read the brief file to decide.

### Convergence

The investigation ends when:
- Critic finds no new substantial issues
- Hypotheses are adequately tested
- Remaining questions require empirical research
- Human approves convergence

**Guardrails**:
- Minimum 2 rounds before convergence allowed
- Maximum 5 rounds (prevents infinite loops)

### Report Generation

After convergence, the Report Generator:
1. Reads all session files
2. Synthesizes into polished REPORT.md
3. Ensures proper citations and confidence levels

---

## Human Checkpoints

After each round, you receive a summary and choose how to proceed.

### Checkpoint Options

| Option | When to Use |
|--------|-------------|
| **Continue** | Critic raised valid points that need addressing |
| **Deep dive** | One aspect needs more focused investigation |
| **Converge** | Main question is adequately addressed |
| **Redirect** | Investigation went off-track, need new direction |
| **Stop** | Enough information gathered, or wrong approach |

### Reading Your Results

After each round, the system produces two files:

- **`round-N-brief.md`** (~55 lines) — Open this first. It contains an executive brief (3 sentences on what happened), key findings, hypothesis changes, the Critic's verdict, and your decision options. Everything you need to decide is here.
- **`round-N.md`** (full detail) — Open this when you want to understand HOW the agents reached their conclusions. Contains the full reasoning from each agent plus the Synthesizer's detailed tension mapping and evidence quality assessment.

**You don't need to read the detail file to make a good decision** — the brief is self-contained. But reading the detail file is where you learn the most about how rigorous analysis works.

### What to Look For

At each checkpoint, consider:

1. **Are hypotheses being tested fairly?** Both supporting and opposing evidence?
2. **Is evidence quality sufficient?** High-quality sources or mostly speculation?
3. **Are critical gaps being addressed?** Or is the system spinning on the same issues?
4. **Is the scope appropriate?** Too narrow or too broad?

### Redirecting the Investigation

You can redirect at any checkpoint:

```
I want to focus specifically on the iron-auxin connection,
not the general transcription factor hypothesis.
```

The system will adjust accordingly.

---

## Interpreting Results

### Hypothesis Verdicts

| Verdict | Meaning |
|---------|---------|
| **Supported** | Evidence favors this hypothesis; no major contradicting evidence |
| **Rejected** | Evidence contradicts this hypothesis; should be abandoned |
| **Unresolved** | Insufficient evidence to decide; needs empirical testing |

### Evidence Quality Ratings

| Rating | Criteria |
|--------|----------|
| **High** | Peer-reviewed, RCT or systematic review, n>100, replicated |
| **Medium** | Peer-reviewed, observational or small trial, some limitations |
| **Low** | Preprint, case report, expert opinion, major limitations |

### Reading the Evidence Table

Each source in `evidence.md` includes:
- Citation with PMID/DOI
- Study type (RCT, cohort, review, etc.)
- Key finding
- Quality rating
- Relevance notes

---

## Understanding Confidence Levels

Every claim in the report has a confidence level. Here's how to interpret them:

### High Confidence

**Means**: Multiple high-quality sources agree; no contradicting evidence; well-replicated

**Appropriate response**: Can cite this in your work with reasonable assurance

**Example**: "NRAMP6 localizes to the Golgi/TGN" (High) - confirmed by multiple studies with appropriate methods

### Medium Confidence

**Means**: Some support but limitations; single good study; or indirect evidence

**Appropriate response**: Worth pursuing but verify independently

**Example**: "APL regulates companion cell identity" (Medium-High) - well-established but specific binding to target promoters not demonstrated

### Low Confidence

**Means**: Preliminary, speculative, or based on indirect evidence

**Appropriate response**: Treat as hypothesis, not established fact

**Example**: "ROS-mediated crosstalk explains co-expression" (Low-Medium) - plausible but untested

---

## Working with Reports

### Report Structure

Every `REPORT.md` follows this structure:

1. **Executive Summary** - 3-5 sentences, includes main conclusion and critical caveat
2. **Research Question** - Context, significance, scope
3. **Key Findings** - Numbered list with confidence levels
4. **Hypothesis Analysis** - Ranking table + detailed breakdown
5. **Evidence Summary** - Strongest evidence, weakest links, gaps
6. **Limitations & Caveats** - What the report cannot establish
7. **Experimental Predictions** - Testable next steps
8. **Conclusions** - Established, uncertain, next steps
9. **Methodology** - How the investigation was conducted
10. **References** - Properly formatted with quality ratings

### Using Reports in Your Work

**Do**:
- Verify key citations independently
- Use confidence levels appropriately when citing
- Include caveats when presenting findings
- Follow up on experimental predictions

**Don't**:
- Treat all findings as equally certain
- Ignore the limitations section
- Skip checking high-impact citations
- Present AI synthesis as your own primary analysis

### Sharing Reports

Reports are designed to be shareable with colleagues. They:
- Stand alone without needing round files
- Include methodology transparency
- Provide proper citations
- Acknowledge AI assistance

---

## Tips for Better Results

### Before Starting

1. **Define your goal**: Literature review? Hypothesis testing? Gap identification?
2. **Specify context**: Human vs model organism? In vivo vs in vitro?
3. **State your priors**: What do you already believe? (Helps identify confirmation bias)

### During Investigation

1. **Stay engaged at checkpoints**: Don't just click "continue" automatically
2. **Redirect when needed**: If agents are missing the point, say so
3. **Ask for clarification**: "Why was H2 rejected?" gets you more detail
4. **Request specific searches**: "Search for evidence against the APL hypothesis"

### After Completion

1. **Read the full report**: Not just the executive summary
2. **Check key citations**: Especially those supporting main conclusions
3. **Note the gaps**: What evidence is missing?
4. **Plan follow-up**: Which experimental predictions are most feasible?

### Question Refinement

If results are unsatisfying, try reformulating:

| Original | Refined |
|----------|---------|
| "Does X work?" | "What is the evidence for X's efficacy in Y context?" |
| "Why does A cause B?" | "What mechanisms have been proposed for A→B, and what's the evidence for each?" |
| "Is this field promising?" | "What are the main unsolved problems in this field and what progress has been made?" |

---

## Limitations

### What the System Cannot Do

| Limitation | Implication |
|------------|-------------|
| **No full-text access** | Only reads abstracts; may miss methodological details |
| **No database queries** | Cannot query scRNA-seq, proteomics, or other data repositories |
| **No computation** | Cannot run statistics, analyze data, or generate figures |
| **No real-time data** | Knowledge cutoff applies |
| **No domain expertise** | May miss nuances obvious to specialists |

### When NOT to Use This System

- For questions requiring primary data analysis
- When you need real-time or very recent information
- For highly specialized subfields where nuance is critical
- As a replacement for expert consultation

### Appropriate Use Cases

- Initial literature survey for new research direction
- Systematic hypothesis evaluation
- Identifying gaps in a field
- Preparing for grant writing or review articles
- Training researchers in rigorous thinking

---

## Troubleshooting

### Common Issues

**Session seems stuck**
- Press Esc and type "continue" to resume
- May be API timeout; usually resolves on retry

**Agents not finding relevant papers**
- Try different search terms
- Specify the field more precisely
- Ask for searches in specific databases

**Too much focus on one hypothesis**
- Explicitly ask to explore alternatives
- Request counter-evidence searches
- Redirect at checkpoint

**Confidence levels seem wrong**
- Ask for justification: "Why is H1 rated High confidence?"
- Request re-evaluation with specific criteria

**Report missing key papers you know about**
- Mention them explicitly: "Make sure to include Smith et al. 2023"
- The system searches systematically but may miss specific papers

### Getting Help

At any point, you can ask:
- "What have you found so far?"
- "Why did you reject H2?"
- "Search specifically for [topic]"
- "Focus more on [aspect]"

---

## Example Session Walkthrough

Here's what a typical session looks like:

### 1. Initiation

**You**: Call the engine

**System**: Research Intelligence Engine activated. What would you like to investigate?

**You**: What is the mechanistic link between PIN5 and NRAMP6 that explains their co-expression in phloem companion cells?

### 2. Round 1 (Structuring)

**System**:
- Creates session: `2026-01-pin5-nramp6-coexpression`
- Deep Analyst reframes question, generates 4 hypotheses
- Researcher searches PubMed, OpenAlex, bioRxiv (60+ sources)
- Synthesizer produces checkpoint

**Checkpoint summary shows**:
- H1: ER metabolic coupling (initial favorite)
- H2: ER stress response
- H3: Phloem metal-auxin co-transport
- H4: Shared transcription factor program

### 3. Round 2 (Iteration)

**System**:
- Critic identifies critical issue: "NRAMP6 is TGN-localized, not ER!"
- Deep Analyst revises hypotheses
- Researcher searches for APL regulation evidence

**Checkpoint shows**:
- H1 rejected (localization conflict)
- H4 emerging as leading hypothesis
- New question: Is co-expression even validated?

### 4. Round 3 (Convergence)

**System**:
- Critic notes spinning on same co-expression validation issue
- Literature cannot resolve this - needs experimental data
- Recommends convergence

**You**: Approve convergence

### 5. Report Generation

**System** produces REPORT.md with:
- Executive summary acknowledging unvalidated premise
- H1 rejected, H4 most plausible
- 6 specific experimental predictions
- 21 properly formatted references

### Total Time: ~25 minutes

---

## Conclusion

The Research Intelligence Engine is a tool for augmenting—not replacing—your scientific judgment. It excels at systematic literature review, hypothesis generation, and adversarial evaluation. Its value comes from the structured process and built-in skepticism, not from any claim to superhuman knowledge.

Use it wisely:
- Stay engaged at checkpoints
- Verify key citations
- Acknowledge limitations
- Follow up with experiments

Good luck with your research.

---

*For technical details, see [ENGINE.md](ENGINE.md).*
*For quick reference, see [README.md](README.md).*
