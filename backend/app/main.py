import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from .sec import sec, SecError
from .extract import extract_sections, compare

app = FastAPI(title='10-K Detective')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173'], allow_methods=['GET'])
FIXTURES = Path(__file__).parent.parent / 'fixtures'

def mode():
    value = os.getenv('DATA_MODE', 'mock')
    if value not in ('mock', 'live'):
        raise HTTPException(503, 'DATA_MODE must be mock or live.')
    return value

def mock_filings():
    return [{'year': year, 'report_date': f'{year}-12-31', 'filing_date': f'{year+1}-02-15',
             'accession': f'SYNTHETIC-{year}', 'url': f'/api/mock-filings/{year}'} for year in [2025, 2024]]

async def lookup(ticker):
    ticker = ticker.strip().upper()
    if mode() == 'mock':
        if ticker != 'DEMO':
            raise LookupError('Mock mode supports only DEMO, a fictional company.')
        return {'ticker': 'DEMO', 'name': 'Demo Devices (fictional)', 'cik': '0000000000'}, mock_filings()
    company = await sec.company(ticker)
    return company, await sec.filings(company['cik'])

@app.get('/api/health')
def health():
    return {'status': 'ok', 'mode': mode()}

@app.get('/api/mock-filings/{year}', response_class=HTMLResponse)
def mock_document(year: int):
    if year not in (2024, 2025):
        raise HTTPException(404, 'Mock filing not found.')
    return (FIXTURES / f'{year}.html').read_text(encoding='utf-8')

@app.get('/api/companies/{ticker}')
async def company(ticker: str):
    try:
        company, filings = await lookup(ticker)
        return {'mode': mode(), 'company': company, 'filings': filings}
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except SecError as exc:
        raise HTTPException(502, str(exc))

@app.get('/api/compare/{ticker}')
async def comparison(ticker: str, before: int = Query(..., ge=1994, le=2100), after: int = Query(..., ge=1994, le=2100)):
    if before >= after:
        raise HTTPException(422, 'Select two years in chronological order.')
    try:
        company, filings = await lookup(ticker)
        selected = []
        for year in (before, after):
            filing = next((f for f in filings if f['year'] == year), None)
            if not filing:
                raise LookupError(f'No original 10-K found for report year {year}.')
            html = (FIXTURES / f'{year}.html').read_text(encoding='utf-8') if mode() == 'mock' else await sec.get(filing['url'])
            selected.append({**filing, 'sections': extract_sections(html)})
        return {'mode': mode(), 'company': company, 'before': selected[0], 'after': selected[1],
                'changes': compare(selected[0]['sections']['1a'], selected[1]['sections']['1a']),
                'method': 'Exact paragraph comparison after whitespace and case normalization. Changes are textual evidence, not conclusions about risk severity.',
                'warning': 'Section boundaries are heuristic. Review the extracted sections against each original filing.'}
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except SecError as exc:
        raise HTTPException(502, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc))
