// AI module client — scaffold-owned, matches ai/routes.py exactly.
import { api } from "./client";
import { API_BASE } from "../config";

export interface Citation { chunk_index: number; document_id: string; score: number; preview: string }
export interface QueryResponse { session_id: string; answer: string; citations: Citation[] }
export interface DocInfo { id: string; filename: string; status: string; created_at: string }
export interface SessionInfo { id: string; title: string; created_at: string }
export interface MessageInfo { id: string; role: "user" | "assistant"; content: string; created_at: string }

export const uploadDocument = (file: File) => {
  const form = new FormData();
  form.append("file", file);
  return api.post<{ document_id: string; filename: string; chunks_indexed: number }>(
    "/api/ai/upload", form, { headers: { "Content-Type": "multipart/form-data" } });
};
export const listDocuments = () => api.get<DocInfo[]>("/api/ai/documents");
export const queryAI = (question: string, session_id?: string) =>
  api.post<QueryResponse>("/api/ai/query", { question, session_id });
export const listSessions = () => api.get<SessionInfo[]>("/api/ai/sessions");
export const listMessages = (sessionId: string) =>
  api.get<MessageInfo[]>(`/api/ai/sessions/${sessionId}/messages`);

// Streaming via fetch (SSE over POST).
export async function streamAI(
  question: string,
  sessionId: string | undefined,
  onToken: (t: string) => void,
  onDone: (sessionId: string) => void
): Promise<void> {
  const token = localStorage.getItem("token");
  const resp = await fetch(`${API_BASE}/api/ai/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ question, session_id: sessionId }),
  });
  if (!resp.ok || !resp.body) throw new Error("Stream failed");
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (!line.startsWith("data:")) continue;
      const data = JSON.parse(line.slice(5));
      if (data.token) onToken(data.token);
      if (data.done) onDone(data.session_id);
    }
  }
}
