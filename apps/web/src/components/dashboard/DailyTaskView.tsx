'use client';

import { useState, useRef, useMemo, useCallback } from 'react';
import {
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  Check,
  Clock,
  Loader2,
  Trash2,
} from 'lucide-react';
import {
  format,
  addDays,
  subDays,
  isSameDay,
  isBefore,
  parseISO,
  isToday as isDateToday,
} from 'date-fns';
import { useTodos, type Todo } from '@/hooks/useTodos';
import type { TaskDomain, UnifiedTask } from '@/server/dashboard/types';
import { DOMAIN_CONFIG } from '@/server/dashboard/types';
import { CompleteCheckbox } from './CompleteCheckbox';
import { StatusDropdown } from './StatusDropdown';

const DOMAINS: TaskDomain[] = ['work', 'career', 'personal'];

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

// Unified item type for rendering
type DailyItem =
  | { kind: 'task'; data: UnifiedTask }
  | { kind: 'todo'; data: Todo };

function formatDateLabel(date: Date): string {
  const today = new Date();
  const tomorrow = addDays(today, 1);
  const yesterday = subDays(today, 1);

  if (isSameDay(date, today)) return 'Today';
  if (isSameDay(date, tomorrow)) return 'Tomorrow';
  if (isSameDay(date, yesterday)) return 'Yesterday';
  return format(date, 'EEE, MMM d');
}

