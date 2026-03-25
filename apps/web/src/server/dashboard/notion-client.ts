import { Client } from '@notionhq/client';

// Lazy-init singleton (avoids errors when NOTION_API_KEY is missing at import time)
let _client: Client | null = null;

export function getNotionClient(): Client {
  if (!_client) {
    const apiKey = process.env.NOTION_API_KEY;
    if (!apiKey) {
      throw new Error('NOTION_API_KEY environment variable is required');
    }
    _client = new Client({ auth: apiKey });
  }
  return _client;
}

// Single unified database
export const NOTION_DB_ID =
  process.env.NOTION_DB_ID || '6d67536239644847b4783fedf988982f';

// Consistent property names across all items
export const PROPS = {
  title: 'Name',
  status: 'Status',
  priority: 'Priority',
  dueDate: 'Due Date',
  domain: 'Domain',
  type: 'Type',
  category: 'Category',
  timeEstimate: 'Time Estimate',
} as const;
