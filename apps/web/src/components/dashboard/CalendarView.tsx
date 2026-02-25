'use client';

import { useMemo, useState } from 'react';
import {
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  format,
  isSameMonth,
  isSameDay,
  isBefore,
  addMonths,
  subMonths,
  parseISO,
} from 'date-fns';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useIsMobile } from '@/hooks/useIsMobile';
import type { UnifiedTask, TaskDomain } from '@/server/dashboard/types';
import { DOMAIN_CONFIG } from '@/server/dashboard/types';
import { StatusDropdown } from './StatusDropdown';

interface CalendarViewProps {
  tasks: UnifiedTask[];
  onStatusChange: (taskId: string, rawStatus: string, domain: TaskDomain) => void;
}

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export function CalendarView({ tasks, onStatusChange }: CalendarViewProps) {
  const isMobile = useIsMobile();
  const [currentMonth, setCurrentMonth] = useState(new Date());

  if (isMobile) {
    return (
      <AgendaView
        tasks={tasks}
        onStatusChange={onStatusChange}
        currentMonth={currentMonth}
        onMonthChange={setCurrentMonth}
      />
    );
  }

  return (
    <MonthlyGrid
      tasks={tasks}
      currentMonth={currentMonth}
      onMonthChange={setCurrentMonth}
    />
  );
}

