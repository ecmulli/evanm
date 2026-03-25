import { getNotionClient, NOTION_DB_ID, PROPS } from './notion-client';
import type { Todo } from './todo-types';
import type { TaskDomain } from './types';

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function extractStartTime(dateStr: string | null): string | null {
  if (!dateStr || !dateStr.includes('T')) return null;
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return null;
  return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true, timeZone: 'America/Chicago' });
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function normalizeTodo(page: any): Todo {
  const props = page.properties;

  // Extract title
  const titleProp = props[PROPS.title];
  const name =
    titleProp?.title?.[0]?.plain_text || titleProp?.title?.[0]?.text?.content || '';

  // Status-based done check
  const status = props[PROPS.status]?.select?.name || 'To Do';
  const done = status === 'Done';

  // Domain
  const domainRaw = props[PROPS.domain]?.select?.name?.toLowerCase() || 'personal';
  const domain: TaskDomain =
    domainRaw === 'work' || domainRaw === 'career' || domainRaw === 'personal'
      ? domainRaw
      : 'personal';

  // Due date
  const dueDateProp = props[PROPS.dueDate];
  const dueDate = dueDateProp?.date?.start || null;
  const startTime = extractStartTime(dueDate);

  return {
    id: page.id,
    name,
    done,
    domain,
    dueDate,
    startTime,
    createdAt: page.created_time,
  };
}

export async function fetchTodos(includeCompleted = false): Promise<Todo[]> {
  const notion = getNotionClient();

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const conditions: any[] = [
    { property: PROPS.type, select: { equals: 'Quick To-Do' } },
  ];

  if (!includeCompleted) {
    conditions.push(
      { property: PROPS.status, select: { does_not_equal: 'Done' } },
      { property: PROPS.status, select: { does_not_equal: 'Cancelled' } },
    );
  }

  const filter = conditions.length === 1 ? conditions[0] : { and: conditions };

  const todos: Todo[] = [];
  let hasMore = true;
  let startCursor: string | undefined;

  while (hasMore) {
    const response = await notion.databases.query({
      database_id: NOTION_DB_ID,
      filter,
      sorts: [{ timestamp: 'created_time', direction: 'descending' }],
      start_cursor: startCursor,
      page_size: 100,
    });

    for (const page of response.results) {
      if ('properties' in page) {
        todos.push(normalizeTodo(page));
      }
    }

    hasMore = response.has_more;
    startCursor = response.next_cursor ?? undefined;
  }

  return todos;
}

export async function createTodoInNotion(
  name: string,
  domain: TaskDomain,
): Promise<Todo> {
  const notion = getNotionClient();

  const response = await notion.pages.create({
    parent: { database_id: NOTION_DB_ID },
    properties: {
      [PROPS.title]: { title: [{ text: { content: name } }] },
      [PROPS.type]: { select: { name: 'Quick To-Do' } },
      [PROPS.domain]: { select: { name: capitalize(domain) } },
      [PROPS.status]: { select: { name: 'To Do' } },
    },
  });

  return normalizeTodo(response);
}

export async function toggleTodoInNotion(
  pageId: string,
  done: boolean,
): Promise<void> {
  const notion = getNotionClient();

  await notion.pages.update({
    page_id: pageId,
    properties: {
      [PROPS.status]: { select: { name: done ? 'Done' : 'To Do' } },
    },
  });
}

export async function deleteTodoInNotion(pageId: string): Promise<void> {
  const notion = getNotionClient();

  await notion.pages.update({
    page_id: pageId,
    archived: true,
  });
}
