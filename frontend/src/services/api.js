const API = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
export async function uploadDocument(file) {
  const body = new FormData(); body.append("file", file);
  const response = await fetch(`${API}/documents/upload`, { method: "POST", body });
  if (!response.ok) throw new Error((await response.json()).detail || "Upload failed");
  return response.json();
}
export async function listDocuments() { const response = await fetch(`${API}/documents`); return response.json(); }
export async function sendChat(message, conversationId) {
  const response = await fetch(`${API}/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message, conversation_id: conversationId }) });
  if (!response.ok) throw new Error((await response.json()).detail || "Chat failed");
  return response.json();
}

