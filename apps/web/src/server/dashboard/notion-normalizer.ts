import type { TaskDomain, TaskPriority, TaskStatus, TaskType, UnifiedTask } from './types';
import { PRIORITY_MAP, STATUS_MAP } from './types';
import { PROPS } from './notion-client';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type NotionProperties = Record<string, any>;

// ===== Property Extraction Helpers =====

function getTitle(props: NotionProperties, key: string): string {
  const prop = props[key];
  if (!prop) return '';
  if (prop.type === 'title') {
    return prop.title?.map((t: { plain_text: string }) => t.plain_text).join('') || '';
  }
  return '';
}

function getSelect(props: NotionProperties, key: string): string | undefined {
  const prop = props[key];
  if (!prop || (prop.type !== 'select' && prop.type !== 'status')) return undefined;
  return prop.select?.name || prop.status?.name || undefined;
}

function getDate(props: NotionProperties, key: string): string | null {
  const prop = props[key];
  if (!prop || prop.type !== 'date' || !prop.date) return null;
  return prop.date.start || null;
}

function getDateFull(props: NotionProperties, key: string): { start: string | null; end: string | null } {
  const prop = props[key];
  if (!prop || prop.type !== 'date' || !prop.date) return { start: null, end: null };
  return { start: prop.date.start || null, end: prop.date.end || null };
}

function extractStartTime(dateStr: string | null): string | null {
  if (!dateStr || !dateStr.includes('T')) return null;
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return null;
  return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true, timeZone: 'America/Chicago' });
}

function calculateDurationFromRange(start: string | null, end: string | null): number | null {
  if (!start || !end || !start.includes('T') || !end.includes('T')) return null;
  const startDate = new Date(start);
  const endDate = new Date(end);
  if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) return null;
  const hours = (endDate.getTime() - startDate.getTime()) / 3_600_000;
  return hours > 0 ? Math.round(hours * 100) / 100 : null;
}

function parseTimeEstimateToHours(estimate: string | undefined): number | null {
  if (!estimate) return null;
  const map: Record<string, number> = {
    '10 min': 0.17,
    '30 min': 0.5,
    '60 min': 1,
    '90+ min': 1.5,
  };
  return map[estimate] ?? null;
}

// ===== Normalization =====

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function normalizeTask(page: any): UnifiedTask {
  const props = page.properties;

  const rawStatus = getSelect(props, PROPS.status) || '';
  const rawPriority = getSelect(props, PROPS.priority);
  const rawType = getSelect(props, PROPS.type) || 'Task';
  const rawDomain = getSelect(props, PROPS.domain)?.toLowerCase() || 'personal';

  const domain: TaskDomain =
    rawDomain === 'work' || rawDomain === 'career' || rawDomain === 'personal'
      ? rawDomain
      : 'personal';

  const type: TaskType = rawType === 'Quick To-Do' ? 'quick_todo' : 'task';

  // Extract full date range for start time and duration
  const dateFull = getDateFull(props, PROPS.dueDate);
  const startTime = extractStartTime(dateFull.start);
  const durationHours = calculateDurationFromRange(dateFull.start, dateFull.end);

  const category = getSelect(props, PROPS.category);
  const timeEstimate = getSelect(props, PROPS.timeEstimate);

  const task: UnifiedTask = {
    id: page.id,
    title: getTitle(props, PROPS.title),
    notionUrl: page.url || `https://notion.so/${page.id.replace(/-/g, '')}`,
    type,
    domain,
    status: STATUS_MAP[rawStatus] || 'todo',
    rawStatus,
    priority: rawPriority ? (PRIORITY_MAP[rawPriority] || null) : null,
    dueDate: getDate(props, PROPS.dueDate),
    startTime,
    durationHours: durationHours || parseTimeEstimateToHours(timeEstimate),
    metadata: {
      category,
      timeEstimate,
    },
    createdAt: page.created_time,
    updatedAt: page.last_edited_time,
  };

  return task;
}
