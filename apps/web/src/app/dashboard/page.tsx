'use client';

import { useState, useCallback } from 'react';
import { useTasks } from '@/hooks/useTasks';
import { FilterBar, type ViewMode } from '@/components/dashboard/FilterBar';
import { ListView } from '@/components/dashboard/ListView';
import { BoardView } from '@/components/dashboard/BoardView';
import { CalendarView } from '@/components/dashboard/CalendarView';
import type { TaskDomain } from '@/server/dashboard/types';

export default function DashboardPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [domainFilter, setDomainFilter] = useState<TaskDomain | null>(null);
  const [showCompleted, setShowCompleted] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const { tasks, count, isLoading, error, updateTaskStatus, refreshTasks } = useTasks({
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
    async (taskId: string, rawStatus: string, domain: TaskDomain) => {
      try {
        await updateTaskStatus(taskId, rawStatus, domain);
      } catch (err) {
        console.error('Failed to update task status:', err);
      }
    },
    [updateTaskStatus],
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Task Dashboard</h1>
        </div>

        {/* Filters */}
        <FilterBar
          viewMode={viewMode}
          onViewChange={setViewMode}
          domainFilter={domainFilter}
          onDomainChange={setDomainFilter}
          showCompleted={showCompleted}
          onShowCompletedChange={setShowCompleted}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
          taskCount={count}
        />

        {/* Content */}
        <div className="mt-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-4">
              <p className="text-sm font-medium">Failed to load tasks</p>
              <p className="text-xs mt-1">{error.message}</p>
              <button
                onClick={handleRefresh}
                className="mt-2 text-xs text-red-600 hover:text-red-800 underline"
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
                <ListView tasks={tasks} onStatusChange={handleStatusChange} />
              )}
              {viewMode === 'board' && (
                <BoardView tasks={tasks} onStatusChange={handleStatusChange} />
              )}
              {viewMode === 'calendar' && (
                <CalendarView tasks={tasks} onStatusChange={handleStatusChange} />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function LoadingSkeleton({ viewMode }: { viewMode: ViewMode }) {
  if (viewMode === 'board') {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="space-y-3">
            <div className="h-6 bg-gray-200 rounded w-24 animate-pulse" />
            {Array.from({ length: 3 }).map((_, j) => (
              <div key={j} className="bg-white rounded-lg border border-gray-200 p-3 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4 animate-pulse" />
                <div className="h-3 bg-gray-100 rounded w-1/2 animate-pulse" />
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="bg-white rounded-lg border border-gray-200 p-3 flex items-center gap-3">
          <div className="w-2 h-2 bg-gray-200 rounded-full animate-pulse" />
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              <div className="h-4 bg-gray-200 rounded w-14 animate-pulse" />
              <div className="h-4 bg-gray-200 rounded w-20 animate-pulse" />
            </div>
            <div className="h-4 bg-gray-100 rounded w-2/3 animate-pulse" />
          </div>
          <div className="h-3 bg-gray-100 rounded w-16 animate-pulse" />
        </div>
      ))}
    </div>
  );
}
