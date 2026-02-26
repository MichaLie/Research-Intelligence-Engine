# Domain Profile: Social Sciences

## Domain ID
social_sciences

---

## Database Priority

1. **OpenAlex** (REQUIRED): Broad social science coverage, citation analysis
   - `python3 skills/openalex.py "query"`
2. **Semantic Scholar** (REQUIRED): Cross-disciplinary, growing social science coverage
   - `python3 skills/semantic_scholar.py "query"`
3. **Crossref** (RECOMMENDED): Journal articles, DOI coverage, publisher metadata
   - `python3 skills/crossref.py "query"`
4. **PubMed** (supplementary — for health-adjacent topics): Public health, psychology, psychiatry
   - `python3 skills/pubmed.py "query"`
5. **Web Search** (supplementary): Policy documents, government reports, think tank publications

### Default search_all.py Sources
`openalex, semantic_scholar, crossref`

---

## Evidence Hierarchy

| Level | Source Type | Weight |
|-------|------------|--------|
| 1 | Systematic reviews / meta-analyses | Highest |
| 2 | Pre-registered experimental studies / large-scale RCTs | High |
| 3 | Large-n observational / longitudinal studies | Moderate-High |
| 4 | Quasi-experimental designs (difference-in-differences, RDD, instrumental variables) | Moderate |
| 5 | Qualitative studies, case studies, small-n studies | Moderate-Low |
| 6 | Expert commentary, policy briefs, opinion pieces | Lowest |

### Key Considerations
- **Pre-registration** significantly increases evidence weight (addresses p-hacking concerns)
- **Replication status** is critical — check for replication studies
- **Effect sizes** matter more than statistical significance
- **Qualitative research** can be high quality when methodologically rigorous (grounded theory, ethnography)

---

## Quality Rubric

| Rating | Criteria | Examples |
|--------|----------|----------|
| **High** | Pre-registered + peer-reviewed + large-n + replicated + transparent methods | Pre-registered RCTs, large panel studies in QJE/AER/APSR, Many Labs replications |
| **Medium** | Peer-reviewed + adequate methodology + some limitations | Regular journal articles, well-designed qualitative studies, working papers from top institutions |
| **Low** | Not pre-registered + small-n OR unreplicated + possible p-hacking concerns | Underpowered studies, grey literature, working papers without peer review |

---

## Perspectives

### Disciplinary Lenses
- **Sociological:** What social structures and systems are at play? Power dynamics?
- **Psychological:** What cognitive and behavioral factors matter? Individual differences?
- **Economic:** What incentives and resource dynamics apply? Market failures?
- **Political:** What power structures and governance issues exist? Policy implications?
- **Anthropological/Cultural:** What cultural context shapes this? Cross-cultural variation?
- **Historical:** What precedents and trajectories exist? Path dependencies?

### Stakeholder Perspectives
- **Researcher:** What advances understanding? What are methodological frontiers?
- **Policymaker:** What informs better policy? What are the tradeoffs?
- **Practitioner:** What works on the ground? Implementation challenges?
- **Affected Community:** What do those impacted think and need?
- **Skeptic:** What are replication concerns? Selection effects? Confounds?

---

## Abstraction Levels

1. **Individual:** Personal behavior, cognition, choice, attitudes
2. **Group/Organizational:** Team dynamics, institutional behavior, firms
3. **Community:** Local patterns, social networks, neighborhoods
4. **Societal:** Population-level patterns, cultural norms, national trends
5. **Structural:** Systems, institutions, political economy, global dynamics
6. **Theoretical:** Grand theories, paradigms, foundational assumptions

---

## Question Types

### Causal Questions
- Focus: Experimental and quasi-experimental evidence, causal inference
- Search terms: effect, impact, cause, intervention, treatment, outcome, causal, RCT
- Best databases: OpenAlex, Semantic Scholar

### Descriptive Questions
- Focus: Surveys, census data, qualitative research, phenomenology
- Search terms: prevalence, pattern, experience, perception, attitude, survey, qualitative
- Best databases: OpenAlex, Crossref

### Policy Questions
- Focus: Evaluations, cost-benefit, implementation science
- Search terms: policy, program, evaluation, implementation, cost-effectiveness, welfare
- Best databases: OpenAlex, Crossref, Web Search (for reports)

---

## Query Building Notes

- Search by **study type** (e.g., "randomized experiment", "difference-in-differences", "ethnography")
- Include **geographic scope** when relevant (e.g., "developing countries", "United States")
- Search for **replication studies** explicitly (e.g., "replication of [original study]")
- Look for **pre-registration** information (OSF, AEA Registry)
- Use **NBER working papers** as a source for economics

### Counter-Evidence Search Examples
```bash
python3 skills/openalex.py "X (replication failure OR failed to replicate OR no effect)"
python3 skills/semantic_scholar.py "X (criticism OR confound OR selection bias OR endogeneity)"
```