function DailyTodoItem({
  todo,
  onToggle,
  onDelete,
}: {
  todo: Todo;
  onToggle: (id: string, done: boolean) => void;
  onDelete: (id: string) => void;
}) {
  const [deleting, setDeleting] = useState(false);
  const checkStyles = DOMAIN_CHECK_STYLES[todo.domain] ?? DOMAIN_CHECK_STYLES.personal;

  return (
    <div className="group flex items-center gap-3 py-2 px-1 rounded-lg transition-all duration-200 hover:bg-[#F0EEEB]">
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

      {todo.startTime && (
        <span className="flex items-center gap-1 text-[11px] text-[#8B8580] flex-shrink-0">
          <Clock className="w-3 h-3" />
          {todo.startTime}
        </span>
      )}

      <button
        onClick={async (e) => {
          e.stopPropagation();
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

function DailyTaskItem({
  task,
  onStatusChange,
}: {
  task: UnifiedTask;
  onStatusChange: (taskId: string, rawStatus: string) => void;
}) {
  const isCompleted = task.status === 'done' || task.status === 'cancelled';
  const config = DOMAIN_CONFIG[task.domain];

  return (
    <div
      className={`flex items-center gap-2 py-2 px-1 rounded-lg transition-all duration-200 hover:bg-[#F0EEEB] ${
        isCompleted ? 'opacity-50' : ''
      }`}
    >
      <CompleteCheckbox task={task} onStatusChange={onStatusChange} />
      <span
        className="w-1 self-stretch rounded-full flex-shrink-0"
        style={{ backgroundColor: config.color }}
      />
      <div className="flex-1 min-w-0">
        <a
          href={task.notionUrl}
          target="_blank"
          rel="noopener noreferrer"
          className={`text-[15px] leading-relaxed text-[#1A1714] hover:text-[#A0584A] hover:underline line-clamp-2 block ${
            isCompleted ? 'line-through' : ''
          }`}
        >
          {task.title}
        </a>
      </div>
      {task.startTime && (
        <span className="flex items-center gap-1 text-[11px] text-[#8B8580] flex-shrink-0">
          <Clock className="w-3 h-3" />
          {task.startTime}
        </span>
      )}
      <StatusDropdown
        currentRawStatus={task.rawStatus}
        onStatusChange={rawStatus => onStatusChange(task.id, rawStatus)}
      />
    </div>
  );
}

interface DailyTaskViewProps {
  tasks: UnifiedTask[];
  onStatusChange: (taskId: string, rawStatus: string) => void;
}

export function DailyTaskView({ tasks, onStatusChange }: DailyTaskViewProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [selectedDate, setSelectedDate] = useState(() => new Date());
  const touchStartX = useRef<number | null>(null);

  const { todos, toggleTodo, deleteTodo } = useTodos(true);

  const isToday = isDateToday(selectedDate);
  const selectedDateStr = format(selectedDate, 'yyyy-MM-dd');

  // Filter items for the selected date
  const dailyItems = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const items: DailyItem[] = [];

    for (const task of tasks) {
      if (!task.dueDate) continue;
      const taskDateStr = task.dueDate.split('T')[0];
      const taskDate = parseISO(taskDateStr);

      if (taskDateStr === selectedDateStr) {
        items.push({ kind: 'task', data: task });
      } else if (
        isToday &&
        isBefore(taskDate, today) &&
        task.status !== 'done' &&
        task.status !== 'cancelled'
      ) {
        // Include overdue tasks on today view
        items.push({ kind: 'task', data: task });
      }
    }

    for (const todo of todos) {
      if (!todo.dueDate) continue;
      const todoDateStr = todo.dueDate.split('T')[0];
      const todoDate = parseISO(todoDateStr);

      if (todoDateStr === selectedDateStr) {
        items.push({ kind: 'todo', data: todo });
      } else if (
        isToday &&
        isBefore(todoDate, today) &&
        !todo.done
      ) {
        items.push({ kind: 'todo', data: todo });
      }
    }

    return items;
  }, [tasks, todos, selectedDateStr, isToday]);

  // Group items by domain
  const groupedByDomain = useMemo(() => {
    const groups: Partial<Record<TaskDomain, DailyItem[]>> = {};
    for (const domain of DOMAINS) {
      const domainItems = dailyItems.filter(item => {
        const d = item.kind === 'task' ? item.data.domain : item.data.domain;
        return d === domain;
      });
      if (domainItems.length > 0) groups[domain] = domainItems;
    }
    return groups;
  }, [dailyItems]);

  const itemCount = dailyItems.length;

  const goToPrev = useCallback(() => setSelectedDate(d => subDays(d, 1)), []);
  const goToNext = useCallback(() => setSelectedDate(d => addDays(d, 1)), []);
  const goToToday = useCallback(() => setSelectedDate(new Date()), []);

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  }, []);

  const handleTouchEnd = useCallback(
    (e: React.TouchEvent) => {
      if (touchStartX.current === null) return;
      const delta = e.changedTouches[0].clientX - touchStartX.current;
      touchStartX.current = null;
      if (Math.abs(delta) > 50) {
        if (delta > 0) goToPrev();
        else goToNext();
      }
    },
    [goToPrev, goToNext],
  );

  const handleToggleTodo = useCallback(
    async (id: string, done: boolean) => {
      try {
        await toggleTodo(id, done);
      } catch (err) {
        console.error('Failed to toggle todo:', err);
      }
    },
    [toggleTodo],
  );

  const handleDeleteTodo = useCallback(
    async (id: string) => {
      try {
        await deleteTodo(id);
      } catch (err) {
        console.error('Failed to delete todo:', err);
      }
    },
    [deleteTodo],
  );

  const dateLabel = formatDateLabel(selectedDate);
  const fullDateLabel = isToday
    ? `Today \u2014 ${format(selectedDate, 'MMM d')}`
    : format(selectedDate, 'EEE, MMM d');

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
        <span className="text-sm font-semibold text-[#1A1714] tracking-tight">
          {fullDateLabel}
        </span>
        {itemCount > 0 && (
          <span className="text-xs bg-[#A05040] text-white px-1.5 py-0.5 rounded-full font-mono tabular-nums leading-none">
            {itemCount}
          </span>
        )}
      </button>

      {isExpanded && (
        <div className="border-t border-[#E5E0DB]">
          {/* Date navigation */}
          <div
            className="flex items-center justify-between px-4 py-2 border-b border-[#F0EEEB]"
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
          >
            <button
              onClick={goToPrev}
              className="p-1.5 text-[#B5AFA9] hover:text-[#1A1714] transition-colors rounded-lg hover:bg-[#F0EEEB]"
              aria-label="Previous day"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-[#1A1714]">
                {dateLabel}
              </span>
              {!isToday && (
                <button
                  onClick={goToToday}
                  className="text-[10px] font-semibold uppercase tracking-wide text-[#A05040] hover:text-[#7D3A2E] transition-colors px-1.5 py-0.5 rounded-md hover:bg-[#F5EDEB]"
                >
                  Today
                </button>
              )}
            </div>

            <button
              onClick={goToNext}
              className="p-1.5 text-[#B5AFA9] hover:text-[#1A1714] transition-colors rounded-lg hover:bg-[#F0EEEB]"
              aria-label="Next day"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Items */}
          <div
            className="px-4 pb-3"
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
          >
            {itemCount === 0 ? (
              <p className="text-sm text-[#B5AFA9] py-4 text-center">
                Nothing scheduled for {dateLabel.toLowerCase()}
              </p>
            ) : (
              <div>
                {DOMAINS.map(domain => {
                  const items = groupedByDomain[domain];
                  if (!items) return null;
                  const config = DOMAIN_CONFIG[domain];
                  return (
                    <div key={domain} className="mb-1">
                      <div
                        className="text-[10px] font-bold uppercase tracking-widest mb-0.5 px-1 pt-2"
                        style={{ color: config.color }}
                      >
                        {config.label}
                      </div>
                      {items.map(item =>
                        item.kind === 'todo' ? (
                          <DailyTodoItem
                            key={item.data.id}
                            todo={item.data}
                            onToggle={handleToggleTodo}
                            onDelete={handleDeleteTodo}
                          />
                        ) : (
                          <DailyTaskItem
                            key={item.data.id}
                            task={item.data}
                            onStatusChange={onStatusChange}
                          />
                        ),
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
