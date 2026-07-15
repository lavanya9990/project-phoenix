"use client";
import { useEffect, useState } from "react";
import { BookOpen, Check, Clipboard, Download, ExternalLink, FileText, Search, Trash2 } from "lucide-react";
import { Research, researchApi } from "@/lib/api";
import { exportResearchPdf } from "@/lib/pdf";

const steps = ["Plan", "Research", "Analyze", "Fact-check", "Write"];
export default function Home() {
  const [topic, setTopic] = useState(""); const [depth, setDepth] = useState("standard");
  const [history, setHistory] = useState<Research[]>([]); const [selected, setSelected] = useState<Research>();
  const [loading, setLoading] = useState(false); const [error, setError] = useState("");
  const [pdfLoading, setPdfLoading] = useState(false);
  const refresh = () => researchApi.list().then(setHistory).catch(() => setError("Could not connect to the research API."));
  useEffect(() => { void refresh(); }, []);
  async function start() { setLoading(true); setError(""); try { const result = await researchApi.create(topic.trim(), depth); setSelected(result); await refresh(); if (result.status === "failed") setError(result.error_message || "Research failed."); } catch (e) { setError(e instanceof Error ? e.message : "Research failed."); } finally { setLoading(false); } }
  async function remove(id: number) { await researchApi.remove(id); if (selected?.research_id === id) setSelected(undefined); refresh(); }
  function download() { if (!selected) return; const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([selected.final_report], { type: "text/markdown" })); a.download = `phoenix-research-${selected.research_id}.md`; a.click(); URL.revokeObjectURL(a.href); }
  async function downloadPdf() { if (!selected) return; setPdfLoading(true); setError(""); try { await exportResearchPdf(selected); } catch { setError("PDF generation failed. Please try again or use the Markdown download."); } finally { setPdfLoading(false); } }
  return <main>
    <header><div className="brand"><span className="mark"><Search size={19}/></span><div><strong>Phoenix Research</strong><small>Multi-agent intelligence workspace</small></div></div><span className="status"><i/> API workspace</span></header>
    <div className="shell">
      <aside><div className="asideTitle"><span>Research history</span><span>{history.length}</span></div><div className="history">{history.map(item => <div className={`historyItem ${selected?.research_id === item.research_id ? "active" : ""}`} key={item.research_id}><button onClick={() => setSelected(item)}><strong>{item.topic}</strong><small>{new Date(item.created_at).toLocaleDateString()} · {item.research_depth}</small></button><button className="icon" title="Delete research" onClick={() => remove(item.research_id)}><Trash2 size={15}/></button></div>)}{!history.length && <p className="empty">Completed research will appear here.</p>}</div></aside>
      <section className="workspace">
        <div className="composer"><label htmlFor="topic">What would you like to investigate?</label><textarea id="topic" value={topic} onChange={e => setTopic(e.target.value)} placeholder="e.g. AI automation opportunities for dental clinics"/><div className="controls"><div className="segments" aria-label="Research depth">{["quick","standard","deep"].map(x => <button className={depth === x ? "chosen" : ""} onClick={() => setDepth(x)} key={x}>{x}</button>)}</div><button className="primary" disabled={loading || topic.trim().length < 3} onClick={start}><Search size={17}/>{loading ? "Researching..." : "Start research"}</button></div></div>
        {error && <div className="error">{error}</div>}
        {loading && <div className="progress">{steps.map((step, i) => <div key={step}><span>{i === 0 ? <span className="spinner"/> : i + 1}</span><small>{step}</small></div>)}</div>}
        {selected && <div className="results"><div className="resultHead"><div><span className={`badge ${selected.status}`}>{selected.status}</span><h1>{selected.topic}</h1></div>{selected.final_report && <div className="actions"><button title="Copy report" onClick={() => navigator.clipboard.writeText(selected.final_report)}><Clipboard size={17}/></button><button title="Download Markdown" onClick={download}><Download size={17}/></button><button title="Download PDF" aria-label="Download PDF" disabled={pdfLoading} onClick={downloadPdf}><FileText size={17}/><span>PDF</span></button></div>}</div>
          {selected.plan.length > 0 && <section className="block"><h2><BookOpen size={18}/> Research plan</h2><ol>{selected.plan.map((x, i) => <li key={i}><span>{i + 1}</span><div><strong>{x.question}</strong><p>{x.rationale}</p></div></li>)}</ol></section>}
          {selected.final_report && <section className="block report"><h2><Check size={18}/> Final report</h2><pre>{selected.final_report}</pre></section>}
          {selected.sources.length > 0 && <section className="block"><h2><ExternalLink size={18}/> Sources <small>{selected.sources.length}</small></h2><div className="sources">{selected.sources.map(source => <a href={source.url} target="_blank" rel="noreferrer" key={source.url}><strong>{source.title}</strong><p>{source.snippet}</p><span>{new URL(source.url).hostname}<ExternalLink size={13}/></span></a>)}</div></section>}
        </div>}
        {!selected && !loading && <div className="welcome"><Search size={28}/><h1>Start with a question worth answering.</h1><p>Five specialized agents will plan, research, analyze, verify, and write the result.</p></div>}
      </section>
    </div>
  </main>;
}
