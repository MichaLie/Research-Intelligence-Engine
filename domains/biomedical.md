# Domain Profile: Biomedical Research

## Domain ID
biomedical

---

## Database Priority

1. **PubMed** (REQUIRED): Clinical studies, reviews, mechanisms, MeSH-indexed
   - `python3 skills/pubmed.py "query"`
2. **OpenAlex** (REQUIRED): Cross-disciplinary, citation analysis, open access
   - `python3 skills/openalex.py "query"`
3. **bioRxiv/medRxiv** (REQUIRED): Latest preprints in biology and medicine
   - `python3 skills/biorxiv.py "query"`
4. **Semantic Scholar** (RECOMMENDED): Broad coverage, citation metadata
   - `python3 skills/semantic_scholar.py "query"`
5. **Crossref** (supplementary): DOI-registered works, journal metadata
   - `python3 skills/crossref.py "query"`
6. **Web Search** (supplementary only): News, policy, grey literature

### Default search_all.py Sources
`pubmed, openalex, semantic_scholar, biorxiv`

---

## Evidence Hierarchy

| Level | Source Type | Weight |
|-------|------------|--------|
| 1 | Systematic reviews / meta-analyses | Highest |
| 2 | Randomized controlled trials (RCTs) | High |
| 3 | Cohort studies | Moderate |
| 4 | Case-control studies | Moderate-Low |
| 5 | Case series / reports | Low |
| 6 | Expert opinion / editorials | Lowest |

---

## Quality Rubric

| Rating | Criteria | Examples |
|--------|----------|----------|
| **High** | Peer-reviewed + (RCT or SR/MA) + n>100 + replicated OR seminal work in top journal | Cochrane reviews, large RCTs in NEJM/Lancet/Nature |
| **Medium** | Peer-reviewed + (observational or small RCT or narrative review) + adequate methods | Cohort studies, pilot RCTs, well-conducted observational |
| **Low** | Preprint OR case report OR expert opinion OR major limitations OR unreplicated | bioRxiv preprints, case series, opinion pieces |

---

## Perspectives

### Disciplinary Lenses
- **Biological/Mechanistic:** What are the underlying mechanisms? Pathways, molecules, interactions?
- **Evolutionary:** What selective pressures shaped this? Evolutionary tradeoffs?
- **Clinical/Applied:** What are the practical implications for intervention?
- **Epidemiological:** What patterns exist at population level? Risk factors?
- **Psychological/Behavioral:** How do cognitive and behavioral factors interact?
- **Economic:** What are the cost-effectiveness implications?

### Stakeholder Perspectives
- **Researcher:** What would advance scientific understanding?
- **Clinician:** What would improve patient outcomes?
- **Patient:** What matters most to those affected?
- **Policymaker:** What would inform better health policy?

---

## Abstraction Levels

1. **Molecular/Mechanistic:** Specific pathways, molecules, interactions
2. **Cellular/Tissue:** Cell types, tissue organization, local effects
3. **Organ/System:** Physiological systems, organ function
4. **Organism:** Whole-body effects, individual variation
5. **Population:** Epidemiological patterns, public health implications
6. **Conceptual:** Abstract principles, theoretical frameworks

---

## Question Types

### Mechanism Questions
- Focus: Basic science, pathway databases, molecular interactions
- Search terms: mechanism, pathway, molecular, signaling, regulation, expression
- Best databases: PubMed, OpenAlex

### Intervention Questions
- Focus: Clinical trials, systematic reviews, treatment efficacy
- Search terms: treatment, therapy, intervention, trial, randomized, efficacy
- Best databases: PubMed (with RCT filter), Cochrane via OpenAlex

### Epidemiology Questions
- Focus: Cohort studies, population studies, risk factors
- Search terms: prevalence, incidence, risk factor, association, cohort, longitudinal
- Best databases: PubMed, OpenAlex

### Prognosis Questions
- Focus: Longitudinal studies, survival analyses, natural history
- Search terms: outcome, prognosis, survival, follow-up, natural history
- Best databases: PubMed, OpenAlex

---

## Query Building Notes

- **Use MeSH terms for PubMed** — PubMed uses Medical Subject Headings for indexing
- Use Boolean operators (AND, OR, NOT)
- Apply filters: publication date, study type (RCT, review, etc.), species (humans)
- Search by PMID for known references
- Use quotation marks for exact phrases

### Counter-Evidence Search Examples
```bash
python3 skills/pubmed.py "X Y (fail OR failure OR negative OR no effect OR ineffective)"
python3 skills/pubmed.py "X Y (criticism OR critique OR limitations OR concerns)"
```
