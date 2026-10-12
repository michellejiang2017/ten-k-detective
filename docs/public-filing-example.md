# Real public filing example: Apple

Public SEC reports reviewed via web browsing on October 12, 2026:

- [2024 10-K, period ended September 28, 2024](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm)
- [2025 10-K, period ended September 27, 2025](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

In Item 1A, locate the discussion of political events and international trade. The 2024 report describes tariffs and import/export restrictions generally, including past U.S.–China disputes. The 2025 report adds a discussion of tariffs announced during 2025, reciprocal measures, potential sector-based measures, and effects on supply chains, input availability, pricing, and margins.

This is a useful manual comparison target: the topic existed before, while the later report elaborates on developments. Do not label the entire topic a newly introduced risk just because some paragraphs are added. Read each surrounding section before interpreting differences.

These links and observations were verified through web browsing, not the app's SEC client. They do not establish automated ticker/submissions/archive access from the app. Real filings are not bundled or substituted for the clearly labeled mock fixtures.

## Local verification

- 8 offline backend tests passed.
- TypeScript check and Vite production build passed.
- Browser smoke test: DEMO lookup → 2024/2025 selection → two change groups and source links displayed correctly.
- Live client requires an actual application/contact User-Agent; that identity is not configured yet.

Next exercise: read the two linked trade-risk sections side by side and identify which passages changed. Later, use these filings for extraction regression tests after acquiring their HTML through a compliant request path.
