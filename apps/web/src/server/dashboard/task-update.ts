import { getNotionClient, DB_CONFIG } from './notion-client';
import { getAnthropicClient, getPropertyType, parsePageBodyToBlocks } from './task-creation';
import { buildTaskEditPrompt } from './task-edit-prompt';
import type { TaskDomain } from './types';

const DEFAULT_MODEL = 'claude-haiku-4-5-20251001';

// --- Types ---

export interface TaskContext {
  title: string;
  status: string;
  priority: string | null;
  dueDate: string | null;
  domain: TaskDomain;
  metadata: Record<string, unknown>;
}

export interface DateRange {
  start: string;
  end?: string;
}

export interface PropertyUpdates {
  [key: string]: string | number | string[] | null | DateRange;
}

export interface PageBodyUpdate {
  action: 'append' | 'replace' | 'none';
  content: string | null;
}

export interface ParsedEdit {
  propertyUpdates: PropertyUpdates;
  pageBodyUpdate: PageBodyUpdate;
  summary: string;
}

// --- AI Parsing ---

export async function parseEditWithAI(
  instruction: string,
  task: TaskContext,
  domain: TaskDomain,
): Promise<ParsedEdit> {
  const anthropic = getAnthropicClient();
  const model = process.env.ANTHROPIC_MODEL || DEFAULT_MODEL;
  const currentDate = new Date().toISOString().split('T')[0];

  const taskContext = `Current task:
- Title: ${task.title}
- Domain: ${domain}
- Status: ${task.status}
- Priority: ${task.priority || 'not set'}
- Due Date: ${task.dueDate || 'not set'}
- Labels: ${(task.metadata?.labels as string[])?.join(', ') || 'none'}
- Category: ${(task.metadata?.category as string) || 'not set'}
- Phase: ${(task.metadata?.phase as string) || 'not set'}`;

  const userMessage = `${taskContext}

Edit instruction: ${instruction}`;

  const response = await anthropic.messages.create({
    model,
    max_tokens: 1024,
    system: buildTaskEditPrompt(currentDate),
    messages: [{ role: 'user', content: userMessage }],
  });

  const content = response.content[0];
  if (content.type !== 'text') {
    throw new Error('Unexpected response type from AI');
  }

  // Extract JSON from response
  const rawText = content.text.trim();
  const jsonStart = rawText.indexOf('{');
  const jsonEnd = rawText.lastIndexOf('}');
  if (jsonStart === -1 || jsonEnd === -1) {
    throw new Error('No JSON object found in AI response');
  }
  const jsonText = rawText.slice(jsonStart, jsonEnd + 1);

  return JSON.parse(jsonText) as ParsedEdit;
}

// --- Notion Update ---

export async function updateTaskInNotionFull(
  taskId: string,
  domain: TaskDomain,
  updates: PropertyUpdates,
  pageBodyUpdate?: PageBodyUpdate,
): Promise<void> {
  const notion = getNotionClient();
  const config = DB_CONFIG[domain];

  // Build Notion properties payload from flat updates
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const properties: Record<string, any> = {};

  for (const [key, value] of Object.entries(updates)) {
    if (value === null || value === undefined) continue;

    // Handle title property
    if (key === config.titleProperty) {
      properties[key] = {
        title: [{ text: { content: String(value) } }],
      };
      continue;
    }

    // Handle status property — uses different Notion types per domain
    if (key === config.statusProperty) {
      if (config.statusPropertyType === 'status') {
        properties[key] = { status: { name: String(value) } };
      } else {
        properties[key] = { select: { name: String(value) } };
      }
      continue;
    }

    // Use the property type mapper for everything else
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
        } else {
          // Single value — wrap in array
          properties[key] = {
            multi_select: [{ name: String(value) }],
          };
        }
        break;
      case 'date':
        if (typeof value === 'object' && value !== null && !Array.isArray(value) && 'start' in value) {
          const dateRange = value as DateRange;
          properties[key] = {
            date: { start: dateRange.start, ...(dateRange.end ? { end: dateRange.end } : {}) },
          };
        } else {
          properties[key] = { date: { start: String(value) } };
        }
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

  // Update the page properties if there are any
  if (Object.keys(properties).length > 0) {
    await notion.pages.update({
      page_id: taskId,
      properties,
    });
  }

  // Handle page body updates
  if (pageBodyUpdate && pageBodyUpdate.action !== 'none' && pageBodyUpdate.content) {
    const blocks = parsePageBodyToBlocks(pageBodyUpdate.content);
    if (blocks.length > 0) {
      if (pageBodyUpdate.action === 'append') {
        // Append new blocks at the end
        await notion.blocks.children.append({
          block_id: taskId,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          children: blocks as any,
        });
      } else if (pageBodyUpdate.action === 'replace') {
        // For replace: delete existing blocks then add new ones
        const existingBlocks = await notion.blocks.children.list({
          block_id: taskId,
        });

        // Delete all existing blocks
        for (const block of existingBlocks.results) {
          await notion.blocks.delete({ block_id: block.id });
        }

        // Add the new blocks
        await notion.blocks.children.append({
          block_id: taskId,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          children: blocks as any,
        });
      }
    }
  }
}
