import type { TaskDomain } from './types';
import { getNotionClient, DB_CONFIG, NOTION_USER_ID } from './notion-client';
import { normalizeTask } from './notion-normalizer';
import type { UnifiedTask } from './types';

interface QueryOptions {
  includeCompleted?: boolean;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function buildFilter(domain: TaskDomain, options: QueryOptions): any {
  const config = DB_CONFIG[domain];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const conditions: any[] = [];

  // Filter to tasks assigned to the user (Work has Assignee property)
  if (config.assigneeProperty && NOTION_USER_ID) {
    conditions.push({
      property: config.assigneeProperty,
      people: { contains: NOTION_USER_ID },
    });
  }

  if (!options.includeCompleted) {
    if (domain === 'work') {
      conditions.push(
        { property: config.statusProperty, status: { does_not_equal: 'Backlog' } },
        { property: config.statusProperty, status: { does_not_equal: 'Completed' } },
        { property: config.statusProperty, status: { does_not_equal: 'Cancelled' } },
      );
    } else if (domain === 'career') {
      conditions.push(
        { property: config.statusProperty, select: { does_not_equal: 'Done' } },
        { property: config.statusProperty, select: { does_not_equal: 'Completed' } },
        { property: config.statusProperty, select: { does_not_equal: 'Skipped' } },
      );
    } else {
      conditions.push(
        { property: config.statusProperty, select: { does_not_equal: 'Done' } },
      );
    }
  }

  if (conditions.length === 0) return undefined;
  if (conditions.length === 1) return conditions[0];
  return { and: conditions };
}

export async function queryDomain(domain: TaskDomain, options: QueryOptions = {}): Promise<UnifiedTask[]> {
  const notion = getNotionClient();
  const config = DB_CONFIG[domain];
  const filter = buildFilter(domain, options);

  const tasks: UnifiedTask[] = [];
  let hasMore = true;
  let startCursor: string | undefined;

  while (hasMore) {
    const response = await notion.databases.query({
      database_id: config.databaseId,
      filter,
      sorts: [{ property: config.dueDateProperty, direction: 'ascending' }],
      start_cursor: startCursor,
      page_size: 100,
    });

    for (const page of response.results) {
      if ('properties' in page) {
        tasks.push(normalizeTask(page, domain));
      }
    }

    hasMore = response.has_more;
    startCursor = response.next_cursor ?? undefined;
  }

  return tasks;
}

export interface FetchResult {
  tasks: UnifiedTask[];
  errors: Record<string, string>;
}

export async function fetchAllTasks(options: QueryOptions = {}): Promise<FetchResult> {
  // Fetch all three domains in parallel
  const [workTasks, careerTasks, personalTasks] = await Promise.allSettled([
    queryDomain('work', options),
    queryDomain('career', options),
    queryDomain('personal', options),
  ]);

  const tasks: UnifiedTask[] = [];
  const errors: Record<string, string> = {};

  if (workTasks.status === 'fulfilled') tasks.push(...workTasks.value);
  else { console.error('Failed to fetch work tasks:', workTasks.reason); errors.work = String(workTasks.reason); }

  if (careerTasks.status === 'fulfilled') tasks.push(...careerTasks.value);
  else { console.error('Failed to fetch career tasks:', careerTasks.reason); errors.career = String(careerTasks.reason); }

  if (personalTasks.status === 'fulfilled') tasks.push(...personalTasks.value);
  else { console.error('Failed to fetch personal tasks:', personalTasks.reason); errors.personal = String(personalTasks.reason); }

  return { tasks, errors };
}

export async function updateTaskInNotion(
  taskId: string,
  domain: TaskDomain,
  rawStatus: string,
): Promise<void> {
  const notion = getNotionClient();
  const config = DB_CONFIG[domain];

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const properties: Record<string, any> = {};

  if (config.statusPropertyType === 'status') {
    properties[config.statusProperty] = { status: { name: rawStatus } };
  } else {
    properties[config.statusProperty] = { select: { name: rawStatus } };
  }

  await notion.pages.update({
    page_id: taskId,
    properties,
  });
}
