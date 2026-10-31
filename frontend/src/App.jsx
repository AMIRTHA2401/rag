import { useEffect, useRef, useState } from "react";
import { FileText, Send, Upload, Bot, User, Trash2, Loader2 } from "lucide-react";
import { listDocuments, sendChat, uploadDocument } from "./services/api";

const stages = ["Analyzing question", "Routing query", "Rewriting query", "Retrieving documents", "Evaluating relevance", "Generating answer", "Verifying answer"];

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const fileInput = useRef(null);

  useEffect(() => { listDocuments().then(setDocuments).catch(() => setError("Could not load documents")); }, []);
  async function handleUpload(event) {
    const file = event.target.files?.[0]; if (!file) return;
    setError(""); setStatus("Uploading and indexing document...");
    try { const doc = await uploadDocument(file); setDocuments((current) => [...current.filter((item) => item.id !== doc.id), doc]); }
    catch (err) { setError(err.message); } finally { setStatus(""); }
  }
  async function handleSend(event) {
    event.preventDefault(); const text = input.trim(); if (!text || busy) return;
    setMessages((current) => [...current, { role: "user", content: text }]); setInput(""); setBusy(true); setError("");
    try {
      const result = await sendChat(text, conversationId); setConversationId(result.conversation_id);
      setMessages((current) => [...current, { role: "assistant", content: result.answer, sources: result.sources, stages: result.stages }]);
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  return <div className="min-h-screen bg-slate-950 text-slate-100 flex">
    <aside className="w-80 border-r border-slate-800 p-5 hidden md:flex flex-col gap-6">
      <div><div className="flex items-center gap-3 text-xl font-bold"><Bot className="text-cyan-400" /> Atlas RAG</div><p className="text-slate-400 text-sm mt-2">Grounded answers from your documents.</p></div>
      <section><h2 className="font-semibold mb-3">Knowledge base</h2><button onClick={() => fileInput.current?.click()} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); const file = event.dataTransfer.files?.[0]; if (file) handleUpload({ target: { files: [file] } }); }} className="w-full border border-dashed border-cyan-700 rounded-xl p-5 text-sm text-cyan-300 hover:bg-cyan-950/40"><Upload className="mx-auto mb-2" />Drop or choose a document<input ref={fileInput} type="file" accept=".pdf,.txt,.docx" onChange={handleUpload} className="hidden" /></button><div className="mt-4 space-y-2">{documents.map((doc) => <div key={doc.id} className="flex items-center gap-2 text-sm bg-slate-900 rounded-lg p-2"><FileText size={16} className="text-cyan-400" /><span className="truncate">{doc.name}</span><span className="ml-auto text-xs text-slate-500">{doc.chunks}</span></div>)}</div></section>
      <div className="mt-auto text-xs text-slate-500">Ollama · ChromaDB · LangGraph</div>
    </aside>
    <main className="flex-1 flex flex-col max-w-5xl mx-auto w-full">
      <header className="p-5 border-b border-slate-800"><h1 className="text-2xl font-semibold">Document assistant</h1><p className="text-slate-400 text-sm">Ask about your files or start a general conversation.</p></header>
      <div className="flex-1 overflow-y-auto p-5 space-y-5">{messages.length === 0 && <div className="h-full grid place-items-center text-center text-slate-500"><Bot size={48} className="mx-auto mb-3 text-cyan-500" /><p>Upload a document, then ask a question.</p></div>}{messages.map((message, index) => <div key={index} className={`flex gap-3 ${message.role === "user" ? "justify-end" : ""}`}><div className={`max-w-3xl rounded-2xl p-4 ${message.role === "user" ? "bg-cyan-700" : "bg-slate-900 border border-slate-800"}`}>{message.role === "user" ? <User size={16} className="mb-2" /> : <Bot size={16} className="mb-2 text-cyan-400" />}<p className="whitespace-pre-wrap leading-7">{message.content}</p>{message.stages?.length > 0 && <details className="mt-4 text-xs text-slate-400"><summary className="cursor-pointer">Agent execution</summary><div className="mt-2 space-y-1">{stages.map((stage) => <div key={stage} className={message.stages.includes(stage) ? "text-cyan-300" : ""}>{message.stages.includes(stage) ? "✓ " : "○ "}{stage}</div>)}</div></details>}{message.sources?.length > 0 && <details className="mt-3 text-xs"><summary className="cursor-pointer text-cyan-300">Sources ({message.sources.length})</summary><div className="mt-2 space-y-2">{message.sources.map((source, sourceIndex) => <div key={sourceIndex} className="border-l-2 border-cyan-700 pl-2 text-slate-400"><b>{source.document_name}</b>{source.page_number ? ` · page ${source.page_number}` : ""}<p>{source.content}</p></div>)}</div></details>}</div></div>)}</div>
      {error && <div className="mx-5 mb-3 rounded-lg bg-red-950 border border-red-800 p-3 text-red-300 text-sm">{error}</div>}{status && <div className="px-5 pb-3 text-sm text-cyan-300">{status}</div>}
      <form onSubmit={handleSend} className="p-5 border-t border-slate-800 flex gap-3"><input value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ask a question..." className="flex-1 rounded-xl bg-slate-900 border border-slate-700 px-4 py-3 outline-none focus:border-cyan-500" /><button disabled={busy} className="rounded-xl bg-cyan-600 px-4 hover:bg-cyan-500 disabled:opacity-50">{busy ? <Loader2 className="animate-spin" /> : <Send />}</button></form>
    </main>
  </div>;
}
