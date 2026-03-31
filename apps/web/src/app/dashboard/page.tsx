'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import Link from 'next/link';
import { LogIn } from 'lucide-react';
import { useTasks } from '@/hooks/useTasks';
import { useDemoTasks } from '@/hooks/useDemoTasks';
import { useDemoTodos } from '@/hooks/useDemoTodos';
import { useAuth } from '@/hooks/useAuth';
import { FilterBar, type ViewMode } from '@/components/dashboard/FilterBar';
import { ListView } from '@/components/dashboard/ListView';
import { BoardView } from '@/components/dashboard/BoardView';
import { CalendarView } from '@/components/dashboard/CalendarView';
import { TodoSection } from '@/components/dashboard/TodoSection';
import { DailyTaskView } from '@/components/dashboard/DailyTaskView';
import { FloatingAddBar } from '@/components/dashboard/FloatingAddBar';
import type { TaskDomain, UnifiedTask } from '@/server/dashboard/types';
import type { Todo } from '@/hooks/useTodos';

// A selected item can be either a task or a todo
type SelectedItem =
  | { kind: 'task'; task: UnifiedTask }
  | { kind: 'todo'; todo: Todo };

export default function DashboardPage() {
  const { isAuthenticated } = useAuth();

  // Render entirely separate component trees so the real SWR hooks
  // are never mounted (and never fetch) when in demo mode.
  return isAuthenticated ? <AuthenticatedDashboard /> : <DemoDashboard />;
}

// ─── Authenticated Dashboard (real Notion data) ────────────────────────

function AuthenticatedDashboard() {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [domainFilter, setDomainFilter] = useState<TaskDomain | null>(null);
  const [showCompleted, setShowCompleted] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedItem, setSelectedItem] = useState<SelectedItem | null>(null);
  const addTodoRef = useRef<(text: string, domain: TaskDomain) => Promise<void>>(() => Promise.resolve());
  const smartAddRef = useRef<(text: string, domain: TaskDomain) => Promise<unknown>>(() => Promise.resolve());
  const editTodoRef = useRef<(instruction: string, todo: Todo) => Promise<unknown>>(() => Promise.resolve());

  const { tasks, count, isLoading, error, updateTaskStatus, editTask, refreshTasks } = useTasks({
    domain: domainFilter ?? undefined,
    includeCompleted: showCompleted,
  });

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await refreshTasks();
    } finally {
      setIsRefreshing(false);
    }
  }, [refreshTasks]);

  const handleStatusChange = useCallback(
    async (taskId: string, rawStatus: string) => {
      try {
        await updateTaskStatus(taskId, rawStatus);
      } catch (err) {
        console.error('Failed to update task status:', err);
      }
    },
    [updateTaskStatus],
  );

  const handleSelectTask = useCallback((task: UnifiedTask) => {
    setSelectedItem(prev =>
      prev?.kind === 'task' && prev.task.id === task.id ? null : { kind: 'task', task },
    );
  }, []);

  const handleSelectTodo = useCallback((todo: Todo) => {
    setSelectedItem(prev =>
      prev?.kind === 'todo' && prev.todo.id === todo.id ? null : { kind: 'todo', todo },
    );
  }, []);

  const handleDeselect = useCallback(() => {
    setSelectedItem(null);
  }, []);

  const handleEditTask = useCallback(
    async (instruction: string, task: UnifiedTask) => {
      return editTask(instruction, task);
    },
    [editTask],
  );

  const handleEditTodo = useCallback(
    async (instruction: string, todo: Todo) => {
      return editTodoRef.current(instruction, todo);
    },
    [],
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && selectedItem) {
        setSelectedItem(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedItem]);

  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch((err) => {
        console.error('SW registration failed:', err);
      });
    }
  }, []);

  const selectedTask = selectedItem?.kind === 'task' ? selectedItem.task : null;
  const selectedTodo = selectedItem?.kind === 'todo' ? selectedItem.todo : null;

  return (
    <DashboardShell
      isDemo={false}
      viewMode={viewMode}
      onViewChange={setViewMode}
      domainFilter={domainFilter}
      onDomainChange={setDomainFilter}
      showCompleted={showCompleted}
      onShowCompletedChange={setShowCompleted}
      isRefreshing={isRefreshing}
      onRefresh={handleRefresh}
      tasks={tasks}
      count={count}
      isLoading={isLoading}
      error={error}
      onStatusChange={handleStatusChange}
      selectedTask={selectedTask}
      selectedTodo={selectedTodo}
      onSelectTask={handleSelectTask}
      onSelectTodo={handleSelectTodo}
      onDeselect={handleDeselect}
      onAdd={(text, domain) => addTodoRef.current(text, domain)}
      onSmartAdd={(text, domain) => smartAddRef.current(text, domain)}
      onEditTask={handleEditTask}
      onEditTodo={handleEditTodo}
      todoSectionProps={{
        onAddRef: (fn) => { addTodoRef.current = fn; },
        onSmartAddRef: (fn) => { smartAddRef.current = fn; },
        onEditRef: (fn) => { editTodoRef.current = fn; },
        selectedTodoId: selectedTodo?.id ?? null,
        onSelectTodo: handleSelectTodo,
      }}
    />
  );
}

