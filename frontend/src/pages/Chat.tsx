import { useEffect, useRef, useState } from "react";
import {
  DocInfo, MessageInfo, SessionInfo,
  listDocuments, listMessages, listSessions, streamAI, uploadDocument,
} from "../api/aiClient";
import TypingIndicator from "../components/TypingIndicator";

export default function Chat() {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [activeSession, setActiveSession] = useState<string | undefined>();
  const [messages, setMessages] = useState<MessageInfo[]>([]);
  const [docs, setDocs] = useState<DocInfo[]>([]);
  const [input, setInput] = useState("");
  const [streamingText, setStreamingText] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const refreshSidebar = () => {
    listSessions().then((r) => setSessions(r.data)).catch(() => {});
    listDocuments().then((r) => setDocs(r.data)).catch(() => {});
  };
  useEffect(refreshSidebar, []);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, streamingText]);

  const openSession = async (id: string) => {
    setActiveSession(id);
    setMessages((await listMessages(id)).data);
  };

  const send = async () => {
    const question = input.trim();
    if (!question || streamingText !== null) return;
    setInput("");
    setError("");
    setMessages((m) => [...m, { id: "tmp-u", role: "user", content: question, created_at: "" }]);
    setStreamingText("");
    let acc = "";
    try {
      await streamAI(question, activeSession,
        (t) => { acc += t; setStreamingText(acc); },
        async (sid) => {
          setActiveSession(sid);
          setStreamingText(null);
          setMessages((await listMessages(sid)).data);
          refreshSidebar();
        });
    } catch (e: any) {
      setStreamingText(null);
      setError(e.message || "Query failed");
    }
  };

  const onUpload = async (file: File) => {
    setUploading(true);
    setError("");
    try {
      await uploadDocument(file);
      refreshSidebar();
    } catch (e: any) {
      setError(e.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex gap-4 h-[calc(100vh-8rem)]">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 border rounded-xl bg-white p-3 overflow-y-auto">
        <label className="block border-2 border-dashed rounded-lg p-3 text-center text-sm text-gray-500 cursor-pointer hover:border-blue-400">
          {uploading ? "Uploading…" : "＋ Upload PDF / TXT"}
          <input type="file" accept=".pdf,.txt" className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) onUpload(f); e.target.value = ""; }} />
        </label>
        <div className="mt-3">
          <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Documents</p>
          {docs.map((d) => (
            <div key={d.id} className="text-sm truncate py-0.5" title={d.filename}>
              📄 {d.filename} <span className="text-xs text-gray-400">({d.status})</span>
            </div>
          ))}
        </div>
        <div className="mt-3">
          <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Chats</p>
          <button onClick={() => { setActiveSession(undefined); setMessages([]); }}
            className="w-full text-left text-sm py-1 px-2 rounded hover:bg-gray-100 text-blue-600">
            ＋ New chat
          </button>
          {sessions.map((s) => (
            <button key={s.id} onClick={() => openSession(s.id)}
              className={`w-full text-left text-sm truncate py-1 px-2 rounded hover:bg-gray-100 ${s.id === activeSession ? "bg-blue-50 text-blue-700" : ""}`}>
              {s.title}
            </button>
          ))}
        </div>
      </aside>

      {/* Chat window */}
      <section className="flex-1 flex flex-col border rounded-xl bg-white">
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && streamingText === null && (
            <p className="text-gray-400 text-sm mt-8 text-center">
              Upload a document, then ask a question about it.
            </p>
          )}
          {messages.map((m, i) => (
            <div key={m.id + i} className={`max-w-[80%] rounded-xl px-4 py-2 text-sm whitespace-pre-wrap ${
              m.role === "user" ? "ml-auto bg-blue-600 text-white" : "bg-gray-100 text-gray-900"}`}>
              {m.content}
            </div>
          ))}
          {streamingText !== null && (
            <div className="max-w-[80%] rounded-xl px-4 py-2 text-sm bg-gray-100 whitespace-pre-wrap">
              {streamingText || <TypingIndicator />}
            </div>
          )}
          <div ref={bottomRef} />
        </div>
        {error && <p className="text-sm text-red-600 px-4">{error}</p>}
        <div className="border-t p-3 flex gap-2">
          <input
            className="flex-1 border rounded-lg px-3 py-2 text-sm"
            placeholder="Ask about your documents…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
          />
          <button onClick={send} disabled={streamingText !== null}
            className="bg-blue-600 disabled:bg-gray-300 text-white rounded-lg px-4 py-2 text-sm">
            Send
          </button>
        </div>
      </section>
    </div>
  );
}
