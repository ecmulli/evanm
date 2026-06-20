'use client';

import { useState } from 'react';
import type { Question } from '@/lib/chat/api';

// Batched question form: renders ALL questions, collects every answer, and only
// submits once. Fixes Discord's flow where answering one question started processing.
export function QuestionPanel({
  questions, onSubmit,
}: {
  questions: Question[];
  onSubmit: (answers: { question: string; answer: string }[]) => void;
}) {
  const [answers, setAnswers] = useState<Record<number, string[]>>({});
  const [custom, setCustom] = useState<Record<number, string>>({});

  const toggle = (qi: number, label: string, multi: boolean) => {
    setAnswers((prev) => {
      const cur = prev[qi] ?? [];
      if (multi) {
        return { ...prev, [qi]: cur.includes(label) ? cur.filter((l) => l !== label) : [...cur, label] };
      }
      return { ...prev, [qi]: [label] };
    });
  };

  const allAnswered = questions.every((_, qi) => (answers[qi]?.length ?? 0) > 0 || custom[qi]?.trim());

  const submit = () => {
    const payload = questions.map((q, qi) => {
      const picked = answers[qi] ?? [];
      const extra = custom[qi]?.trim();
      const all = extra ? [...picked, extra] : picked;
      return { question: q.question, answer: all.join(', ') };
    });
    onSubmit(payload);
  };

  return (
    <div className="chat-questions">
      <div className="chat-questions-title">A few questions before I continue</div>
      {questions.map((q, qi) => (
        <div key={qi} className="chat-question">
          <div className="chat-question-label">
            <span className="chat-question-chip">{q.header}</span>
            {q.question}
          </div>
          <div className="chat-question-options">
            {q.options.map((opt) => {
              const selected = (answers[qi] ?? []).includes(opt.label);
              return (
                <button
                  key={opt.label}
                  type="button"
                  onClick={() => toggle(qi, opt.label, q.multiSelect)}
                  className={`chat-option ${selected ? 'chat-option-on' : ''}`}
                >
                  <span className="chat-option-label">{opt.label}</span>
                  <span className="chat-option-desc">{opt.description}</span>
                </button>
              );
            })}
          </div>
          <input
            className="chat-question-custom"
            placeholder="Or type your own…"
            value={custom[qi] ?? ''}
            onChange={(e) => setCustom((c) => ({ ...c, [qi]: e.target.value }))}
          />
        </div>
      ))}
      <button type="button" className="chat-submit-answers" disabled={!allAnswered} onClick={submit}>
        Submit answers
      </button>
    </div>
  );
}
