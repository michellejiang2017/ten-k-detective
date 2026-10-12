"""Export deterministic, visibly synthetic API responses for GitHub Pages."""
import asyncio
import json
import os
import shutil
from pathlib import Path
from app.main import company, comparison, FIXTURES

os.environ['DATA_MODE'] = 'mock'
output = Path(__file__).resolve().parent.parent / 'frontend/public/demo'
output.mkdir(parents=True, exist_ok=True)

async def export():
    discovery = await company('DEMO')
    result = await comparison('DEMO', 2024, 2025)
    for filing in discovery['filings'] + [result['before'], result['after']]:
        filing['url'] = f'./demo/{filing["year"]}.html'
    for filename, data in [('company.json', discovery), ('comparison.json', result)]:
        (output / filename).write_text(json.dumps(data, indent=2), encoding='utf-8')
    for year in (2024,2025):
        shutil.copyfile(FIXTURES / f'{year}.html', output / f'{year}.html')

asyncio.run(export())
