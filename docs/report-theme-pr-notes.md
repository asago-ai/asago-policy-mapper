# Theme grouping: notes for the report PR

Include the methodology and coverage limitations below in the PR description when opening the report PR. Partial mapping coverage is a known limitation reviewers need to see.

## How grouping is built

- The existing `src/asago_policy_mapper/data/risk_to_category.sssom.tsv` links risk IDs to NIST AI RMF, OWASP LLM, OWASP ASI and AILuminate categories. It combines Nexus mappings with reviewed project additions.
- The new `src/asago_policy_mapper/data/report_themes.yaml` adds eight curated Asago themes and explicitly maps those categories to them. These are presentation groupings chosen by this project.
- Only `exactMatch`, `closeMatch` and `broadMatch` links are used, following the existing evaluation mapping policy. Weak `relatedMatch` links are excluded.
- `extract/report_themes.py` joins the two mappings when generating HTML from saved results. It preserves the category links for inspection inside each finding. No extraction or LLM rerun, labelled customer policy or live Nexus access is required; saved extraction data and evaluation counts are unchanged.
- Full variant IDs use their own mappings. There is no inference from risk names or synthetic variant parents.
- The overview uses a compact clickable theme bar chart alongside the taxonomy and grounding charts. Coverage and methodology are kept in the collapsed **Technical details → Theme grouping** section; individual findings retain their source category links.

## Observed coverage in the current example

Using `output/st-johns-openai/risk-extraction.json` and theme mapping version 1:

| Measure | Matched risk entries |
| --- | ---: |
| Total | 65 |
| Assigned at least one theme | 46 (70.8%) |
| Other / not yet grouped | 19 (29.2%) |
| Assigned multiple themes (subset of the 46) | 10 |

The 19 ungrouped entries comprise 11 Credo UCF, 6 MIT AI Risk Repository, 1 IBM Risk Atlas and 1 custom hiring taxonomy entry. The sample file is a local preview artifact, not a committed test fixture.

These figures describe mapping availability for this saved example only. They are not overall catalog coverage, extraction recall, policy coverage or an accuracy estimate. Recalculate them if the source results or mappings change before the PR is opened.

## Limitations and review points

- Coverage is incomplete and varies by taxonomy. Custom risks currently lack category mappings. All unmatched entries remain accessible through **Other / not yet grouped**; they are not discarded or assigned a guessed theme.
- Several category systems are combined into one curated theme vocabulary. Reviewers should inspect these choices and the underlying mappings; strong relationship types do not by themselves establish that every grouping is semantically correct.
- One risk may belong to multiple themes. Theme totals overlap, while the filtered findings list includes each matched risk once. Counts remain counts of taxonomy entries, not distinct real-world issues.
- Themes with zero matches are omitted. Their absence does not establish that the policy lacks those topics, and the view is not a completeness or compliance assessment.
- Automated checks cover mapping application, current category coverage, variant handling, overlapping selections and UI behaviour. They do not establish the semantic accuracy of every source mapping. Future mapping additions need review and refreshed coverage figures.
