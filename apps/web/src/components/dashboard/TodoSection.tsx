'use client';

import { useState, useRef, useCallback } from 'react';
import { ChevronDown, ChevronRight, Plus, Trash2, Loader2, Check } from 'lucide-react';
import { useTodos, type Todo } from '@/hooks/useTodos';
import type { TaskDomain } from '@/server/dashboard/types';
import { DOMAIN_CONFIG } from '@/server/dashboard/types';

const DOMAINS: TaskDomain[] = ['work', 'career', 'personal'];

const DOMAIN_PILL_STYLES: Record<TaskDomain, { active: string; inactive: string }> = {
  work: {
    active: 'bg-[#1C2B4A] text-white',
    inactive: 'bg-[#EEF1F7] text-[#1C2B4A] hover:bg-[#DDE3EF]',
  },
  career: {
    active: 'bg-[#4A6B3A] text-white',
    inactive: 'bg-[#EFF4EC] text-[#4A6B3A] hover:bg-[#E0ECD9]',
  },
  personal: {
    active: 'bg-[#A05040] text-white',
    inactive: 'bg-[#F5EDEB] text-[#A05040] hover:bg-[#EEDEDA]',
  },
};

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

function DomainPill({
  domain,
  selected,
  onClick,
}: {
  domain: TaskDomain;
  selected: boolean;
  onClick: () => void;
}) {
  const config = DOMAIN_CONFIG[domain];
  const styles = DOMAIN_PILL_STYLES[domain];
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
        selected ? styles.active : styles.inactive
      }`}
    >
      {config.label}
    </button>
  );
}

function TodoItem({
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

export function TodoSection() {
  const [isExpanded, setIsExpanded] = useState(true);
  const [showCompleted, setShowCompleted] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [selectedDomain, setSelectedDomain] = useState<TaskDomain>('personal');
  const [isAdding, setIsAdding] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const { todos, isLoading, addTodo, toggleTodo, deleteTodo } =
    useTodos(showCompleted);

  const handleAdd = useCallback(async () => {
    const text = inputValue.trim();
    if (!text || isAdding) return;

    setIsAdding(true);
    try {
      await addTodo(text, selectedDomain);
      setInputValue('');
      inputRef.current?.focus();
    } catch (err) {
      console.error('Failed to add todo:', err);
    } finally {
      setIsAdding(false);
    }
  }, [inputValue, selectedDomain, isAdding, addTodo]);

  const handleToggle = useCallback(
    async (id: string, done: boolean) => {
      try {
        await toggleTodo(id, done);
      } catch (err) {
        console.error('Failed to toggle todo:', err);
      }
    },
    [toggleTodo],
  );

  const handleDelete = useCallback(
    async (id: string) => {
      try {
        await deleteTodo(id);
      } catch (err) {
        console.error('Failed to delete todo:', err);
      }
    },
    [deleteTodo],
  );

  const activeTodos = todos.filter((t) => !t.done);
  const doneTodos = todos.filter((t) => t.done);

  const groupedActive = DOMAINS.reduce(
    (acc, d) => {
      const items = activeTodos.filter((t) => t.domain === d);
      if (items.length > 0) acc[d] = items;
      return acc;
    },
    {} as Partial<Record<TaskDomain, Todo[]>>,
  );

  const activeCount = activeTodos.length;

  return (
    <section className="bg-white border border-[#E5E0DB] rounded-2xl overflow-hidden shadow-sm">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-2 px-4 py-3.5 hover:bg-[#F7F6F4] transition-colors"
        aria-expanded={isExpanded}
      >
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-[#B5AFA9]" />
        ) : (
          <ChevronRight className="w-4 h-4 text-[#B5AFA9]" />
        )}
        <span className="text-sm font-semibold text-[#1A1714] tracking-tight">Quick To-Dos</span>
        {activeCount > 0 && (
          <span className="text-xs bg-[#1C2B4A] text-white px-1.5 py-0.5 rounded-full font-mono tabular-nums leading-none">
            {activeCount}
          </span>
        )}
      </button>

      {isExpanded && (
        <div className="border-t border-[#E5E0DB]">
          {/* Domain selector + Add input — large, thumb-friendly on mobile */}
          <div className="px-4 pt-3 pb-2">
            {/* Domain pills */}
            <div className="flex items-center gap-1.5 mb-3">
              {DOMAINS.map((d) => (
                <DomainPill
                  key={d}
                  domain={d}
                  selected={selectedDomain === d}
                  onClick={() => setSelectedDomain(d)}
                />
              ))}
            </div>

            {/* Large capture input */}
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAdd();
                }}
                placeholder="Add a to-do..."
                className="flex-1 px-4 py-3 text-base bg-[#F7F6F4] border border-[#E5E0DB] rounded-xl text-[#1A1714] placeholder-[#B5AFA9] focus:outline-none focus:ring-2 focus:ring-[#1C2B4A]/20 focus:border-[#1C2B4A] transition-all"
                disabled={isAdding}
                aria-label="New to-do text"
              />
              <button
                onClick={handleAdd}
                disabled={!inputValue.trim() || isAdding}
                className="w-11 h-11 flex-shrink-0 flex items-center justify-center bg-[#1C2B4A] text-white rounded-xl disabled:opacity-30 transition-all active:scale-95"
                aria-label="Add to-do"
              >
                {isAdding ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Plus className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>

          {/* Todo list */}
          <div className="px-4 pb-1">
            {isLoading && todos.length === 0 ? (
              <div className="flex items-center gap-2 py-4 text-[#B5AFA9] text-sm">
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading...
              </div>
            ) : activeTodos.length === 0 && doneTodos.length === 0 ? (
              <p className="text-sm text-[#B5AFA9] py-3">
                Nothing here yet. Type above and press Enter.
              </p>
            ) : (
              <div>
                {DOMAINS.map((domain) => {
                  const items = groupedActive[domain];
                  if (!items) return null;
                  const config = DOMAIN_CONFIG[domain];
                  return (
                    <div key={domain} className="mb-1">
                      <div
                        className="text-[10px] font-bold uppercase tracking-widest mb-0.5 px-1 pt-1"
                        style={{ color: config.color }}
                      >
                        {config.label}
                      </div>
                      {items.map((todo) => (
                        <TodoItem
                          key={todo.id}
                          todo={todo}
                          onToggle={handleToggle}
                          onDelete={handleDelete}
                        />
                      ))}
                    </div>
                  );
                })}

                {showCompleted && doneTodos.length > 0 && (
                  <div className="pt-2 border-t border-[#E5E0DB] mt-2">
                    <div className="text-[10px] font-bold uppercase tracking-widest text-[#B5AFA9] mb-0.5 px-1 pt-1">
                      Done
                    </div>
                    {doneTodos.map((todo) => (
                      <TodoItem
                        key={todo.id}
                        todo={todo}
                        onToggle={handleToggle}
                        onDelete={handleDelete}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Show completed toggle */}
          <div className="flex items-center px-4 py-3 border-t border-[#E5E0DB]">
            <label className="flex items-center gap-2 text-xs text-[#6B6560] cursor-pointer select-none">
              <input
                type="checkbox"
                checked={showCompleted}
                onChange={(e) => setShowCompleted(e.target.checked)}
                className="rounded border-[#C8C2BC] text-[#4A6B3A] focus:ring-[#4A6B3A] w-3.5 h-3.5"
              />
              Show completed
            </label>
          </div>
        </div>
      )}
    </section>
  );
}
