# Technical Debt — Deferred for Production

Items intentionally deferred during POC. Each would matter for shared/production use but is acceptable for personal proof-of-concept.

---

## TLS Certificate Verification Disabled

**Files:** `skills/pubmed.py`, `skills/openalex.py`, `skills/biorxiv.py`

All three API clients disable SSL certificate verification (`CERT_NONE`). This was done to work around macOS certificate chain issues during development.

**Risk:** Man-in-the-middle attacks on API traffic. Low risk for read-only academic API queries on trusted networks, but unacceptable for production.

**Fix:** Install `certifi` package, point SSL context at its CA bundle: `ssl.create_default_context(cafile=certifi.where())`. Remove `check_hostname = False` and `verify_mode = CERT_NONE`.

---

## No Retry/Backoff Strategy

**Files:** `skills/pubmed.py`, `skills/openalex.py`, `skills/biorxiv.py`

API calls fail on first error with no retry. Transient network issues, rate limit 429s, and server 503s all produce the same outcome: silent failure returning empty results.

**Risk:** Intermittent search failures that look like "no results found". The `[ERROR]` stderr prefix (added in POC fix) makes this visible but doesn't recover.

**Fix:** Add exponential backoff with 2-3 retries. Distinguish retryable errors (429, 503, timeout) from permanent ones (404, 400). Consider `tenacity` or `urllib3.util.retry`.

---

## Pagination / Completeness Limits

**Files:** `skills/biorxiv.py` (cursor cap at 1000), `skills/openalex.py` (50 per page, no pagination loop)

- bioRxiv: Hard cursor cap at 1000 means searches over large date ranges may miss relevant papers beyond the first 1000 API results.
- OpenAlex: Max 50 results per request, no pagination loop — `max_results > 50` silently caps at 50.
- PubMed: No pagination issue (single `esearch` call returns IDs up to `retmax`), but `retmax` is unbounded — very large requests may timeout.

**Risk:** Incomplete search results without the user knowing. For POC this is acceptable since agents typically request 25 results.

**Fix:** Add pagination loops for OpenAlex. Raise bioRxiv cursor cap or make it configurable. Add `retmax` ceiling for PubMed.

---

## No Tests for Search/Parsing Edge Cases

**Files:** All `skills/*.py`

No test suite exists. Known edge cases that should be tested:

- **bioRxiv:** Empty query, single-character query, query with only stopwords, API returning malformed JSON, papers with missing fields (no abstract, no authors)
- **PubMed:** XML with missing elements (no abstract, no authors, no year), `MedlineDate` format variations, unicode in titles/abstracts, empty PMID list to `fetch_details`
- **OpenAlex:** Inverted index abstract reconstruction with edge cases (empty index, single word), `None` values in nested fields (already partially handled with `or {}`), works with no primary location

**Fix:** Add `pytest` test suite with mocked API responses for each edge case. Start with the parsing functions (`_parse_pubmed_xml`, `_reconstruct_abstract`, `_parse_work`) since those are pure functions that are easy to test.

---

## Rate Limiting Is Per-Process Only

**Files:** `skills/pubmed.py`, `skills/openalex.py`

Rate limiting uses module-level `_last_request_time` — works within a single process but not across concurrent agent spawns. If the Orchestrator spawns multiple Researcher agents simultaneously, they could independently exceed API rate limits.

**Risk:** 429 errors from APIs. Low risk in current architecture (one Researcher per round) but would matter if parallelism increases.

**Fix:** File-based lock or shared rate limiter if concurrent search agents are needed.

---

## bioRxiv Client-Side Filtering

**File:** `skills/biorxiv.py`

The bioRxiv API has no server-side full-text search. The current approach fetches pages of recent papers and filters client-side by keyword matching. This is inherently incomplete — it only searches papers the API returns in date order, not all papers matching the query.

**Risk:** Missing relevant older papers or papers outside the cursor window. The 1000-result cursor cap compounds this.

**Fix:** For production, consider using the bioRxiv content API with subject-area filtering, or supplementing with a third-party search index (e.g., Europe PMC covers bioRxiv preprints with proper full-text search).
