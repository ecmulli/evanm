import { getNotionClient } from './notion-client';
import type { Todo } from './todo-types';
import type { TaskDomain } from './types';

const TODOS_DB_ID =
  process.env.NOTION_TODOS_DB || '3296a969f3204d79bd19e02c1645689c';

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function normalizeTodo(page: any): Todo {
  const props = page.properties;

  // Extract title
  const titleProp = props['Name'];
  const name =
    titleProp?.title?.[0]?.plain_text || titleProp?.title?.[0]?.text?.content || '';

  // Extract checkbox
  const done = props['Done']?.checkbox ?? false;

  // Extract domain select
  const domainRaw = props['Domain']?.select?.name?.toLowerCase() || 'personal';
  const domain: TaskDomain =
    domainRaw === 'work' || domainRaw === 'career' || domainRaw === 'personal'
      ? domainRaw
      : 'personal';

  return {
    id: page.id,
    name,
    done,
    domain,
    createdAt: page.created_time,
  };
}

export async function fetchTodos(includeCompleted = false): Promise<Todo[]> {
  const notion = getNotionClient();

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const filter: any = includeCompleted
    ? undefined
    : { property: 'Done', checkbox: { equals: false } };

  const todos: Todo[] = [];
  let hasMore = true;
  let startCursor: string | undefined;

  while (hasMore) {
    const response = await notion.databases.query({
      database_id: TODOS_DB_ID,
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
    parent: { database_id: TODOS_DB_ID },
    properties: {
      Name: { title: [{ text: { content: name } }] },
      Domain: { select: { name: capitalize(domain) } },
      Done: { checkbox: false },
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
      Done: { checkbox: done },
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
