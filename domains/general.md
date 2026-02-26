# Domain Profile: General / Interdisciplinary

## Domain ID
general

---

## Database Priority

1. **OpenAlex** (REQUIRED): Broadest academic coverage across all fields
   - `python3 skills/openalex.py "query"`
2. **Semantic Scholar** (REQUIRED): Cross-disciplinary, strong citation data
   - `python3 skills/semantic_scholar.py "query"`
3. **Crossref** (RECOMMENDED): DOI-registered works, broad journal coverage
   - `python3 skills/crossref.py "query"`
4. **arXiv** (if STEM-adjacent): Preprints in physics, math, CS, biology
   - `python3 skills/arxiv.py "query"`
5. **PubMed** (if health-adjacent): Biomedical and life sciences literature
   - `python3 skills/pubmed.py "query"`
6. **DBLP** (if CS-adjacent): Computer science venues
   - `python3 skills/dblp.py "query"`
7. **Web Search** (supplementary): Grey literature, reports, news

### Default search_all.py Sources
`openalex, semantic_scholar, crossref`

---

## Evidence Hierarchy

Use a general academic evidence hierarchy. Adapt to the specific sub-domain as the investigation progresses.

| Level | Source Type | Weight |
|-------|------------|--------|
| 1 | Systematic reviews / meta-analyses / comprehensive surveys | Highest |
| 2 | Peer-reviewed empirical studies with strong methodology | High |
| 3 | Peer-reviewed studies with moderate methodology | Moderate |
| 4 | Preprints, working papers, conference papers | Moderate-Low |
| 5 | Grey literature, reports, theses | Low |
| 6 | Opinion, commentary, unverified claims | Lowest |

---

## Quality Rubric

| Rating | Criteria | Examples |
|--------|----------|----------|
| **High** | Peer-reviewed in respected venue + strong methodology + replicated/verified | Top journal articles, major survey papers, seminal works |
| **Medium** | Peer-reviewed + adequate methodology + some limitations | Regular journal and conference articles, working papers from top institutions |
| **Low** | Not peer-reviewed OR major limitations OR unreplicated | Preprints, grey literature, opinion pieces, blog posts |

---

## Perspectives

Use the most relevant disciplinary lenses from the specific domains involved. Start broad:

### Disciplinary Lenses
- **Theoretical:** What frameworks and principles apply?
- **Empirical:** What does the evidence show?
- **Applied/Practical:** What are the real-world implications?
- **Critical/Skeptic:** What are the strongest objections?
- **Historical:** How has understanding evolved?
- **Ethical:** What values and principles are at stake?

### Stakeholder Perspectives
- **Researcher:** What advances understanding?
- **Practitioner:** What works in practice?
- **Skeptic:** What could be wrong? What alternative explanations exist?
- **Policymaker:** What informs better decisions?

---

## Abstraction Levels

Adapt to the specific research question. Default hierarchy:

1. **Specific:** Concrete data points, implementations, cases, examples
2. **Mechanism:** Processes, procedures, causal chains, algorithms
3. **Pattern:** Recurring regularities, empirical laws, trends
4. **Theory:** Explanatory frameworks, models, formalisms
5. **Paradigm:** Foundational assumptions, worldviews, meta-theory

---

## Question Types

### Empirical Questions
- Focus: What does the evidence show? What patterns exist?
- Search terms: study, evidence, data, analysis, results, findings
- Best databases: OpenAlex, Semantic Scholar

### Theoretical Questions
- Focus: What frameworks explain this? What are the formal properties?
- Search terms: theory, framework, model, formal, proof, analysis
- Best databases: Semantic Scholar, OpenAlex

### Applied Questions
- Focus: What works in practice? What are the implications?
- Search terms: application, implementation, practice, case study, real-world
- Best databases: OpenAlex, Crossref, Web Search

---

## Query Building Notes

- Start with **broad searches** across OpenAlex and Semantic Scholar
- Narrow based on initial results — if the topic leans toward a specific domain, consider switching to that domain's profile
- Use **citation chaining** — find one good paper, then search for papers that cite it
- Search in **multiple languages** if the topic has geographic specificity

### Counter-Evidence Search Examples
```bash
python3 skills/openalex.py "X (criticism OR critique OR limitations OR challenge)"
python3 skills/semantic_scholar.py "X (fails OR failure OR negative OR does not)"
```
