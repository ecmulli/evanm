import type { TaskDomain, TaskPriority, TaskStatus, UnifiedTask } from './types';
import { PRIORITY_MAP, STATUS_MAP } from './types';
import { DB_CONFIG } from './notion-client';

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

function getStatusValue(props: NotionProperties, key: string): string {
  const prop = props[key];
  if (!prop) return '';
  if (prop.type === 'status') return prop.status?.name || '';
  if (prop.type === 'select') return prop.select?.name || '';
  return '';
}

function getSelect(props: NotionProperties, key: string): string | undefined {
  const prop = props[key];
  if (!prop || prop.type !== 'select') return undefined;
  return prop.select?.name || undefined;
}

function getMultiSelect(props: NotionProperties, key: string): string[] {
  const prop = props[key];
  if (!prop || prop.type !== 'multi_select') return [];
  return prop.multi_select?.map((s: { name: string }) => s.name) || [];
}

function getDate(props: NotionProperties, key: string): string | null {
  const prop = props[key];
  if (!prop || prop.type !== 'date' || !prop.date) return null;
  return prop.date.start || null;
}

function getNumber(props: NotionProperties, key: string): number | undefined {
  const prop = props[key];
  if (!prop || prop.type !== 'number') return undefined;
  return prop.number ?? undefined;
}

function getRichText(props: NotionProperties, key: string): string | undefined {
  const prop = props[key];
  if (!prop || prop.type !== 'rich_text') return undefined;
  const text = prop.rich_text?.map((t: { plain_text: string }) => t.plain_text).join('');
  return text || undefined;
}

// ===== Normalization =====

function normalizeStatus(domain: TaskDomain, rawStatus: string): TaskStatus {
  return STATUS_MAP[domain]?.[rawStatus] || 'todo';
}

function normalizePriority(domain: TaskDomain, rawPriority: string | undefined): TaskPriority | null {
  if (!rawPriority) return null;
  return PRIORITY_MAP[domain]?.[rawPriority] || null;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function normalizeTask(page: any, domain: TaskDomain): UnifiedTask {
  const props = page.properties;
  const config = DB_CONFIG[domain];

  const rawStatus = getStatusValue(props, config.statusProperty);
  const rawPriority = config.priorityProperty ? getSelect(props, config.priorityProperty) : undefined;

  const task: UnifiedTask = {
    id: page.id,
    title: getTitle(props, config.titleProperty),
    notionUrl: page.url || `https://notion.so/${page.id.replace(/-/g, '')}`,
    domain,
    status: normalizeStatus(domain, rawStatus),
    rawStatus,
    priority: normalizePriority(domain, rawPriority),
    dueDate: getDate(props, config.dueDateProperty),
    metadata: {},
    createdAt: page.created_time,
    updatedAt: page.last_edited_time,
  };

  // Domain-specific metadata
  if (domain === 'work') {
    task.metadata.labels = getMultiSelect(props, 'Labels');
    task.metadata.estimatedHours = getNumber(props, 'Est Duration Hrs');
  } else if (domain === 'career') {
    task.metadata.phase = getSelect(props, 'Phase');
    task.metadata.category = getSelect(props, 'Category');
    task.metadata.cadence = getSelect(props, 'Cadence');
    task.metadata.timeEstimate = getSelect(props, 'Time Estimate');
  } else if (domain === 'personal') {
    task.metadata.description = getRichText(props, 'Description');
    task.metadata.personalCategory = getSelect(props, 'Category');
  }

  return task;
}
