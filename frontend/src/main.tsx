import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';
type Filing = {year:number;report_date:string;filing_date:string;accession:string;url:string;sections?:Record<string,string[]>};
type Discovery = {mode:string;company:{name:string;ticker:string;cik:string};filings:Filing[]};
type Evidence = {paragraph:number;text:string};
type Result = {mode:string;before:Filing;after:Filing;changes:{kind:string;before:Evidence[];after:Evidence[]}[];method:string;warning:string};
async function get<T>(url:string):Promise<T> {
  const staticDemo = (import.meta as unknown as {env:Record<string,string>}).env.VITE_STATIC_DEMO === 'true';
  let requestUrl = url;
  if (staticDemo) {
    const path = url.split('?')[0];
    if (!path.endsWith('/DEMO')) throw new Error('The hosted demo supports only DEMO. Run the FastAPI backend locally for live SEC mode.');
    requestUrl = path.startsWith('/api/companies/') ? './demo/company.json' : './demo/comparison.json';
  }
  const response = await fetch(requestUrl);
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Invalid request. Check your ticker and selected years.');
  return data;
}
function App(){
  const [ticker,setTicker]=useState('DEMO');
  const [discovery,setDiscovery]=useState<Discovery|null>(null);
  const [before,setBefore]=useState(''); const [after,setAfter]=useState('');
  const [result,setResult]=useState<Result|null>(null);
  const [busy,setBusy]=useState(false); const [error,setError]=useState('');
  async function lookup(event:React.FormEvent){
    event.preventDefault();setBusy(true);setError('');setResult(null);setDiscovery(null);
    try {const d=await get<Discovery>(`/api/companies/${encodeURIComponent(ticker.trim())}`);setDiscovery(d);setBefore(String(d.filings[1]?.year??''));setAfter(String(d.filings[0]?.year??''));}
    catch(e){setError((e as Error).message);}finally{setBusy(false);}
  }
  async function compare(){
    if(!discovery)return;setBusy(true);setError('');setResult(null);
    try{setResult(await get<Result>(`/api/compare/${encodeURIComponent(discovery.company.ticker)}?before=${before}&after=${after}`));}
    catch(e){setError((e as Error).message);}finally{setBusy(false);}
  }
  return <main><header><span>FILING EVIDENCE · MVP 01</span><h1>10-K Detective</h1><p>See how a company's risk disclosures changed between two annual reports.</p></header>
    <form onSubmit={lookup}><label>Ticker <input value={ticker} onChange={e=>setTicker(e.target.value)} disabled={busy} required maxLength={20}/></label><button disabled={busy}>Find 10-Ks</button></form>
    <p className="hint">Local mock mode uses DEMO, a fictional company. Live mode requires backend configuration.</p>
    {busy&&<p role="status">Loading filing evidence…</p>}{error&&<p role="alert" className="error">{error}</p>}
    {discovery&&<section><h2>{discovery.company.name}</h2><p className="badge">{discovery.mode==='mock'?'SYNTHETIC DEMO DATA':'LIVE SEC DATA'} · CIK {discovery.company.cik}</p>
      <div className="controls"><label>Earlier report year<select value={before} onChange={e=>{setBefore(e.target.value);setResult(null);}} disabled={busy}><option value="">Choose year</option>{discovery.filings.map(f=><option key={f.year}>{f.year}</option>)}</select></label>
      <label>Later report year<select value={after} onChange={e=>{setAfter(e.target.value);setResult(null);}} disabled={busy}><option value="">Choose year</option>{discovery.filings.map(f=><option key={f.year}>{f.year}</option>)}</select></label>
      <button onClick={compare} disabled={busy||!before||!after||Number(before)>=Number(after)}>Compare risk factors</button></div>
      {discovery.filings.length<2&&<p>At least two report years are required.</p>}</section>}
    {result&&<section><h2>Item 1A · Risk Factors</h2><p>{result.method}</p><p className="hint">{result.warning}</p>
      <div className="columns">{[result.before,result.after].map(f=><article key={f.year}><h3>{f.year} report</h3><p>Period ended {f.report_date} · Filed {f.filing_date}</p><a href={f.url} target="_blank" rel="noreferrer">Open {f.accession}</a></article>)}</div>
      <h3>{result.changes.length} changed paragraph groups</h3>{!result.changes.length&&<p>No textual differences under this comparison method.</p>}
      {result.changes.map((change,i)=><article className="change" key={i}><h3>{change.kind==='replace'?'Replaced text':change.kind==='insert'?'Added text':'Removed text'}</h3><div className="columns">{(['before','after'] as const).map(side=><div key={side} className={side}><h4>{side==='before'?result.before.year:result.after.year}</h4>{change[side].length?change[side].map(p=><blockquote key={p.paragraph}><a href={(side==='before'?result.before:result.after).url} target="_blank" rel="noreferrer">Item 1A · extracted paragraph {p.paragraph}</a><p>{p.text}</p></blockquote>):<p>No corresponding text.</p>}</div>)}</div></article>)}
      <details><summary>Review complete extracted sections</summary>{[result.before,result.after].map(f=><div key={f.year}><h3>{f.year}</h3>{Object.entries(f.sections??{}).map(([item,paragraphs])=><div key={item}><h4>Item {item.toUpperCase()}</h4>{paragraphs.map((p,i)=><p key={i}>{i+1}. {p}</p>)}</div>)}</div>)}</details>
    </section>}<footer>Text changes can reflect formatting or reordering. Review original filings before drawing conclusions. AI Q&A is deferred.</footer></main>;
}
createRoot(document.getElementById('root')!).render(<App/>);