function MonthNav({
  currentMonth,
  onMonthChange,
}: {
  currentMonth: Date;
  onMonthChange: (d: Date) => void;
}) {
  return (
    <div className="flex items-center justify-between mb-4">
      <button
        onClick={() => onMonthChange(subMonths(currentMonth, 1))}
        className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors"
      >
        <ChevronLeft className="w-4 h-4" />
      </button>
      <h3 className="text-sm font-semibold text-gray-700">
        {format(currentMonth, 'MMMM yyyy')}
      </h3>
      <button
        onClick={() => onMonthChange(addMonths(currentMonth, 1))}
        className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors"
      >
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
}

function MonthlyGrid({
  tasks,
  currentMonth,
  onMonthChange,
}: Omit<CalendarViewProps, 'onStatusChange'> & { currentMonth: Date; onMonthChange: (d: Date) => void }) {
  const days = useMemo(() => {
    const start = startOfWeek(startOfMonth(currentMonth));
    const end = endOfWeek(endOfMonth(currentMonth));
    return eachDayOfInterval({ start, end });
  }, [currentMonth]);

  const tasksByDate = useMemo(() => {
    const map = new Map<string, UnifiedTask[]>();
    for (const task of tasks) {
      if (!task.dueDate) continue;
      const key = task.dueDate.split('T')[0]; // YYYY-MM-DD
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(task);
    }
    return map;
  }, [tasks]);

  const today = useMemo(() => new Date(), []);

  return (
    <div>
      <MonthNav currentMonth={currentMonth} onMonthChange={onMonthChange} />

      {/* Weekday headers */}
      <div className="grid grid-cols-7 gap-px mb-1">
        {WEEKDAYS.map(day => (
          <div key={day} className="text-center text-xs font-medium text-gray-500 py-1">
            {day}
          </div>
        ))}
      </div>

      {/* Day cells */}
      <div className="grid grid-cols-7 gap-px bg-gray-200 rounded-lg overflow-hidden">
        {days.map(day => {
          const key = format(day, 'yyyy-MM-dd');
          const dayTasks = tasksByDate.get(key) || [];
          const isCurrentMonth = isSameMonth(day, currentMonth);
          const isToday = isSameDay(day, today);

          return (
            <div
              key={key}
              className={`min-h-[80px] p-1 ${
                isCurrentMonth ? 'bg-white' : 'bg-gray-50'
              } ${isToday ? 'ring-2 ring-inset ring-blue-400' : ''}`}
            >
              <div
                className={`text-xs mb-1 ${
                  isToday
                    ? 'font-bold text-blue-600'
                    : isCurrentMonth
                      ? 'text-gray-700'
                      : 'text-gray-300'
                }`}
              >
                {format(day, 'd')}
              </div>
              <div className="space-y-0.5">
                {dayTasks.slice(0, 3).map(task => (
                  <a
                    key={task.id}
                    href={task.notionUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-[10px] leading-tight px-1 py-0.5 rounded truncate hover:opacity-80 transition-opacity"
                    style={{
                      backgroundColor: DOMAIN_CONFIG[task.domain].bgColor,
                      color: DOMAIN_CONFIG[task.domain].color,
                    }}
                    title={task.title}
                  >
                    {task.title}
                  </a>
                ))}
                {dayTasks.length > 3 && (
                  <span className="text-[10px] text-gray-400 px-1">
                    +{dayTasks.length - 3} more
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function AgendaView({
  tasks,
  onStatusChange,
  currentMonth,
  onMonthChange,
}: CalendarViewProps & { currentMonth: Date; onMonthChange: (d: Date) => void }) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const { overdueTasks, upcomingByDate } = useMemo(() => {
    const withDates = tasks.filter(t => t.dueDate);
    const overdue: UnifiedTask[] = [];
    const upcoming = new Map<string, UnifiedTask[]>();

    for (const task of withDates) {
      const date = parseISO(task.dueDate!);
      if (isBefore(date, today) && !isSameDay(date, today) && task.status !== 'done') {
        overdue.push(task);
      } else {
        const key = task.dueDate!.split('T')[0];
        if (!upcoming.has(key)) upcoming.set(key, []);
        upcoming.get(key)!.push(task);
      }
    }

    // Sort upcoming by date
    const sorted = new Map(
      [...upcoming.entries()].sort(([a], [b]) => a.localeCompare(b)),
    );

    return { overdueTasks: overdue, upcomingByDate: sorted };
  }, [tasks, today]);

  const noDatedTasks = tasks.filter(t => !t.dueDate);

  return (
    <div>
      <MonthNav currentMonth={currentMonth} onMonthChange={onMonthChange} />

      {/* Overdue */}
      {overdueTasks.length > 0 && (
        <div className="mb-4">
          <h4 className="text-xs font-semibold text-red-600 uppercase tracking-wider mb-2">
            Overdue ({overdueTasks.length})
          </h4>
          <div className="space-y-1.5">
            {overdueTasks.map(task => (
              <AgendaItem key={task.id} task={task} onStatusChange={onStatusChange} />
            ))}
          </div>
        </div>
      )}

      {/* Upcoming by date */}
      {[...upcomingByDate.entries()].map(([dateStr, dateTasks]) => {
        const date = parseISO(dateStr);
        const isDateToday = isSameDay(date, today);
        return (
          <div key={dateStr} className="mb-4">
            <h4
              className={`text-xs font-semibold uppercase tracking-wider mb-2 ${
                isDateToday ? 'text-blue-600' : 'text-gray-500'
              }`}
            >
              {isDateToday ? 'Today' : format(date, 'EEE, MMM d')}
            </h4>
            <div className="space-y-1.5">
              {dateTasks.map(task => (
                <AgendaItem key={task.id} task={task} onStatusChange={onStatusChange} />
              ))}
            </div>
          </div>
        );
      })}

      {/* No date */}
      {noDatedTasks.length > 0 && (
        <div className="mb-4">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            No due date ({noDatedTasks.length})
          </h4>
          <div className="space-y-1.5">
            {noDatedTasks.map(task => (
              <AgendaItem key={task.id} task={task} onStatusChange={onStatusChange} />
            ))}
          </div>
        </div>
      )}

      {tasks.length === 0 && (
        <p className="text-center text-gray-400 py-8 text-sm">No tasks found</p>
      )}
    </div>
  );
}

function AgendaItem({
  task,
  onStatusChange,
}: {
  task: UnifiedTask;
  onStatusChange: CalendarViewProps['onStatusChange'];
}) {
  const isCompleted = task.status === 'done' || task.status === 'cancelled';
  const config = DOMAIN_CONFIG[task.domain];

  return (
    <div
      className={`flex items-center gap-2 p-2 bg-white rounded-lg border border-gray-200 ${
        isCompleted ? 'opacity-60' : ''
      }`}
    >
      <span
        className="w-1 self-stretch rounded-full flex-shrink-0"
        style={{ backgroundColor: config.color }}
      />
      <div className="flex-1 min-w-0">
        <a
          href={task.notionUrl}
          target="_blank"
          rel="noopener noreferrer"
          className={`text-sm text-gray-900 hover:text-blue-600 hover:underline truncate block ${
            isCompleted ? 'line-through' : ''
          }`}
        >
          {task.title}
        </a>
      </div>
      <StatusDropdown
        domain={task.domain}
        currentRawStatus={task.rawStatus}
        onStatusChange={rawStatus => onStatusChange(task.id, rawStatus, task.domain)}
      />
    </div>
  );
}
