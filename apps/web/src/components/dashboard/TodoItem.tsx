'use client';

import { useState } from 'react';
import { Trash2, Loader2, Check } from 'lucide-react';
import type { Todo } from '@/hooks/useTodos';
import type { TaskDomain } from '@/server/dashboard/types';

const DOMAIN_CHECK_STYLES: Record<TaskDomain, { checked: string; unchecked: string }> = {
  work: {
    checked: 'bg-[#1C2B4A] border-[#1C2B4A]',
    unchecked: 'border-[#C8C2BC] hover:border-[#1C2B4A]',
  },
  career: {
    checked: 'bg-[#4A6B3A] border-[#4A6B3A]',
    unchecked: 'border-[#C8C2BC] hover:border-[#4A6B3A]',
  },
  personal: {
    checked: 'bg-[#A05040] border-[#A05040]',
    unchecked: 'border-[#C8C2BC] hover:border-[#A05040]',
  },
};

export function TodoItem({
  todo,
  onToggle,
  onDelete,
}: {
  todo: Todo;
  onToggle: (id: string, done: boolean) => void;
  onDelete: (id: string) => void;
}) {
  const [deleting, setDeleting] = useState(false);
  const checkStyles = DOMAIN_CHECK_STYLES[todo.domain as TaskDomain] ?? DOMAIN_CHECK_STYLES.personal;

  return (
    <div
      className={`group flex items-center gap-3 py-2 px-1 rounded-lg transition-all duration-200 ${
        todo.done ? 'opacity-40' : 'hover:bg-[#F0EEEB]'
      }`}
    >
      <button
        onClick={() => onToggle(todo.id, !todo.done)}
        className={`flex-shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all duration-200 ${
          todo.done ? checkStyles.checked : checkStyles.unchecked
        }`}
      >
        {todo.done && <Check className="w-2.5 h-2.5 text-white" strokeWidth={3} />}
      </button>

      <span
        className={`flex-1 text-[15px] leading-relaxed text-[#1A1714] ${
          todo.done ? 'line-through text-[#B5AFA9]' : ''
        }`}
      >
        {todo.name}
      </span>

      <button
        onClick={async () => {
          setDeleting(true);
          try {
            await onDelete(todo.id);
          } finally {
            setDeleting(false);
          }
        }}
        className="opacity-0 group-hover:opacity-100 text-[#B5AFA9] hover:text-[#B34438] transition-all p-1 rounded-md hover:bg-[#FDF2F1]"
        title="Delete"
        aria-label="Delete to-do"
      >
        {deleting ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <Trash2 className="w-3.5 h-3.5" />
        )}
      </button>
    </div>
  );
}
