import asyncio
import os
import time
import httpx

class SecError(Exception):
    pass

class SecClient:
    """One process-wide client/limiter; run one worker for this local MVP."""
    def __init__(self):
        self.lock = asyncio.Lock()
        self.last = 0.0
        self.cache = {}

    async def get(self, url):
        cached = self.cache.get(url)
        if cached and time.monotonic() - cached[0] < 3600:
            return cached[1]
        agent = os.getenv('SEC_USER_AGENT', '')
        if '@' not in agent or 'example.com' in agent:
            raise SecError('Live mode requires SEC_USER_AGENT with your application name and real contact email.')
        async with self.lock:
            # Serialize ALL SEC hosts; at most two requests per second.
            await asyncio.sleep(max(0, 0.5 - (time.monotonic() - self.last)))
            self.last = time.monotonic()
            try:
                async with httpx.AsyncClient(timeout=30, headers={'User-Agent': agent, 'Accept-Encoding': 'gzip, deflate'}) as client:
                    response = await client.get(url)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise SecError('SEC request failed or was blocked. Try later or use mock mode; no automatic fallback was applied.') from exc
            self.cache[url] = (time.monotonic(), response.text)
            return response.text

    async def json(self, url):
        import json
        try:
            return json.loads(await self.get(url))
        except ValueError as exc:
            raise SecError('SEC returned an invalid JSON response.') from exc

    async def company(self, ticker):
        data = await self.json('https://www.sec.gov/files/company_tickers.json')
        for company in data.values():
            if company['ticker'].upper() == ticker:
                return {'ticker': ticker, 'name': company['title'], 'cik': str(company['cik_str']).zfill(10)}
        raise LookupError('Ticker not found in the SEC ticker map.')

    async def filings(self, cik):
        data = await self.json(f'https://data.sec.gov/submissions/CIK{cik}.json')
        batches = [data['filings']['recent']]
        # Historical submission files have the same parallel arrays at their root.
        for entry in data['filings'].get('files', []):
            batches.append(await self.json('https://data.sec.gov/submissions/' + entry['name']))
        results = {}
        for batch in batches:
            for i, form in enumerate(batch['form']):
                if form != '10-K':
                    continue
                report = batch['reportDate'][i]
                if not report:
                    continue
                accession = batch['accessionNumber'][i]
                document = batch['primaryDocument'][i]
                row = {'year': int(report[:4]), 'report_date': report, 'filing_date': batch['filingDate'][i],
                       'accession': accession, 'url': f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace("-", "")}/{document}'}
                if row['year'] not in results or row['filing_date'] > results[row['year']]['filing_date']:
                    results[row['year']] = row
        return sorted(results.values(), key=lambda x: x['year'], reverse=True)

sec = SecClient()