// ─── Demo Dashboard (in-memory data, no API calls) ─────────────────────

function DemoDashboard() {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [domainFilter, setDomainFilter] = useState<TaskDomain | null>(null);
  const [showCompleted, setShowCompleted] = useState(false);
  const [selectedItem, setSelectedItem] = useState<SelectedItem | null>(null);
  const addTodoRef = useRef<(text: string, domain: TaskDomain) => Promise<void>>(() => Promise.resolve());

  const { tasks, count, isLoading, error, updateTaskStatus } = useDemoTasks({
    domain: domainFilter ?? undefined,
    includeCompleted: showCompleted,
  });
  const demoTodosHook = useDemoTodos(showCompleted);

  const handleStatusChange = useCallback(
    async (taskId: string, rawStatus: string) => {
      try {
        await updateTaskStatus(taskId, rawStatus);
      } catch (err) {
        console.error('Failed to update task status:', err);
      }
    },
    [updateTaskStatus],
  );

  const handleSelectTask = useCallback((task: UnifiedTask) => {
    setSelectedItem(prev =>
      prev?.kind === 'task' && prev.task.id === task.id ? null : { kind: 'task', task },
    );
  }, []);

  const handleSelectTodo = useCallback((todo: Todo) => {
    setSelectedItem(prev =>
      prev?.kind === 'todo' && prev.todo.id === todo.id ? null : { kind: 'todo', todo },
    );
  }, []);

  const handleDeselect = useCallback(() => {
    setSelectedItem(null);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && selectedItem) {
        setSelectedItem(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedItem]);

  const selectedTask = selectedItem?.kind === 'task' ? selectedItem.task : null;
  const selectedTodo = selectedItem?.kind === 'todo' ? selectedItem.todo : null;

  return (
    <DashboardShell
      isDemo={true}
      viewMode={viewMode}
      onViewChange={setViewMode}
      domainFilter={domainFilter}
      onDomainChange={setDomainFilter}
      showCompleted={showCompleted}
      onShowCompletedChange={setShowCompleted}
      isRefreshing={false}
      onRefresh={async () => {}}
      tasks={tasks}
      count={count}
      isLoading={isLoading}
      error={error}
      onStatusChange={handleStatusChange}
      selectedTask={selectedTask}
      selectedTodo={selectedTodo}
      onSelectTask={handleSelectTask}
      onSelectTodo={handleSelectTodo}
      onDeselect={handleDeselect}
      onAdd={(text, domain) => addTodoRef.current(text, domain)}
      todoSectionProps={{
        onAddRef: (fn) => { addTodoRef.current = fn; },
        selectedTodoId: selectedTodo?.id ?? null,
        onSelectTodo: handleSelectTodo,
        injectedTodos: demoTodosHook,
      }}
    />
  );
}

// ─── Shared Dashboard UI Shell ──────────────────────────────────────────

interface DashboardShellProps {
  isDemo: boolean;
  viewMode: ViewMode;
  onViewChange: (mode: ViewMode) => void;
  domainFilter: TaskDomain | null;
  onDomainChange: (domain: TaskDomain | null) => void;
  showCompleted: boolean;
  onShowCompletedChange: (show: boolean) => void;
  isRefreshing: boolean;
  onRefresh: () => Promise<void>;
  tasks: UnifiedTask[];
  count: number;
  isLoading: boolean;
  error: Error | null;
  onStatusChange: (taskId: string, rawStatus: string) => Promise<void>;
  selectedTask: UnifiedTask | null;
  selectedTodo: Todo | null;
  onSelectTask: (task: UnifiedTask) => void;
  onSelectTodo: (todo: Todo) => void;
  onDeselect: () => void;
  onAdd: (text: string, domain: TaskDomain) => Promise<void>;
  onSmartAdd?: (text: string, domain: TaskDomain) => Promise<unknown>;
  onEditTask?: (instruction: string, task: UnifiedTask) => Promise<{ success: boolean; updates: { summary: string } }>;
  onEditTodo?: (instruction: string, todo: Todo) => Promise<unknown>;
  todoSectionProps: React.ComponentProps<typeof TodoSection>;
}

function DashboardShell({
  isDemo,
  viewMode,
  onViewChange,
  domainFilter,
  onDomainChange,
  showCompleted,
  onShowCompletedChange,
  isRefreshing,
  onRefresh,
  tasks,
  count,
  isLoading,
  error,
  onStatusChange,
  selectedTask,
  selectedTodo,
  onSelectTask,
  onSelectTodo,
  onDeselect,
  onAdd,
  onSmartAdd,
  onEditTask,
  onEditTodo,
  todoSectionProps,
}: DashboardShellProps) {
  return (
    <div className="min-h-screen bg-[#F7F6F4] font-sans pb-32">
      {/* Header bar */}
      <header className="bg-[#1C2B4A] sticky top-0 z-40">
        {isDemo && (
          <div className="bg-[#A05040]/90 text-white text-center text-xs py-1.5 font-medium tracking-wide">
            Demo Mode — data is temporary and stored in your browser
          </div>
        )}
        <div className="max-w-2xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-[#A05040] flex items-center justify-center flex-shrink-0">
              <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <h1 className="text-sm font-semibold text-white tracking-tight">My Work</h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-white/40 font-mono tabular-nums">
              {count} task{count !== 1 ? 's' : ''}
            </span>
            {isDemo && (
              <Link
                href="/login?redirect=/dashboard"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs font-medium transition-colors"
              >
                <LogIn className="w-3.5 h-3.5" />
                Log In
              </Link>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-4 sm:py-6 space-y-4">
        {/* Daily Task View */}
        <DailyTaskView
          tasks={tasks}
          onStatusChange={handleStatusChange}
          selectedTaskId={selectedTask?.id ?? null}
          selectedTodoId={selectedTodo?.id ?? null}
          onSelectTask={handleSelectTask}
          onSelectTodo={handleSelectTodo}
        />

        {/* Quick To-Dos */}
        <TodoSection {...todoSectionProps} />

        {/* Filters */}
        <FilterBar
          viewMode={viewMode}
          onViewChange={onViewChange}
          domainFilter={domainFilter}
          onDomainChange={onDomainChange}
          showCompleted={showCompleted}
          onShowCompletedChange={onShowCompletedChange}
          onRefresh={onRefresh}
          isRefreshing={isRefreshing}
          taskCount={count}
        />

        {/* Content */}
        <div>
          {error && (
            <div className="bg-[#FDF2F1] border border-[#B34438]/20 text-[#B34438] rounded-xl p-4 mb-4">
              <p className="text-sm font-medium">Failed to load tasks</p>
              <p className="text-xs mt-1 opacity-70">{error.message}</p>
              <button
                onClick={onRefresh}
                className="mt-2 text-xs text-[#B34438] hover:opacity-70 underline"
              >
                Try again
              </button>
            </div>
          )}

          {isLoading && !tasks.length ? (
            <LoadingSkeleton viewMode={viewMode} />
          ) : (
            <>
              {viewMode === 'list' && (
                <ListView
                  tasks={tasks}
                  onStatusChange={onStatusChange}
                  selectedTaskId={selectedTask?.id ?? null}
                  onSelectTask={onSelectTask}
                />
              )}
              {viewMode === 'board' && (
                <BoardView tasks={tasks} onStatusChange={onStatusChange} />
              )}
              {viewMode === 'calendar' && (
                <CalendarView tasks={tasks} onStatusChange={onStatusChange} />
              )}
            </>
          )}
        </div>
      </div>

      {/* Floating liquid-glass add bar */}
      <FloatingAddBar
        onAdd={onAdd}
        onSmartAdd={onSmartAdd}
        selectedTask={selectedTask}
        selectedTodo={selectedTodo}
        onEditTask={onEditTask}
        onEditTodo={onEditTodo}
        onDeselect={onDeselect}
      />
    </div>
  );
}

function LoadingSkeleton({ viewMode }: { viewMode: ViewMode }) {
  if (viewMode === 'board') {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="space-y-2">
            <div className="h-5 bg-[#E5E0DB] rounded-full w-20 animate-pulse" />
            {Array.from({ length: 3 }).map((_, j) => (
              <div key={j} className="bg-white rounded-xl border border-[#E5E0DB] p-3 space-y-2">
                <div className="h-4 bg-[#E5E0DB] rounded-full w-3/4 animate-pulse" />
                <div className="h-3 bg-[#F0EEEB] rounded-full w-1/2 animate-pulse" />
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="bg-white rounded-xl border border-[#E5E0DB] p-3.5 flex items-center gap-3">
          <div className="w-4 h-4 bg-[#E5E0DB] rounded-full animate-pulse flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              <div className="h-4 bg-[#E5E0DB] rounded-full w-12 animate-pulse" />
              <div className="h-4 bg-[#E5E0DB] rounded-full w-16 animate-pulse" />
            </div>
            <div className="h-4 bg-[#F0EEEB] rounded-full w-2/3 animate-pulse" />
          </div>
          <div className="h-3 bg-[#F0EEEB] rounded-full w-14 animate-pulse" />
        </div>
      ))}
    </div>
  );
}
