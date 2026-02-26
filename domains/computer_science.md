# Domain Profile: Computer Science

## Domain ID
computer_science

---

## Database Priority

1. **Semantic Scholar** (REQUIRED): Broad CS coverage, citation counts, venue metadata
   - `python3 skills/semantic_scholar.py "query"`
2. **arXiv** (REQUIRED): Preprints — the standard dissemination channel in CS
   - `python3 skills/arxiv.py "query"`
3. **DBLP** (REQUIRED): Authoritative CS venue/publication index
   - `python3 skills/dblp.py "query"`
   - Note: DBLP does NOT provide abstracts. Use for discovery, then look up details in Semantic Scholar or arXiv.
4. **OpenAlex** (RECOMMENDED): Cross-disciplinary, citation analysis, open access
   - `python3 skills/openalex.py "query"`
5. **Crossref** (supplementary): DOI-registered journal articles
   - `python3 skills/crossref.py "query"`
6. **Web Search** (supplementary): Blog posts, technical reports, documentation, GitHub repos

### Default search_all.py Sources
`semantic_scholar, arxiv, openalex, dblp`

---

## Evidence Hierarchy

CS research has a fundamentally different publication culture from medicine. **Top conferences are equal to or more prestigious than journals.** Empirical benchmarks and formal proofs are the primary evidence types.

| Level | Source Type | Weight |
|-------|------------|--------|
| 1 | Peer-reviewed papers at top venues with reproducible results and code | Highest |
| 2 | Peer-reviewed journal articles (JMLR, TPAMI, AIJ, TKDE, etc.) | High |
| 3 | Workshop papers at top venues OR strong arXiv preprints from established groups with code | Moderate |
| 4 | Technical reports, theses, arXiv preprints without code/reproduction | Moderate-Low |
| 5 | Blog posts, tutorials, documentation (useful but not citable as evidence) | Low |
| 6 | Unverified claims, marketing materials, social media | Lowest |

### Top CS Venues (non-exhaustive)
- **ML/AI:** NeurIPS, ICML, ICLR, AAAI, IJCAI, AISTATS, UAI
- **NLP:** ACL, EMNLP, NAACL, EACL, COLING
- **Vision:** CVPR, ICCV, ECCV
- **Data Mining/IR:** KDD, SIGIR, WWW, WSDM, RecSys, CIKM
- **Systems:** OSDI, SOSP, NSDI, EuroSys, MLSys
- **Theory:** STOC, FOCS, SODA, COLT
- **Databases:** SIGMOD, VLDB, ICDE
- **Software Engineering:** ICSE, FSE, ASE
- **HCI:** CHI, UIST, CSCW

### Key Differences from Biomedical
- **Conferences are top-tier** (unlike medicine where journals dominate)
- **arXiv preprints carry more weight** (CS norms accept pre-print sharing as standard practice)
- **Reproducibility = code availability** (not sample size)
- **Ablation studies** replace "controlled trials" as the gold standard for causal claims about components
- **Benchmark performance** on standard datasets is the primary empirical evidence

---

## Quality Rubric

| Rating | Criteria | Examples |
|--------|----------|----------|
| **High** | Peer-reviewed at top venue + reproducible (code available) + ablation studies + multiple baselines + statistical significance reported | NeurIPS/ICML papers with GitHub repo, JMLR articles with reproducibility checklist |
| **Medium** | Peer-reviewed at recognized venue OR strong preprint + some reproducibility + reasonable baselines | Workshop papers, second-tier conferences (e.g., ECML, PAKDD), well-cited arXiv |
| **Low** | Preprint without code OR single-dataset evaluation OR no comparison to baselines OR no statistical tests | Early-stage arXiv, blog experiments, informal benchmarks |

---

## Perspectives

### Disciplinary Lenses
- **Algorithmic/Theoretical:** What are the computational properties? Complexity, convergence, guarantees?
- **Empirical/Experimental:** What do benchmarks and experiments show? How robust are results?
- **Systems/Engineering:** Is it practical? Scalable? Deployable? What are the latency/memory constraints?
- **Mathematical:** What formal properties hold? What can be proved?
- **Human-Centered:** What are the user implications? Fairness, interpretability, safety?
- **Historical:** How does this relate to prior approaches? What paradigm shift does it represent?

### Stakeholder Perspectives
- **Researcher:** What advances the state of the art? What are the open problems?
- **Practitioner/Engineer:** What works in production? What are the engineering tradeoffs?
- **Reviewer:** What would a critical peer reviewer at a top venue challenge?
- **Skeptic:** What are the strongest objections? Benchmark overfitting? Cherry-picked results?

---

## Abstraction Levels

1. **Implementation:** Specific code, libraries, hyperparameters, hardware
2. **Algorithm:** Pseudocode-level design, optimization procedures, convergence properties
3. **Architecture:** Model structure, component interaction, information flow
4. **Methodology:** Training paradigm, evaluation protocol, experimental design
5. **Problem Formulation:** How the task is defined and framed, loss functions, metrics
6. **Theoretical Framework:** Formal foundations, complexity classes, learning theory, generalization bounds

---

## Question Types

### Algorithm Design Questions
- Focus: Novel methods, architectures, training procedures
- Search terms: architecture, algorithm, method, model, training, optimization, novel
- Best databases: Semantic Scholar, arXiv, DBLP

### Benchmark/Performance Questions
- Focus: Empirical comparisons, state-of-the-art results, leaderboards
- Search terms: benchmark, evaluation, comparison, baseline, state-of-the-art, SOTA, outperforms
- Best databases: Semantic Scholar (citation-aware), arXiv (latest results)

### Theoretical Questions
- Focus: Formal analysis, proofs, bounds, complexity
- Search terms: theorem, proof, bound, complexity, convergence, guarantee, sample complexity
- Best databases: Semantic Scholar, arXiv, DBLP

### Systems/Scalability Questions
- Focus: Deployment, efficiency, real-world performance, distributed systems
- Search terms: scalability, latency, throughput, deployment, distributed, efficiency, inference
- Best databases: DBLP (systems venues), Semantic Scholar

### Survey/Landscape Questions
- Focus: Comprehensive reviews, taxonomies, position papers
- Search terms: survey, review, taxonomy, overview, landscape, tutorial, position paper
- Best databases: Semantic Scholar (highly-cited surveys), arXiv

---

## Query Building Notes

- **No MeSH terms** — use natural language keywords and paper/method names
- Search by **author name** for key research groups (e.g., "Vaswani attention" or "Hinton deep learning")
- Search by **method name** (e.g., "MAML", "transformer", "GAN", "diffusion model")
- Use DBLP for **venue-specific discovery**, then look up full details in Semantic Scholar
- Conference acronyms work well as search terms (e.g., "NeurIPS 2024 meta-learning")
- Include **year ranges** to find recent work vs. foundational papers

### Counter-Evidence Search Examples
```bash
python3 skills/semantic_scholar.py "X (limitation OR failure OR does not scale OR negative result)"
python3 skills/arxiv.py "X (critique OR replication failure OR benchmark overfitting)"
python3 skills/semantic_scholar.py "X vs Y comparison (worse OR inferior OR underperforms)"
```
