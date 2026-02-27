'use client';

import { useState, useRef, useCallback } from 'react';
import {
  ChevronDown,
  ChevronRight,
  Plus,
  Trash2,
  Loader2,
} from 'lucide-react';
import { useTodos, type Todo } from '@/hooks/useTodos';
import type { TaskDomain } from '@/server/dashboard/types';
import { DOMAIN_CONFIG } from '@/server/dashboard/types';

const DOMAINS: TaskDomain[] = ['work', 'career', 'personal'];

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
  return (
    <button
      onClick={onClick}
      className="px-2 py-0.5 rounded text-xs font-medium transition-all"
      style={{
        backgroundColor: selected ? config.color : config.bgColor,
        color: selected ? '#fff' : config.color,
      }}
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

  return (
    <div
      className={`group flex items-center gap-2 py-1.5 px-1 rounded transition-all duration-300 ${
        todo.done ? 'opacity-40' : ''
      }`}
    >
      <button
        onClick={() => onToggle(todo.id, !todo.done)}
        className={`flex-shrink-0 w-4.5 h-4.5 rounded border-2 flex items-center justify-center transition-all duration-200 ${
          todo.done
            ? 'bg-[#5B6B3B] border-[#5B6B3B]'
            : 'border-[#D4CFC9] hover:border-[#5B6B3B]'
        }`}
      >
        {todo.done && (
          <svg
            className="w-3 h-3 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            strokeWidth={3}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M5 13l4 4L19 7"
            />
          </svg>
        )}
      </button>

      <span
        className={`flex-1 text-sm text-[#2A2520] ${
          todo.done ? 'line-through' : ''
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
        className="opacity-0 group-hover:opacity-100 text-[#BEA09A] hover:text-[#A0584A] transition-opacity p-0.5"
        title="Delete"
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

  // Group todos by domain, only show groups that have items
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
    <section className="mb-4 bg-[#FDFCFA] border border-[#E8E4E0] rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-2 px-3 sm:px-4 py-2.5 hover:bg-[#F5F2EE] transition-colors"
      >
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-[#6B6560]" />
        ) : (
          <ChevronRight className="w-4 h-4 text-[#6B6560]" />
        )}
        <span className="text-sm font-semibold text-[#2A2520]">
          Quick To-Dos
        </span>
        {activeCount > 0 && (
          <span className="text-xs bg-[#152A54] text-white px-1.5 py-0.5 rounded-full font-mono">
            {activeCount}
          </span>
        )}
      </button>

      {isExpanded && (
        <div className="px-3 sm:px-4 pb-3">
          {/* Add input row */}
          <div className="flex items-center gap-2 mb-3">
            <div className="flex items-center gap-1">
              {DOMAINS.map((d) => (
                <DomainPill
                  key={d}
                  domain={d}
                  selected={selectedDomain === d}
                  onClick={() => setSelectedDomain(d)}
                />
              ))}
            </div>
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAdd();
                }}
                placeholder="Add a to-do..."
                className="w-full pl-3 pr-8 py-1.5 text-sm bg-white border border-[#E8E4E0] rounded-md text-[#2A2520] placeholder-[#BEA09A] focus:outline-none focus:ring-1 focus:ring-[#152A54] focus:border-[#152A54]"
                disabled={isAdding}
              />
              <button
                onClick={handleAdd}
                disabled={!inputValue.trim() || isAdding}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 text-[#BEA09A] hover:text-[#152A54] disabled:opacity-30 transition-colors"
              >
                {isAdding ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* Todo list */}
          {isLoading && todos.length === 0 ? (
            <div className="flex items-center gap-2 py-3 text-[#BEA09A] text-xs">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Loading to-dos...
            </div>
          ) : activeTodos.length === 0 && doneTodos.length === 0 ? (
            <p className="text-xs text-[#BEA09A] py-2">
              No to-dos yet. Type above and press Enter.
            </p>
          ) : (
            <div className="space-y-2">
              {/* Active todos grouped by domain */}
              {DOMAINS.map((domain) => {
                const items = groupedActive[domain];
                if (!items) return null;
                const config = DOMAIN_CONFIG[domain];
                return (
                  <div key={domain}>
                    <div
                      className="text-[10px] font-semibold uppercase tracking-wider mb-0.5 px-1"
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

              {/* Done todos */}
              {showCompleted && doneTodos.length > 0 && (
                <div className="pt-1 border-t border-[#E8E4E0]">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-[#BEA09A] mb-0.5 px-1">
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

          {/* Show completed toggle */}
          <div className="flex items-center gap-2 mt-2 pt-2 border-t border-[#E8E4E0]">
            <label className="flex items-center gap-1.5 text-xs text-[#6B6560] cursor-pointer">
              <input
                type="checkbox"
                checked={showCompleted}
                onChange={(e) => setShowCompleted(e.target.checked)}
                className="rounded border-[#D4CFC9] text-[#5B6B3B] focus:ring-[#5B6B3B]"
              />
              <span className="hidden sm:inline">Show completed</span>
              <span className="sm:hidden">Done</span>
            </label>
          </div>
        </div>
      )}
    </section>
  );
}
