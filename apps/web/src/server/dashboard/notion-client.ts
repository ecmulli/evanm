import { Client } from '@notionhq/client';
import type { TaskDomain } from './types';

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

// Notion user ID for "assigned to me" filtering (Evan Mullins)
export const NOTION_USER_ID = process.env.NOTION_USER_ID || 'e0c53979-a938-45b7-9c34-3ed48fd52338';

// Database configuration per domain
export interface DbConfig {
  databaseId: string;
  statusPropertyType: 'status' | 'select'; // Work uses "status" (grouped), Career/Personal use "select"
  titleProperty: string;
  statusProperty: string;
  priorityProperty: string | null;
  dueDateProperty: string;
  assigneeProperty?: string; // People property for assignee filtering
}

export const DB_CONFIG: Record<TaskDomain, DbConfig> = {
  work: {
    databaseId: process.env.NOTION_WORK_DB || '25b0a348-5687-8091-9ae6-e160343ec336',
    statusPropertyType: 'status',
    titleProperty: 'Task name',
    statusProperty: 'Status',
    priorityProperty: 'Priority',
    dueDateProperty: 'Due date',
    assigneeProperty: 'Assignee',
  },
  career: {
    databaseId: process.env.NOTION_CAREER_DB || '064411ee-aa98-4432-9bc8-8a3d78ad73f4',
    statusPropertyType: 'select',
    titleProperty: 'Name',
    statusProperty: 'Status',
    priorityProperty: null,
    dueDateProperty: 'Due Date',
  },
  personal: {
    databaseId: process.env.NOTION_PERSONAL_DB || '4a14b9e60f034daa97ba891b4645c9e1',
    statusPropertyType: 'select',
    titleProperty: 'Name',
    statusProperty: 'Status',
    priorityProperty: 'Priority',
    dueDateProperty: 'Due Date',
  },
};
