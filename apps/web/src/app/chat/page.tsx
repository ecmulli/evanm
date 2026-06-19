'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Plus, Send, Paperclip, Loader, Hash, User, Bell } from 'lucide-react';
import {
  getProfiles, getProjects, getConversations, getMessages,
  createConversation, sendMessage, openStream, uploadFile,
  type Profile, type Project, type Conversation, type Message, type Question, type BridgeEvent,
} from '@/lib/chat/api';
import { Markdown } from '@/components/chat/Markdown';
import { QuestionPanel } from '@/components/chat/QuestionPanel';
import { enablePush } from '@/lib/chat/push-client';

const MODELS = ['sonnet', 'opus', 'haiku'];
type Draft = { text: string; tools: string[] };

export default function ChatPage() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [profileId, setProfileId] = useState('');
  const [projects, setProjects] = useState<Project[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [questions, setQuestions] = useState<{ items: Question[] } | null>(null);
  const [input, setInput] = useState('');
  const [model, setModel] = useState('sonnet');
  const [pending, setPending] = useState<{ name: string; path: string }[]>([]);
  const [running, setRunning] = useState(false);
  const [queued, setQueued] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const seen = useRef<Set<string>>(new Set());

  useEffect(() => { getProfiles().then((r) => { setProfiles(r.profiles); if (r.profiles[0]) setProfileId(r.profiles[0].id); }).catch(() => {}); }, []);

  useEffect(() => {
    if (!profileId) return;
    getProjects(profileId).then((r) => setProjects(r.projects)).catch(() => {});
    getConversations(profileId).then((r) => setConversations(r.conversations)).catch(() => {});
    setActiveId(''); setMessages([]);
  }, [profileId]);

  // Load history + attach the live stream whenever the active conversation changes.
  useEffect(() => {
    if (!activeId) { setMessages([]); setDraft(null); setQuestions(null); return; }
    seen.current = new Set();
    setDraft(null); setQuestions(null); setRunning(false); setQueued(0);
    getMessages(activeId).then((r) => {
      r.messages.forEach((m) => seen.current.add(m.id));
      setMessages(r.messages);
    }).catch(() => {});

    const close = openStream(activeId, handleEvent);
    return () => close();
  }, [activeId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, draft, questions]);

  const refreshConvs = useCallback(() => {
    if (profileId) getConversations(profileId).then((r) => setConversations(r.conversations)).catch(() => {});
  }, [profileId]);

  function handleEvent(e: BridgeEvent) {
    switch (e.type) {
      case 'sync': setRunning(e.running); setQueued(e.queued); break;
      case 'user':
        if (seen.current.has(e.messageId)) break;
        seen.current.add(e.messageId);
        setMessages((m) => [...m, {
          id: e.messageId, conversationId: activeId, role: 'user',
          content: e.text + (e.attachments?.length ? `\n\n📎 ${e.attachments.length} file(s)` : ''),
          attachments: null, createdAt: Date.now(),
        }]);
        break;
      case 'start': setRunning(true); setDraft({ text: '', tools: [] }); setQuestions(null); break;
      case 'text': setDraft((d) => ({ text: e.text, tools: d?.tools ?? [] })); break;
      case 'tool': setDraft((d) => ({ text: d?.text ?? '', tools: [...(d?.tools ?? []), e.name] })); break;
      case 'questions': setQuestions({ items: e.questions }); break;
      case 'error':
        setMessages((m) => [...m, { id: `e-${Date.now()}`, conversationId: activeId, role: 'assistant', content: `⚠️ ${e.message}`, attachments: null, createdAt: Date.now() }]);
        break;
      case 'done':
        if (e.text) setMessages((m) => [...m, { id: `a-${Date.now()}-${Math.random()}`, conversationId: activeId, role: 'assistant', content: e.text, attachments: null, createdAt: Date.now() }]);
        setDraft(null); refreshConvs();
        break;
      case 'end': setQueued((q) => Math.max(0, q - 1)); break;
      case 'idle': setRunning(false); setQueued(0); setDraft(null); break;
    }
  }

  async function newConversation(projectId: string) {
    const r = await createConversation(projectId, profileId, model);
    setConversations((c) => [r.conversation, ...c]);
    setActiveId(r.conversation.id); setMessages([]);
  }

  async function onPickFiles(files: FileList | null) {
    if (!files || !activeId) return;
    for (const f of Array.from(files)) {
      try { const path = await uploadFile(activeId, f); setPending((p) => [...p, { name: f.name, path }]); } catch { /* */ }
    }
  }

  async function send(promptOverride?: string) {
    const prompt = (promptOverride ?? input).trim();
    if (!prompt || !activeId) return;
    const attachments = pending.map((p) => p.path);
    setInput(''); setPending([]);
    // Fire-and-forget — the user bubble + response arrive via the stream.
    await sendMessage({ conversationId: activeId, prompt, model, attachments }).catch(() => {});
  }

  function submitAnswers(answers: { question: string; answer: string }[]) {
    const reply = answers.map((a) => `${a.question}\n→ ${a.answer}`).join('\n\n');
    setQuestions(null);
    send(reply);
  }

  const activeConv = conversations.find((c) => c.id === activeId);

  return (
    <div className="chat-shell">
      <aside className="chat-sidebar">
        <div className="chat-profile">
          <User size={15} />
          <select value={profileId} onChange={(e) => setProfileId(e.target.value)}>
            {profiles.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <button title="Enable notifications" className="chat-bell" onClick={() => profileId && enablePush(profileId)}><Bell size={15} /></button>
        </div>
        <div className="chat-projects">
          {projects.map((proj) => (
            <div key={proj.id} className="chat-project">
              <div className="chat-project-head">
                <span><Hash size={13} /> {proj.name}{proj.scope === 'shared' && <em> · shared</em>}</span>
                <button title="New conversation" onClick={() => newConversation(proj.id)}><Plus size={14} /></button>
              </div>
              {conversations.filter((c) => c.projectId === proj.id).map((c) => (
                <button key={c.id} className={`chat-conv ${c.id === activeId ? 'chat-conv-on' : ''}`} onClick={() => setActiveId(c.id)}>{c.title}</button>
              ))}
            </div>
          ))}
        </div>
      </aside>

      <main className="chat-main">
        <div className="chat-thread" ref={scrollRef}>
          {!activeId && <div className="chat-empty">Pick a project and start a conversation.</div>}
          {messages.map((m) => (
            <div key={m.id} className={`chat-msg chat-msg-${m.role}`}>
              {m.role === 'assistant' ? <Markdown>{m.content}</Markdown> : <div className="chat-user-text">{m.content}</div>}
            </div>
          ))}
          {draft && (
            <div className="chat-msg chat-msg-assistant">
              {draft.tools.length > 0 && <div className="chat-tools">{draft.tools.map((t, i) => <span key={i}>{t}</span>)}</div>}
              {draft.text ? <Markdown>{draft.text}</Markdown> : <Loader className="chat-spin" size={16} />}
            </div>
          )}
          {questions && <QuestionPanel questions={questions.items} onSubmit={submitAnswers} />}
        </div>

        {activeId && (
          <div className="chat-composer">
            {(running || queued > 1) && (
              <div className="chat-status">
                <Loader className="chat-spin" size={12} /> {running ? 'Working…' : ''}{queued > 1 ? ` ${queued - 1} queued` : ''} — keep typing, messages queue
              </div>
            )}
            {pending.length > 0 && <div className="chat-attachments">{pending.map((p, i) => <span key={i}>📎 {p.name}</span>)}</div>}
            {!questions && (
              <>
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); send(); } }}
                  placeholder="Message… (⌘↵ to send). Send freely — messages queue while it works."
                  rows={3}
                />
                <div className="chat-composer-bar">
                  <div className="chat-composer-left">
                    <button onClick={() => fileRef.current?.click()} title="Attach image"><Paperclip size={16} /></button>
                    <input ref={fileRef} type="file" accept="image/*" multiple hidden onChange={(e) => onPickFiles(e.target.files)} />
                    <select value={model} onChange={(e) => setModel(e.target.value)}>{MODELS.map((m) => <option key={m} value={m}>{m}</option>)}</select>
                    {activeConv && <span className="chat-cwd">{activeConv.title}</span>}
                  </div>
                  <button className="chat-send" onClick={() => send()} disabled={!input.trim()}>
                    <Send size={16} />
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
