'use client';

import { useState, useCallback } from 'react';
import { ChevronDown, ChevronRight, Loader2, Calendar } from 'lucide-react';
import { useTodos, type Todo } from '@/hooks/useTodos';
import type { TaskDomain } from '@/server/dashboard/types';
import { DOMAIN_CONFIG } from '@/server/dashboard/types';
import { TodoItem } from './TodoItem';

const DOMAINS: TaskDomain[] = ['work', 'career', 'personal'];

function getTodayCentral(): string {
  return new Date().toLocaleDateString('en-CA', { timeZone: 'America/Chicago' });
}

function formatTodayHeader(): string {
  return new Date().toLocaleDateString('en-US', {
    timeZone: 'America/Chicago',
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
}

export function TodaySection() {
  const [isExpanded, setIsExpanded] = useState(true);
  const [showCompleted, setShowCompleted] = useState(false);

  const { todos, isLoading, toggleTodo, deleteTodo } = useTodos(showCompleted);

  const todayStr = getTodayCentral();
  const todayTodos = todos.filter((t) => t.date === todayStr);
  const activeTodos = todayTodos.filter((t) => !t.done);
  const doneTodos = todayTodos.filter((t) => t.done);

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
        <Calendar className="w-4 h-4 text-[#A05040]" />
        <span className="text-sm font-semibold text-[#1A1714] tracking-tight">Today</span>
        <span className="text-xs text-[#B5AFA9] font-medium">{formatTodayHeader()}</span>
        {activeCount > 0 && (
          <span className="text-xs bg-[#A05040] text-white px-1.5 py-0.5 rounded-full font-mono tabular-nums leading-none ml-auto">
            {activeCount}
          </span>
        )}
      </button>

      {isExpanded && (
        <div className="border-t border-[#E5E0DB]">
          <div className="px-4 pb-1">
            {isLoading && todayTodos.length === 0 ? (
              <div className="flex items-center gap-2 py-4 text-[#B5AFA9] text-sm">
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading...
              </div>
            ) : activeTodos.length === 0 && doneTodos.length === 0 ? (
              <p className="text-sm text-[#B5AFA9] py-3">
                Nothing scheduled for today.
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
          {(activeTodos.length > 0 || doneTodos.length > 0) && (
            <div className="flex items-center px-4 py-3 border-t border-[#E5E0DB]">
              <label className="flex items-center gap-2 text-xs text-[#6B6560] cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={showCompleted}
                  onChange={(e) => setShowCompleted(e.target.checked)}
                  className="rounded border-[#C8C2BC] text-[#A05040] focus:ring-[#A05040] w-3.5 h-3.5"
                />
                Show completed
              </label>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
