import asyncio
import json
from pathlib import Path
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.extract import extract_sections, compare
from app.sec import SecClient, SecError

client = TestClient(app)
@pytest.fixture(autouse=True)
def mock_mode(monkeypatch):
    monkeypatch.setenv('DATA_MODE', 'mock')

def test_full_demo():
    discovery = client.get('/api/companies/demo').json()
    assert discovery['mode'] == 'mock'
    assert [f['year'] for f in discovery['filings']] == [2025, 2024]
    response = client.get('/api/compare/DEMO?before=2024&after=2025')
    assert response.status_code == 200
    result = response.json()
    assert [c['kind'] for c in result['changes']] == ['replace', 'insert']
    assert 'single supplier' in result['changes'][0]['before'][0]['text']
    assert result['changes'][1]['after'][0]['paragraph'] == 4
    assert len(result['before']['sections']['1a']) == 3
    assert client.get(result['before']['url']).status_code == 200

def test_errors():
    assert client.get('/api/companies/AAPL').status_code == 404
    assert client.get('/api/compare/DEMO?before=2025&after=2024').status_code == 422
    assert client.get('/api/compare/DEMO?before=2023&after=2025').status_code == 404

def test_extraction_rejects_missing_end():
    with pytest.raises(ValueError):
        extract_sections('<h2>Item 1A. Risk Factors</h2><p>' + 'risk ' * 100 + '</p>')

def test_inline_and_split_headings():
    html = '<h2>Item 1.</h2><p>Business</p><p>' + 'business ' * 20 + '</p><h2>Item 1A.</h2><p>Risk Factors</p><p>Cyber <b>risk</b> ' + 'disclosure ' * 20 + '</p><h2>Item 2. Properties</h2>'
    sections = extract_sections(html)
    assert sections['1a'][0].startswith('Cyber risk')

def test_normalization_and_removal():
    assert compare(['Same  TEXT'], ['same text']) == []
    assert compare(['removed'], [])[0]['kind'] == 'delete'

def test_live_requires_identity(monkeypatch):
    monkeypatch.delenv('SEC_USER_AGENT', raising=False)
    with pytest.raises(SecError):
        asyncio.run(SecClient().get('https://data.sec.gov/test'))

def test_live_discovery_historical_and_amendments(monkeypatch):
    sec = SecClient()
    recent = {'form':['10-K/A','10-K'], 'reportDate':['2025-12-31']*2,
              'filingDate':['2026-03-01','2026-02-01'], 'accessionNumber':['a','0001-02-03'], 'primaryDocument':['a.htm','report.htm']}
    old = {**recent, 'form':['10-K'], 'reportDate':['2024-12-31'], 'filingDate':['2025-02-01'],
           'accessionNumber':['0001-01-03'], 'primaryDocument':['old.htm']}
    async def fake(url):
        return old if url.endswith('old.json') else {'filings':{'recent':recent,'files':[{'name':'old.json'}]}}
    monkeypatch.setattr(sec, 'json', fake)
    rows = asyncio.run(sec.filings('0000000001'))
    assert [f['year'] for f in rows] == [2025,2024]
    assert rows[0]['url'].endswith('/00010203/report.htm')

def test_headers_cache_and_block(monkeypatch):
    monkeypatch.setenv('SEC_USER_AGENT','Detective developer@real-domain.test')
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, text='cached')
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    async def run():
        sec = SecClient()
        assert await sec.get('https://data.sec.gov/test') == 'cached'
        assert await sec.get('https://data.sec.gov/test') == 'cached'
    asyncio.run(run())
    assert len(calls) == 1
    assert calls[0].headers['User-Agent'].startswith('Detective')
