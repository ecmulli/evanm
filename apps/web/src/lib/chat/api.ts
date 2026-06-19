// Client API for the chat UI -> /api/bridge proxy -> local claude-bridge.

export type Profile = {
  id: string; name: string; memoryRoot: string; allowedCwds: string;
  defaultModel: string; systemPrompt: string | null;
};
export type Project = {
  id: string; name: string; scope: 'private' | 'shared'; profileId: string | null;
  cwd: string; systemPrompt: string | null; defaultModel: string | null; pinned: number;
};
export type Conversation = {
  id: string; projectId: string; profileId: string; sessionId: string | null;
  title: string; model: string | null; createdAt: number; updatedAt: number;
};
export type Message = {
  id: string; conversationId: string; role: 'user' | 'assistant';
  content: string; attachments: string | null; createdAt: number;
};
export type Question = {
  question: string; header: string; multiSelect: boolean;
  options: { label: string; description: string }[];
};

const j = async (r: Response) => {
  if (!r.ok) throw new Error((await r.json().catch(() => ({})))?.error ?? r.statusText);
  return r.json();
};

export const getProfiles = (): Promise<{ profiles: Profile[] }> =>
  fetch('/api/bridge/profiles').then(j);
export const getProjects = (profileId: string): Promise<{ projects: Project[] }> =>
  fetch(`/api/bridge/projects?profileId=${profileId}`).then(j);
export const getConversations = (profileId: string): Promise<{ conversations: Conversation[] }> =>
  fetch(`/api/bridge/conversations?profileId=${profileId}`).then(j);
export const getMessages = (conversationId: string): Promise<{ messages: Message[] }> =>
  fetch(`/api/bridge/conversations/${conversationId}/messages`).then(j);

export const createConversation = (projectId: string, profileId: string, model?: string): Promise<{ conversation: Conversation }> =>
  fetch('/api/bridge/conversations', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ projectId, profileId, model }),
  }).then(j);

export const createProject = (p: { name: string; cwd: string; scope?: string; profileId?: string }): Promise<{ project: Project }> =>
  fetch('/api/bridge/projects', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify(p),
  }).then(j);

export async function uploadFile(conversationId: string, file: File): Promise<string> {
  const dataBase64 = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve((reader.result as string).split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
  const res = await fetch('/api/bridge/upload', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ conversationId, filename: file.name, dataBase64 }),
  }).then(j);
  return res.path as string;
}

// Fire-and-forget: enqueue a message. The run is owned by the bridge; observe via
// the conversation stream. Safe to call while a turn is in flight (it queues).
export const sendMessage = (body: { conversationId: string; prompt: string; model?: string; attachments?: string[] }): Promise<{ ok: boolean; queued: number }> =>
  fetch('/api/bridge/chat', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  }).then(j);

export type BridgeEvent =
  | { type: 'sync'; running: boolean; queued: number }
  | { type: 'user'; messageId: string; text: string; attachments: string[]; queued: boolean }
  | { type: 'start'; sessionId: string; model: string }
  | { type: 'text'; text: string }
  | { type: 'tool'; name: string }
  | { type: 'questions'; questions: Question[]; toolUseId: string }
  | { type: 'done'; text: string; costUsd?: number; isError?: boolean }
  | { type: 'error'; message: string }
  | { type: 'end' }
  | { type: 'idle' };

// Opens a re-attachable SSE stream for a conversation (cookie-authed via proxy).
// Auto-reconnects (native EventSource). Returns a close fn.
export function openStream(conversationId: string, onEvent: (e: BridgeEvent) => void): () => void {
  const es = new EventSource(`/api/bridge/conversations/${conversationId}/stream`);
  es.onmessage = (m) => { try { onEvent(JSON.parse(m.data)); } catch { /* ignore */ } };
  return () => es.close();
}

// ---- Push ----
export const getVapidKey = (): Promise<{ key: string | null }> => fetch('/api/bridge/push/vapid').then(j);
export const subscribePush = (profileId: string, subscription: PushSubscriptionJSON): Promise<{ ok: boolean }> =>
  fetch('/api/bridge/push/subscribe', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ profileId, subscription }),
  }).then(j);
