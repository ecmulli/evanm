import Anthropic from '@anthropic-ai/sdk';
import { getNotionClient, DB_CONFIG, NOTION_USER_ID } from './notion-client';
import { buildTaskIntakePrompt } from './task-intake-prompt';
import type { TaskDomain } from './types';

// Lazy-init Anthropic client
let _anthropic: Anthropic | null = null;

export function getAnthropicClient(): Anthropic {
  if (!_anthropic) {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      throw new Error('ANTHROPIC_API_KEY environment variable is required');
    }
    _anthropic = new Anthropic({ apiKey });
  }
  return _anthropic;
}

const DEFAULT_MODEL = 'claude-haiku-4-5-20251001';

// --- Types ---

type DatabaseTarget = 'work' | 'career' | 'personal' | 'quick_todo';

export interface ParsedTask {
  database: DatabaseTarget;
  title: string;
  properties: Record<string, string | number | string[] | null>;
  pageBody: string | null;
  confidence: 'high' | 'medium' | 'low';
}

export interface CreateTaskResult {
  id: string;
  url: string;
  domain: TaskDomain;
  title: string;
  database: DatabaseTarget;
  properties: Record<string, string | number | string[] | null>;
}

// --- AI Parsing ---

export async function parseTaskWithAI(
  text: string,
  domain: TaskDomain,
): Promise<ParsedTask> {
  const anthropic = getAnthropicClient();
  const model = process.env.ANTHROPIC_MODEL || DEFAULT_MODEL;
  const currentDate = new Date().toISOString().split('T')[0];

  const userMessage = `Domain: ${domain}\n\nTask: ${text}`;

  const response = await anthropic.messages.create({
    model,
    max_tokens: 2048,
    system: buildTaskIntakePrompt(currentDate),
    messages: [{ role: 'user', content: userMessage }],
  });

  const content = response.content[0];
  if (content.type !== 'text') {
    throw new Error('Unexpected response type from AI');
  }

  // Extract JSON object from response — the model may include code fences or trailing text
  const rawText = content.text.trim();
  const jsonStart = rawText.indexOf('{');
  const jsonEnd = rawText.lastIndexOf('}');
  if (jsonStart === -1 || jsonEnd === -1) {
    throw new Error('No JSON object found in AI response');
  }
  const jsonText = rawText.slice(jsonStart, jsonEnd + 1);

  const parsed: ParsedTask = JSON.parse(jsonText);

  // Domain selector is authoritative — override whatever the AI chose
  parsed.database = domain;

  return parsed;
}

// --- Notion Creation ---

const TODOS_DB_ID =
  process.env.NOTION_TODOS_DB || '3296a969f3204d79bd19e02c1645689c';

export async function createTaskInNotion(
  parsed: ParsedTask,
): Promise<CreateTaskResult> {
  if (parsed.database === 'quick_todo') {
    return createQuickTodo(parsed);
  }
  return createFullTask(parsed);
}

async function createQuickTodo(parsed: ParsedTask): Promise<CreateTaskResult> {
  const notion = getNotionClient();

  // Determine domain from properties or default to personal
  const domainRaw = (parsed.properties?.Domain as string) || 'Personal';
  const domainLower = domainRaw.toLowerCase() as TaskDomain;
  const domain: TaskDomain =
    domainLower === 'work' || domainLower === 'career' || domainLower === 'personal'
      ? domainLower
      : 'personal';

  const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

  const response = await notion.pages.create({
    parent: { database_id: TODOS_DB_ID },
    properties: {
      Name: { title: [{ text: { content: parsed.title } }] },
      Domain: { select: { name: capitalize(domain) } },
      Done: { checkbox: false },
    },
  });

  return {
    id: response.id,
    url: (response as { url?: string }).url || `https://notion.so/${response.id.replace(/-/g, '')}`,
    domain,
    title: parsed.title,
    database: 'quick_todo',
    properties: parsed.properties,
  };
}

