"""Opt-in network smoke test: python verify_hosted.py https://your-api-host."""
import sys
import httpx

if len(sys.argv) != 2:
    raise SystemExit('Pass the hosted API base URL explicitly. This test makes live requests.')
base = sys.argv[1].rstrip('/')
failed = []
with httpx.Client(timeout=60) as client:
    for ticker in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA']:
        discovery = client.get(f'{base}/api/companies/{ticker}')
        discovery.raise_for_status()
        years = [f['year'] for f in discovery.json()['filings'][:2]]
        response = client.get(f'{base}/api/compare/{ticker}', params={'before': min(years), 'after': max(years)})
        result = response.json()
        if response.is_success:
            print(ticker, years, 'OK', len(result['changes']), 'change groups', flush=True)
        else:
            failed.append(ticker)
            print(ticker, years, response.status_code, result.get('detail'), flush=True)
if failed:
    raise SystemExit('Comparison failed: ' + ', '.join(failed))
