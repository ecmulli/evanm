import { getNotionClient, PROPS } from './notion-client';
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
  startTime: string | null;
  durationHours: number | null;
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
): Promise<ParsedEdit> {
  const anthropic = getAnthropicClient();
  const model = process.env.ANTHROPIC_MODEL || DEFAULT_MODEL;
  const currentDate = new Date().toISOString().split('T')[0];

  const scheduleInfo = task.startTime
    ? `${task.dueDate} at ${task.startTime}${task.durationHours ? ` (${task.durationHours}h duration)` : ''}`
    : task.dueDate || 'not set';

  const taskContext = `Current item:
- Title: ${task.title}
- Domain: ${task.domain}
- Status: ${task.status}
- Priority: ${task.priority || 'not set'}
- Due Date / Schedule: ${scheduleInfo}
- Category: ${(task.metadata?.category as string) || 'not set'}
- Time Estimate: ${(task.metadata?.timeEstimate as string) || 'not set'}`;

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
  updates: PropertyUpdates,
  pageBodyUpdate?: PageBodyUpdate,
): Promise<void> {
  const notion = getNotionClient();

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const properties: Record<string, any> = {};

  for (const [key, value] of Object.entries(updates)) {
    if (value === null || value === undefined) continue;

    // Handle title
    if (key === PROPS.title) {
      properties[key] = {
        title: [{ text: { content: String(value) } }],
      };
      continue;
    }

    const propType = getPropertyType(key);

    switch (propType) {
      case 'select':
        properties[key] = { select: { name: String(value) } };
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

  // Update properties
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
        await notion.blocks.children.append({
          block_id: taskId,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          children: blocks as any,
        });
      } else if (pageBodyUpdate.action === 'replace') {
        const existingBlocks = await notion.blocks.children.list({
          block_id: taskId,
        });
        for (const block of existingBlocks.results) {
          await notion.blocks.delete({ block_id: block.id });
        }
        await notion.blocks.children.append({
          block_id: taskId,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          children: blocks as any,
        });
      }
    }
  }
}
