import type { TaskDomain, TaskType } from './types';
import { getNotionClient, NOTION_DB_ID, PROPS } from './notion-client';
import { normalizeTask } from './notion-normalizer';
import type { UnifiedTask } from './types';

interface QueryOptions {
  includeCompleted?: boolean;
  domain?: TaskDomain;
  type?: TaskType;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function buildFilter(options: QueryOptions): any {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const conditions: any[] = [];

  // Filter by Type (Task vs Quick To-Do)
  if (options.type === 'task') {
    conditions.push({ property: PROPS.type, select: { equals: 'Task' } });
  } else if (options.type === 'quick_todo') {
    conditions.push({ property: PROPS.type, select: { equals: 'Quick To-Do' } });
  }

  // Filter by Domain
  if (options.domain) {
    const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
    conditions.push({ property: PROPS.domain, select: { equals: capitalize(options.domain) } });
  }

  // Exclude completed/cancelled unless requested
  if (!options.includeCompleted) {
    conditions.push(
      { property: PROPS.status, select: { does_not_equal: 'Done' } },
      { property: PROPS.status, select: { does_not_equal: 'Cancelled' } },
      { property: PROPS.status, select: { does_not_equal: 'Skipped' } },
    );
  }

  if (conditions.length === 0) return undefined;
  if (conditions.length === 1) return conditions[0];
  return { and: conditions };
}

export async function fetchAllTasks(options: QueryOptions = {}): Promise<{ tasks: UnifiedTask[]; errors: Record<string, string> }> {
  const notion = getNotionClient();
  const filter = buildFilter({ ...options, type: options.type ?? 'task' });

  const tasks: UnifiedTask[] = [];
  let hasMore = true;
  let startCursor: string | undefined;

  try {
    while (hasMore) {
      const response = await notion.databases.query({
        database_id: NOTION_DB_ID,
        filter,
        sorts: [{ property: PROPS.dueDate, direction: 'ascending' }],
        start_cursor: startCursor,
        page_size: 100,
      });

      for (const page of response.results) {
        if ('properties' in page) {
          tasks.push(normalizeTask(page));
        }
      }

      hasMore = response.has_more;
      startCursor = response.next_cursor ?? undefined;
    }
  } catch (err) {
    console.error('Failed to fetch tasks:', err);
    return { tasks, errors: { query: String(err) } };
  }

  return { tasks, errors: {} };
}

export async function updateTaskInNotion(
  taskId: string,
  rawStatus: string,
): Promise<void> {
  const notion = getNotionClient();

  await notion.pages.update({
    page_id: taskId,
    properties: {
      [PROPS.status]: { select: { name: rawStatus } },
    },
  });
}
