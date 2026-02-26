# Domain Profile: Physics & Mathematics

## Domain ID
physics_math

---

## Database Priority

1. **arXiv** (REQUIRED): The primary venue for physics/math — preprints are the norm
   - `python3 skills/arxiv.py "query"`
2. **Semantic Scholar** (REQUIRED): Citation analysis, cross-referencing
   - `python3 skills/semantic_scholar.py "query"`
3. **OpenAlex** (RECOMMENDED): Broad coverage, journal articles
   - `python3 skills/openalex.py "query"`
4. **Crossref** (supplementary): DOI-registered journal articles
   - `python3 skills/crossref.py "query"`
5. **Web Search** (supplementary): Lecture notes, reviews, survey talks

### Default search_all.py Sources
`arxiv, semantic_scholar, openalex`

---

## Evidence Hierarchy

| Level | Source Type | Weight |
|-------|------------|--------|
| 1 | Formal proofs / mathematical theorems in peer-reviewed publications | Highest |
| 2 | Published experimental results with statistical analysis, replicated by independent groups | High |
| 3 | Peer-reviewed theoretical/computational papers | Moderate-High |
| 4 | Well-cited arXiv preprints (physics/math norms accept preprints as standard) | Moderate |
| 5 | Conference proceedings, workshop papers | Moderate-Low |
| 6 | Informal notes, blog posts, unrefereed claims | Lowest |

---

## Quality Rubric

| Rating | Criteria | Examples |
|--------|----------|----------|
| **High** | Peer-reviewed in top journal + (formal proof OR replicated experiment OR large collaboration) | Physical Review Letters, Annals of Mathematics, Nature Physics, CERN publications |
| **Medium** | Peer-reviewed OR strong arXiv preprint + reasonable methods + some verification | Regular journal articles, well-cited preprints, computational studies |
| **Low** | Unverified preprint OR single unreplicated observation OR informal note | New arXiv submissions without peer review, conference talks, personal notes |

---

## Perspectives

### Disciplinary Lenses
- **Theoretical/Mathematical:** What are the formal properties? What can be derived or proved?
- **Experimental/Observational:** What does the data show? What measurements confirm or challenge theory?
- **Computational/Numerical:** What do simulations predict? How do numerical results compare to analytical?
- **Phenomenological:** What effective descriptions work? What models capture the essential physics?
- **Historical:** How has understanding evolved? What were the key breakthroughs?

### Stakeholder Perspectives
- **Theorist:** What principles are at work? What symmetries or invariances?
- **Experimentalist:** What can be measured? What precision is achievable?
- **Skeptic:** What assumptions are unverified? What alternative explanations exist?

---

## Abstraction Levels

1. **Specific Calculation:** Particular integrals, numerical values, data points
2. **Model/Equation:** Governing equations, Hamiltonians, Lagrangians
3. **Theory:** Theoretical framework (QFT, GR, algebraic geometry, etc.)
4. **Paradigm:** Foundational principles, symmetries, conservation laws
5. **Meta-Theoretical:** Unification, philosophy of physics/mathematics, foundational questions

---

## Question Types

### Theoretical Questions
- Focus: Proofs, derivations, formal results, conjectures
- Search terms: theorem, proof, conjecture, bound, exact solution, derivation
- Best databases: arXiv, Semantic Scholar

### Experimental Questions
- Focus: Measurements, observations, data analysis, detector design
- Search terms: measurement, observation, experiment, detector, signal, data analysis
- Best databases: arXiv, OpenAlex

### Computational Questions
- Focus: Simulations, numerical methods, algorithms
- Search terms: simulation, numerical, computational, Monte Carlo, lattice, finite element
- Best databases: arXiv, Semantic Scholar

---

## Query Building Notes

- Use **arXiv categories** for targeted search (e.g., `hep-th` for high-energy theory, `math.AG` for algebraic geometry, `cond-mat` for condensed matter)
- Search by **equation names** or **theorem names** (e.g., "Navier-Stokes", "Riemann hypothesis")
- Search by **collaboration name** for experimental physics (e.g., "ATLAS", "LIGO", "Planck")
- Include **arXiv IDs** when referencing specific papers

### Counter-Evidence Search Examples
```bash
python3 skills/arxiv.py "X (inconsistency OR tension OR discrepancy OR counterexample)"
python3 skills/semantic_scholar.py "X (disproved OR incorrect OR error OR retraction)"
```