async function createFullTask(parsed: ParsedTask): Promise<CreateTaskResult> {
  const notion = getNotionClient();
  const domain = parsed.database as TaskDomain;
  const config = DB_CONFIG[domain];

  // Build properties object
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const properties: Record<string, any> = {};

  // Title
  properties[config.titleProperty] = {
    title: [{ text: { content: parsed.title } }],
  };

  // Status — always set to "todo" equivalent
  if (config.statusPropertyType === 'status') {
    properties[config.statusProperty] = { status: { name: 'Todo' } };
  } else {
    properties[config.statusProperty] = { select: { name: 'To Do' } };
  }

  // Assignee for work tasks
  if (domain === 'work' && config.assigneeProperty) {
    properties[config.assigneeProperty] = {
      people: [{ id: NOTION_USER_ID }],
    };
  }

  // Map AI-inferred properties to Notion format
  for (const [key, value] of Object.entries(parsed.properties)) {
    if (value === null || value === undefined) continue;

    // Skip properties we already handle above or that aren't real Notion properties
    if (
      key === 'Domain' || key === 'Done' ||
      key === config.statusProperty ||
      key === config.titleProperty
    ) continue;

    // Determine the Notion property type from the key and domain
    const propType = getPropertyType(domain, key);

    switch (propType) {
      case 'status':
        properties[key] = { status: { name: String(value) } };
        break;
      case 'select':
        properties[key] = { select: { name: String(value) } };
        break;
      case 'multi_select':
        if (Array.isArray(value)) {
          properties[key] = {
            multi_select: value.map((v) => ({ name: String(v) })),
          };
        }
        break;
      case 'date':
        properties[key] = { date: { start: String(value) } };
        break;
      case 'number':
        properties[key] = { number: Number(value) };
        break;
      case 'rich_text':
        properties[key] = {
          rich_text: [{ text: { content: String(value) } }],
        };
        break;
      default:
        // Unknown property type, try as rich_text
        properties[key] = {
          rich_text: [{ text: { content: String(value) } }],
        };
    }
  }

  // Default due date: 1 week from now if not set by AI or user
  const dueDateKey = config.dueDateProperty;
  if (!properties[dueDateKey]) {
    const oneWeekFromNow = new Date();
    oneWeekFromNow.setDate(oneWeekFromNow.getDate() + 7);
    properties[dueDateKey] = { date: { start: oneWeekFromNow.toISOString().split('T')[0] } };
  }

  // Create the page
  const response = await notion.pages.create({
    parent: { database_id: config.databaseId },
    properties,
  });

  const pageId = response.id;
  const url =
    (response as { url?: string }).url ||
    `https://notion.so/${pageId.replace(/-/g, '')}`;

  // Append page body content if provided
  if (parsed.pageBody) {
    try {
      const blocks = parsePageBodyToBlocks(parsed.pageBody);
      if (blocks.length > 0) {
        await notion.blocks.children.append({
          block_id: pageId,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          children: blocks as any,
        });
      }
    } catch (err) {
      // Page body is nice-to-have; don't fail the whole creation
      console.error('Failed to append page body:', err);
    }
  }

  return {
    id: pageId,
    url,
    domain,
    title: parsed.title,
    database: parsed.database,
    properties: parsed.properties,
  };
}

// --- Helpers ---

export type NotionPropertyType = 'select' | 'multi_select' | 'date' | 'number' | 'rich_text' | 'status';

/** Map known property names to their Notion types per domain. */
export function getPropertyType(domain: TaskDomain, propertyName: string): NotionPropertyType {
  const typeMap: Record<string, NotionPropertyType> = {
    // Work
    'Priority': 'select',
    'Labels': 'multi_select',
    'Due date': 'date',
    'Due Date': 'date',
    'Est Duration Hrs': 'number',
    'Summary': 'rich_text',
    // Career
    'Category': 'select',
    'Phase': 'select',
    'Cadence': 'select',
    'Time Estimate': 'select',
    // Personal
    'Description': 'rich_text',
  };

  // Status is handled separately above, but include for completeness
  if (propertyName === 'Status') {
    return domain === 'work' ? 'status' : 'select';
  }

  return typeMap[propertyName] || 'rich_text';
}

/** Parse simple markdown page body into Notion blocks. */
export function parsePageBodyToBlocks(
  body: string,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
): any[] {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const blocks: any[] = [];
  const lines = body.split('\n');

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    if (trimmed.startsWith('## ')) {
      blocks.push({
        object: 'block',
        type: 'heading_2',
        heading_2: {
          rich_text: [{ type: 'text', text: { content: trimmed.slice(3) } }],
        },
      });
    } else if (trimmed.startsWith('- [ ] ')) {
      blocks.push({
        object: 'block',
        type: 'to_do',
        to_do: {
          rich_text: [{ type: 'text', text: { content: trimmed.slice(6) } }],
          checked: false,
        },
      });
    } else if (trimmed.startsWith('- ')) {
      blocks.push({
        object: 'block',
        type: 'bulleted_list_item',
        bulleted_list_item: {
          rich_text: [{ type: 'text', text: { content: trimmed.slice(2) } }],
        },
      });
    } else {
      blocks.push({
        object: 'block',
        type: 'paragraph',
        paragraph: {
          rich_text: [{ type: 'text', text: { content: trimmed } }],
        },
      });
    }
  }

  return blocks;
}
