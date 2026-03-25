import Anthropic from '@anthropic-ai/sdk';
import { getNotionClient, NOTION_DB_ID, PROPS } from './notion-client';
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

export interface ParsedTask {
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
  type: 'task';
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

  // Extract JSON object from response
  const rawText = content.text.trim();
  const jsonStart = rawText.indexOf('{');
  const jsonEnd = rawText.lastIndexOf('}');
  if (jsonStart === -1 || jsonEnd === -1) {
    throw new Error('No JSON object found in AI response');
  }
  const jsonText = rawText.slice(jsonStart, jsonEnd + 1);

  return JSON.parse(jsonText) as ParsedTask;
}

// --- Notion Creation ---

export async function createTaskInNotion(
  parsed: ParsedTask,
  domain: TaskDomain,
): Promise<CreateTaskResult> {
  const notion = getNotionClient();
  const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const properties: Record<string, any> = {
    [PROPS.title]: { title: [{ text: { content: parsed.title } }] },
    [PROPS.type]: { select: { name: 'Task' } },
    [PROPS.domain]: { select: { name: capitalize(domain) } },
    [PROPS.status]: { select: { name: 'To Do' } },
  };

  // Map AI-inferred properties
  for (const [key, value] of Object.entries(parsed.properties)) {
    if (value === null || value === undefined) continue;

    // Skip properties we already set above
    if (key === PROPS.status || key === PROPS.title || key === PROPS.domain || key === PROPS.type) continue;

    const propType = getPropertyType(key);

    switch (propType) {
      case 'select':
        properties[key] = { select: { name: String(value) } };
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
        properties[key] = {
          rich_text: [{ text: { content: String(value) } }],
        };
    }
  }

  // Default due date: 1 week from now if not set
  if (!properties[PROPS.dueDate]) {
    const oneWeekFromNow = new Date();
    oneWeekFromNow.setDate(oneWeekFromNow.getDate() + 7);
    properties[PROPS.dueDate] = { date: { start: oneWeekFromNow.toISOString().split('T')[0] } };
  }

  const response = await notion.pages.create({
    parent: { database_id: NOTION_DB_ID },
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
      console.error('Failed to append page body:', err);
    }
  }

  return {
    id: pageId,
    url,
    domain,
    title: parsed.title,
    type: 'task',
    properties: parsed.properties,
  };
}

// --- Helpers ---

export type NotionPropertyType = 'select' | 'date' | 'number' | 'rich_text';

export function getPropertyType(propertyName: string): NotionPropertyType {
  const typeMap: Record<string, NotionPropertyType> = {
    'Priority': 'select',
    'Category': 'select',
    'Time Estimate': 'select',
    'Due Date': 'date',
    'Domain': 'select',
    'Type': 'select',
    'Status': 'select',
  };

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
