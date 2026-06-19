'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Plus, Send, Paperclip, Loader, User, Bell, Search, ChevronDown, Menu } from 'lucide-react';
import {
  getProjects, getConversations, getMessages, searchConversations,
  createConversation, sendMessage, openStream, uploadFile,
  type Profile, type Project, type Conversation, type Message, type Question, type BridgeEvent,
} from '@/lib/chat/api';
import { Markdown } from '@/components/chat/Markdown';
import { QuestionPanel } from '@/components/chat/QuestionPanel';
import { enablePush } from '@/lib/chat/push-client';

const MODELS = ['sonnet', 'opus', 'haiku'];

export default function ChatPage() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [profileId, setProfileId] = useState('');
  const [projects, setProjects] = useState<Project[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState('');
  const [draftProjectId, setDraftProjectId] = useState<string | null>(null); // new chat, not yet created
  const [messages, setMessages] = useState<Message[]>([]);
  const [tools, setTools] = useState<string[]>([]);
  const [questions, setQuestions] = useState<{ items: Question[] } | null>(null);
  const [input, setInput] = useState('');
  const [model, setModel] = useState('sonnet');
  const [pending, setPending] = useState<{ name: string; path: string }[]>([]);
  const [running, setRunning] = useState(false);
  const [queued, setQueued] = useState(0);
  const [ready, setReady] = useState(false);
  const [newOpen, setNewOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [results, setResults] = useState<Conversation[] | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false); // mobile: collapsed when a chat is active
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const activeIdRef = useRef('');

  // Auth gate via the cookie-aware bridge proxy (NOT /api/v1/auth/validate, which
  // is header-only and caused a login loop).
  useEffect(() => {
    fetch('/api/bridge/profiles')
      .then(async (r) => {
        if (r.status === 401) { window.location.href = '/login?redirect=/chat'; return; }
        const d = await r.json().catch(() => ({ profiles: [] }));
        setProfiles(d.profiles ?? []);
        if (d.profiles?.[0]) setProfileId(d.profiles[0].id);
        setReady(true);
      })
      .catch(() => setReady(true));
  }, []);

  useEffect(() => {
    if (!profileId) return;
    setActiveId(''); setMessages([]); setSearch(''); setResults(null);
    getConversations(profileId).then((r) => setConversations(r.conversations)).catch(() => {});
    getProjects(profileId).then((r) => {
      setProjects(r.projects);
      // Default to a new active chat (General) so the composer is ready immediately.
      const gen = r.projects.find((p) => /general/i.test(p.name)) ?? r.projects[0];
      setDraftProjectId(gen ? gen.id : null);
    }).catch(() => {});
  }, [profileId]);

  useEffect(() => {
    activeIdRef.current = activeId;
    if (!activeId) { setMessages([]); setTools([]); setQuestions(null); return; }
    setTools([]); setQuestions(null); setRunning(false); setQueued(0);
    getMessages(activeId).then((r) => setMessages(r.messages)).catch(() => {});
    const close = openStream(activeId, handleEvent);
    return () => close();
  }, [activeId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Debounced search (title + message content) via the bridge.
  useEffect(() => {
    if (!profileId) return;
    const q = search.trim();
    if (!q) { setResults(null); return; }
    const t = setTimeout(() => {
      searchConversations(profileId, q).then((r) => setResults(r.conversations)).catch(() => setResults([]));
    }, 220);
    return () => clearTimeout(t);
  }, [search, profileId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, tools, questions]);

  const refreshConvs = useCallback(() => {
    if (profileId) getConversations(profileId).then((r) => setConversations(r.conversations)).catch(() => {});
  }, [profileId]);

  function upsert(id: string, patch: Partial<Message> & { role: Message['role']; content: string }) {
    setMessages((m) => {
      const i = m.findIndex((x) => x.id === id);
      if (i >= 0) {
        if (m[i].content === patch.content) return m;
        const next = m.slice(); next[i] = { ...next[i], ...patch }; return next;
      }
      return [...m, { id, conversationId: activeIdRef.current, attachments: null, createdAt: Date.now(), ...patch }];
    });
  }

  function handleEvent(e: BridgeEvent) {
    switch (e.type) {
      case 'sync': setRunning(e.running); setQueued(e.queued); break;
      case 'user': upsert(e.messageId, { role: 'user', content: e.text + (e.attachments?.length ? `\n\n📎 ${e.attachments.length} file(s)` : '') }); break;
      case 'start': setRunning(true); setTools([]); setQuestions(null); break;
      case 'text': upsert(`seg-${e.messageId}`, { role: 'assistant', content: e.text }); break;
      case 'tool': setTools((t) => (t[t.length - 1] === e.name ? t : [...t, e.name])); break;
      case 'questions': setQuestions({ items: e.questions }); break;
      case 'error': upsert(`err-${Date.now()}`, { role: 'assistant', content: `⚠️ ${e.message}` }); break;
      case 'done': break;
      case 'end': setQueued((q) => Math.max(0, q - 1)); setTools([]); refreshConvs(); break;
      case 'idle': setRunning(false); setQueued(0); setTools([]); break;
    }
  }

  function startDraft(projectId: string) {
    setNewOpen(false);
    setActiveId('');
    setDraftProjectId(projectId);
    setMessages([]); setTools([]); setQuestions(null);
    setSidebarOpen(false); // mobile: jump into the chat
  }

  function openConversation(id: string) {
    setDraftProjectId(null);
    setActiveId(id);
    setSidebarOpen(false); // mobile: collapse the list, show the chat
  }

  async function onPickFiles(files: FileList | null) {
    if (!files) return;
    const convId = activeId || 'draft';
    for (const f of Array.from(files)) {
      try { const path = await uploadFile(convId, f); setPending((p) => [...p, { name: f.name, path }]); } catch { /* */ }
    }
  }

  async function send(promptOverride?: string) {
    const prompt = (promptOverride ?? input).trim();
    if (!prompt) return;
    let convId = activeId;
    // Draft → create the conversation only now, on first send.
    if (!convId && draftProjectId) {
      const r = await createConversation(draftProjectId, profileId, model);
      convId = r.conversation.id;
      setConversations((c) => [r.conversation, ...c]);
      setDraftProjectId(null);
      setActiveId(convId);
    }
    if (!convId) return;
    const attachments = pending.map((p) => p.path);
    setInput(''); setPending([]);
    await sendMessage({ conversationId: convId, prompt, model, attachments }).catch(() => {});
  }

  function submitAnswers(answers: { question: string; answer: string }[]) {
    const reply = answers.map((a) => `${a.question}\n→ ${a.answer}`).join('\n\n');
    setQuestions(null);
    send(reply);
  }

  const projectName = (id: string) => projects.find((p) => p.id === id)?.name ?? '';
  const activeConv = conversations.find((c) => c.id === activeId);
  const list = results ?? conversations;
  const composing = !!activeId || !!draftProjectId;
  const lastIsUser = messages.length > 0 && messages[messages.length - 1].role === 'user';
  const showSpinner = running && lastIsUser && tools.length === 0;

  if (!ready) {
    return (
      <div className="chat-shell" style={{ gridTemplateColumns: '1fr' }}>
        <div className="chat-empty" style={{ margin: 'auto' }}><Loader className="chat-spin" size={20} /> Checking access…</div>
      </div>
    );
  }

  return (
    <div className="chat-shell" data-sidebar={sidebarOpen ? 'open' : 'closed'}>
      <aside className="chat-sidebar">
        <div className="chat-profile">
          <User size={15} />
          <select value={profileId} onChange={(e) => setProfileId(e.target.value)}>
            {profiles.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <button title="Enable notifications" className="chat-bell" onClick={() => profileId && enablePush(profileId)}><Bell size={15} /></button>
        </div>

        {/* New chat with project picker */}
        <div className="chat-new">
          <button className="chat-newchat" onClick={() => setNewOpen((o) => !o)} disabled={!projects.length}>
            <Plus size={16} /> New chat <ChevronDown size={14} />
          </button>
          {newOpen && (
            <div className="chat-new-menu">
              {projects.map((p) => (
                <button key={p.id} onClick={() => startDraft(p.id)}>
                  {p.name}{p.scope === 'shared' && <em> · shared</em>}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Search */}
        <div className="chat-search">
          <Search size={14} />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search chats…" />
        </div>

        {/* Flat conversation list with topic badge */}
        <div className="chat-convs">
          {list.length === 0 && <div className="chat-convs-empty">{search ? 'No matches' : 'No conversations yet'}</div>}
          {list.map((c) => (
            <button key={c.id} className={`chat-conv ${c.id === activeId ? 'chat-conv-on' : ''}`} onClick={() => openConversation(c.id)}>
              <span className="chat-conv-title">{c.title}</span>
              <span className="chat-conv-badge">{projectName(c.projectId)}</span>
            </button>
          ))}
        </div>
      </aside>

      <main className="chat-main">
        <div className="chat-mobilebar">
          <button onClick={() => setSidebarOpen(true)} aria-label="Conversations"><Menu size={18} /></button>
          <span className="chat-mobilebar-title">{activeConv?.title ?? (draftProjectId ? `New chat · ${projectName(draftProjectId)}` : 'Chat')}</span>
        </div>
        <div className="chat-thread" ref={scrollRef}>
          {!composing && <div className="chat-empty">Start a new chat or pick a conversation.</div>}
          {composing && messages.length === 0 && (
            <div className="chat-empty chat-draft-hint">New chat{draftProjectId ? ` in ${projectName(draftProjectId)}` : ''} — type a message to begin.</div>
          )}
          {messages.map((m) => (
            <div key={m.id} className={`chat-msg chat-msg-${m.role}`}>
              {m.role === 'assistant' ? <Markdown>{m.content}</Markdown> : <div className="chat-user-text">{m.content}</div>}
            </div>
          ))}
          {tools.length > 0 && <div className="chat-msg chat-msg-assistant"><div className="chat-tools">{tools.map((t, i) => <span key={i}>{t}</span>)}</div></div>}
          {showSpinner && <div className="chat-msg chat-msg-assistant"><Loader className="chat-spin" size={16} /></div>}
          {questions && <QuestionPanel questions={questions.items} onSubmit={submitAnswers} />}
        </div>

        {composing && (
          <div className="chat-composer">
            {(running || queued > 1) && (
              <div className="chat-status"><Loader className="chat-spin" size={12} /> {running ? 'Working…' : ''}{queued > 1 ? ` ${queued - 1} queued` : ''} — keep typing, messages queue</div>
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
                  </div>
                  <button className="chat-send" onClick={() => send()} disabled={!input.trim()}><Send size={16} /></button>
                </div>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
