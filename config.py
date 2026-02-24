"""
Research Intelligence Engine Configuration

Central configuration file for API endpoints, settings, and defaults.
Modify these values to customize the engine's behavior.
"""

# =============================================================================
# API ENDPOINTS
# =============================================================================

# PubMed E-utilities
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# bioRxiv/medRxiv API
BIORXIV_BASE_URL = "https://api.biorxiv.org"

# OpenAlex API
OPENALEX_BASE_URL = "https://api.openalex.org"

# =============================================================================
# API KEYS (Optional)
# =============================================================================

# PubMed API key (optional, increases rate limit from 3 to 10 requests/second)
# Get one at: https://www.ncbi.nlm.nih.gov/account/
PUBMED_API_KEY = None  # Set to your API key string if you have one

# OpenAlex email (optional, for polite pool - better rate limits)
# Setting this is recommended: https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication
OPENALEX_EMAIL = None  # Set to your email string, e.g., "researcher@university.edu"

# =============================================================================
# DEFAULT SETTINGS
# =============================================================================

# Default maximum results per search
DEFAULT_MAX_RESULTS = 25

# Default date range for searches (years back from current date)
DEFAULT_YEARS_BACK = 5

# Maximum rounds before forcing convergence
MAX_DELIBERATION_ROUNDS = 5

# =============================================================================
# FILE TEMPLATES
# =============================================================================

# journal.md - Summary file (kept small, always read by agents)
JOURNAL_TEMPLATE = """# Research Session: {topic}

**Session ID:** {session_id}
**Started:** {timestamp}
**Status:** active
**Current Round:** 0

---

## Problem Space

**Research Question:** {question}

**Reframed as:** [To be filled by Deep Analyst in Round 1]

**Sub-questions:**
1. [To be identified]

**Key Constraints:** [To be identified]

---

## Hypotheses

| # | Hypothesis | Support Criteria | Refutation Criteria | Confidence | Status |
|---|------------|-----------------|---------------------|------------|--------|
| H1 | [To be generated] | [What would confirm?] | [What would refute?] | - | pending |

> **A hypothesis that cannot be refuted is not a scientific hypothesis.** Every hypothesis in this table must have explicit refutation criteria — what evidence, if found, would make you abandon or substantially revise it.

---

## Open Questions

- [ ] [To be identified during analysis]

---

## Current Synthesis

[Living summary - updated after each round by Synthesizer]

---

## Round Log

| Round | Agents | Key Outcome | File |
|-------|--------|-------------|------|

---

## Final Output

[To be produced when status = converged]
"""

# round-N.md - Full agent output for a round
ROUND_TEMPLATE = """# Round {round_number}

**Session:** {session_id}
**Started:** {timestamp}
**Agents:** {agents}

---

## Agent Contributions

[Agent outputs will be appended here]

---

> **Executive brief and checkpoint:** [round-{round_number}-brief.md](round-{round_number}-brief.md)
"""

# round-N-brief.md - Executive brief + checkpoint (~55 lines)
BRIEF_TEMPLATE = """# Round {round_number} Brief

**Session:** {session_id} | **Sources this round:** [to be filled] | **Convergence:** [to be filled]

## Executive Brief

[To be filled by Synthesizer -- 3 sentences maximum]

> Full agent reasoning: [round-{round_number}.md](round-{round_number}.md) | Evidence: [evidence.md](evidence.md)

---

[Checkpoint sections to be filled by Synthesizer]
"""

# evidence.md - Running evidence table
EVIDENCE_TEMPLATE = """# Evidence Collected

**Session:** {session_id}
**Last Updated:** {timestamp}

---

## Sources

| # | Source | Type | Key Finding | Quality | Round | Notes |
|---|--------|------|-------------|---------|-------|-------|

---

## Quality Legend

| Rating | Criteria |
|--------|----------|
| **High** | Peer-reviewed, RCT or systematic review, n>100, replicated |
| **Medium** | Peer-reviewed, observational or small RCT, some limitations |
| **Low** | Preprint, case report, expert opinion, major limitations |

---

## Notes

[Additional notes on evidence patterns, conflicts, gaps]
"""

# =============================================================================
# SESSION SETTINGS
# =============================================================================

# Where sessions are stored (relative to research_engine/)
SESSIONS_DIR = "sessions"

# Session naming format
SESSION_NAME_FORMAT = "{year}-{month:02d}-{slug}"

# =============================================================================
# AGENT SETTINGS
# =============================================================================

# Agent file locations (relative to research_engine/)
AGENT_DEFINITIONS = {
    "deep_analyst": "agents/deep_analyst.md",
    "critic": "agents/critic.md",
    "researcher": "agents/researcher.md",
    "synthesizer": "agents/synthesizer.md",
    "report_generator": "agents/report_generator.md"
}

# Default model for agents
DEFAULT_AGENT_MODEL = "opus"

# =============================================================================
# CONVERGENCE SETTINGS
# =============================================================================

# Minimum rounds before convergence is allowed
MIN_ROUNDS_BEFORE_CONVERGENCE = 2

# Keywords indicating critic found no substantial issues
CONVERGENCE_INDICATORS = [
    "no new substantial issues",
    "no critical weaknesses",
    "ready to converge",
    "analysis is robust"
]
