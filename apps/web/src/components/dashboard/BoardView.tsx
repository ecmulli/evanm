'use client';

import { useMemo, useState } from 'react';
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragStartEvent,
  type DragEndEvent,
} from '@dnd-kit/core';
import { useDroppable } from '@dnd-kit/core';
import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { useIsMobile } from '@/hooks/useIsMobile';
import type { UnifiedTask, TaskDomain, TaskStatus } from '@/server/dashboard/types';
import { BOARD_COLUMNS, STATUS_CONFIG, denormalizeStatus } from '@/server/dashboard/types';
import { TaskCard } from './TaskCard';

interface BoardViewProps {
  tasks: UnifiedTask[];
  onStatusChange: (taskId: string, rawStatus: string, domain: TaskDomain) => void;
}

function DroppableColumn({
  status,
  tasks,
  onStatusChange,
  isMobile,
}: {
  status: TaskStatus;
  tasks: UnifiedTask[];
  onStatusChange: BoardViewProps['onStatusChange'];
  isMobile: boolean;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: status });
  const config = STATUS_CONFIG[status];

  return (
    <div
      ref={setNodeRef}
      className={`flex flex-col min-h-[200px] ${isOver ? 'bg-[#EFF2E8]' : 'bg-[#F5F2EE]'} rounded-lg p-3 transition-colors border border-[#E8E4E0]`}
    >
      <div className="flex items-center gap-2 mb-3">
        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: config.color }} />
        <h3 className="text-xs font-semibold text-[#2A2520] uppercase tracking-wider">
          {config.label}
        </h3>
        <span className="text-xs text-[#BEA09A] ml-auto">{tasks.length}</span>
      </div>
      <div className="space-y-2 flex-1">
        {tasks.map(task =>
          isMobile ? (
            <TaskCard key={task.id} task={task} onStatusChange={onStatusChange} compact />
          ) : (
            <DraggableCard key={task.id} task={task} onStatusChange={onStatusChange} />
          ),
        )}
      </div>
    </div>
  );
}

function DraggableCard({
  task,
  onStatusChange,
}: {
  task: UnifiedTask;
  onStatusChange: BoardViewProps['onStatusChange'];
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: task.id,
    data: { task },
  });

  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} {...listeners} {...attributes}>
      <TaskCard task={task} onStatusChange={onStatusChange} compact />
    </div>
  );
}

export function BoardView({ tasks, onStatusChange }: BoardViewProps) {
  const isMobile = useIsMobile();
  const [activeTask, setActiveTask] = useState<UnifiedTask | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  );

  const columns = useMemo(() => {
    const grouped: Record<TaskStatus, UnifiedTask[]> = {
      todo: [],
      in_progress: [],
      blocked: [],
      done: [],
      skipped: [],
      cancelled: [],
    };
    for (const task of tasks) {
      if (grouped[task.status]) {
        grouped[task.status].push(task);
      }
    }
    return grouped;
  }, [tasks]);

  function handleDragStart(event: DragStartEvent) {
    const task = event.active.data.current?.task as UnifiedTask | undefined;
    setActiveTask(task ?? null);
  }

  function handleDragEnd(event: DragEndEvent) {
    setActiveTask(null);
    const { active, over } = event;
    if (!over) return;

    const targetStatus = over.id as TaskStatus;
    const task = active.data.current?.task as UnifiedTask | undefined;
    if (!task || task.status === targetStatus) return;

    // Map normalized status back to raw status for the task's domain
    const rawStatus = denormalizeStatus(task.domain, targetStatus);
    if (rawStatus) {
      onStatusChange(task.id, rawStatus, task.domain);
    }
  }

  if (isMobile) {
    return (
      <div className="space-y-4">
        {BOARD_COLUMNS.map(status => (
          <DroppableColumn
            key={status}
            status={status}
            tasks={columns[status]}
            onStatusChange={onStatusChange}
            isMobile
          />
        ))}
      </div>
    );
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {BOARD_COLUMNS.map(status => (
          <DroppableColumn
            key={status}
            status={status}
            tasks={columns[status]}
            onStatusChange={onStatusChange}
            isMobile={false}
          />
        ))}
      </div>
      <DragOverlay>
        {activeTask && (
          <div className="rotate-2 shadow-lg">
            <TaskCard task={activeTask} onStatusChange={onStatusChange} compact />
          </div>
        )}
      </DragOverlay>
    </DndContext>
  );
}
