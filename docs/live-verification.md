# Hosted live SEC verification

Verified October 12, 2026 through the Render API, using configured SEC headers and shared rate limiting:

| Ticker | Earlier/later report year | Result |
|---|---|---|
| AAPL | 2024/2025 | Discovery, HTML extraction, comparison successful |
| MSFT | 2025/2026 | Discovery, HTML extraction, comparison successful |
| GOOGL | 2024/2025 | Discovery, HTML extraction, comparison successful |
| AMZN | 2024/2025 | Discovery, HTML extraction, comparison successful |
| META | 2024/2025 | Discovery, HTML extraction, comparison successful |
| NVDA | 2025/2026 | Discovery, HTML extraction, comparison successful |
| TSLA | 2024/2025 | Discovery, HTML extraction, comparison successful |

The public browser displayed Apple's real comparison and original SEC document links. These smoke checks verify the pipeline, not semantic accuracy or every historical section boundary. The application remains a paragraph comparison tool; company summaries, topic grouping, and watchlist analysis are not implemented yet.

Run `python verify_hosted.py https://ten-k-detective-api.onrender.com` from the backend directory for an explicit network smoke test. It is deliberately separate from offline pytest tests.
