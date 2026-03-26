import { getNotionClient } from '../dashboard/notion-client';
import type { TextContent, FolderContent, DesktopIconConfig } from '@/types/window';
import generatedContent from '@/data/generated-content.json';

const CONTENT_DB_ID = process.env.NOTION_CONTENT_DB_ID || '';

interface ContentPage {
  id: string;
  name: string;
  type: 'thought' | 'project' | 'file';
  slug: string;
  description?: string;
  published: boolean;
  order?: number;
}

// Extract plain text from Notion rich text array
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function richTextToString(richText: any[]): string {
  return richText?.map((t: { plain_text: string }) => t.plain_text).join('') || '';
}

// Convert Notion blocks to markdown
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function blocksToMarkdown(blocks: any[]): string {
  const lines: string[] = [];

  for (const block of blocks) {
    const type = block.type;

    switch (type) {
      case 'paragraph':
        lines.push(richTextToString(block.paragraph.rich_text));
        lines.push('');
        break;
      case 'heading_1':
        lines.push(`# ${richTextToString(block.heading_1.rich_text)}`);
        lines.push('');
        break;
      case 'heading_2':
        lines.push(`## ${richTextToString(block.heading_2.rich_text)}`);
        lines.push('');
        break;
      case 'heading_3':
        lines.push(`### ${richTextToString(block.heading_3.rich_text)}`);
        lines.push('');
        break;
      case 'bulleted_list_item':
        lines.push(`- ${richTextToString(block.bulleted_list_item.rich_text)}`);
        break;
      case 'numbered_list_item':
        lines.push(`1. ${richTextToString(block.numbered_list_item.rich_text)}`);
        break;
      case 'code':
        lines.push(`\`\`\`${block.code.language || ''}`);
        lines.push(richTextToString(block.code.rich_text));
        lines.push('```');
        lines.push('');
        break;
      case 'quote':
        lines.push(`> ${richTextToString(block.quote.rich_text)}`);
        lines.push('');
        break;
      case 'divider':
        lines.push('---');
        lines.push('');
        break;
      case 'image': {
        const url = block.image.type === 'external'
          ? block.image.external.url
          : block.image.file.url;
        const caption = richTextToString(block.image.caption);
        lines.push(`![${caption}](${url})`);
        lines.push('');
        break;
      }
      case 'to_do':
        lines.push(`- [${block.to_do.checked ? 'x' : ' '}] ${richTextToString(block.to_do.rich_text)}`);
        break;
      default:
        // Skip unsupported block types
        break;
    }
  }

  return lines.join('\n').trim();
}

// Fetch all blocks for a page (handles pagination)
async function fetchAllBlocks(pageId: string): Promise<unknown[]> {
  const notion = getNotionClient();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const blocks: any[] = [];
  let cursor: string | undefined;

  do {
    const response = await notion.blocks.children.list({
      block_id: pageId,
      start_cursor: cursor,
      page_size: 100,
    });
    blocks.push(...response.results);
    cursor = response.has_more ? (response.next_cursor ?? undefined) : undefined;
  } while (cursor);

  return blocks;
}

// Query the Content database for all published pages
async function fetchContentPages(): Promise<ContentPage[]> {
  const notion = getNotionClient();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const pages: any[] = [];
  let cursor: string | undefined;

  do {
    const response = await notion.databases.query({
      database_id: CONTENT_DB_ID,
      filter: {
        property: 'Published',
        checkbox: { equals: true },
      },
      sorts: [{ property: 'Order', direction: 'ascending' }],
      start_cursor: cursor,
      page_size: 100,
    });
    pages.push(...response.results);
    cursor = response.has_more ? (response.next_cursor ?? undefined) : undefined;
  } while (cursor);

  return pages
    .filter((p) => 'properties' in p)
    .map((page) => {
      const props = page.properties;
      const name = richTextToString(props.Name?.title || []);
      const type = props.Type?.select?.name || 'file';
      const slug = richTextToString(props.Slug?.rich_text || []) || name.replace(/\.(txt|md)$/, '').toLowerCase().replace(/\s+/g, '-');
      const description = richTextToString(props.Description?.rich_text || []) || undefined;
      const published = props.Published?.checkbox ?? false;
      const order = props.Order?.number ?? undefined;

      return { id: page.id, name, type, slug, description, published, order };
    });
}

export interface GeneratedContent {
  textContents: Record<string, TextContent>;
  folderContents: Record<string, FolderContent>;
  desktopIcons: DesktopIconConfig[];
}

// Fallback to static generated content
function getStaticFallback(): GeneratedContent {
  return generatedContent as unknown as GeneratedContent;
}

// Fetch all content from Notion and build the same structure as generated-content.json
// Falls back to static generated-content.json on error
export async function fetchNotionContent(): Promise<GeneratedContent> {
  if (!CONTENT_DB_ID) {
    console.warn('[content] NOTION_CONTENT_DB_ID not set, using static fallback');
    return getStaticFallback();
  }

  try {
    return await fetchNotionContentFromApi();
  } catch (err) {
    console.error('[content] Failed to fetch from Notion, using static fallback:', err);
    return getStaticFallback();
  }
}

async function fetchNotionContentFromApi(): Promise<GeneratedContent> {
  const textContents: Record<string, TextContent> = {};
  const folderContents: Record<string, FolderContent> = {};
  const desktopIcons: DesktopIconConfig[] = [];

  const pages = await fetchContentPages();

  // Fetch all page bodies in parallel
  const pageContents = await Promise.all(
    pages.map(async (page) => {
      const blocks = await fetchAllBlocks(page.id);
      const markdown = blocksToMarkdown(blocks);
      return { page, markdown };
    })
  );

  // Organize by type
  const folderTypes = ['thought', 'project'] as const;
  const folderMap: Record<string, { title: string; items: DesktopIconConfig[] }> = {};

  for (const folderType of folderTypes) {
    const plural = folderType === 'thought' ? 'thoughts' : 'projects';
    folderMap[plural] = { title: plural.charAt(0).toUpperCase() + plural.slice(1), items: [] };
  }

  for (const { page, markdown } of pageContents) {
    if (page.type === 'thought' || page.type === 'project') {
      const plural = page.type === 'thought' ? 'thoughts' : 'projects';
      const contentId = `${plural}-${page.slug}`;

      textContents[contentId] = {
        id: contentId,
        title: page.name,
        content: markdown,
        ...(page.description && { description: page.description }),
      };

      folderMap[plural].items.push({
        id: `${contentId}-icon`,
        label: page.name,
        iconType: 'file',
        appType: 'simpletext',
        contentId,
      });
    } else {
      // Root-level file
      const contentId = page.slug;
      textContents[contentId] = {
        id: contentId,
        title: page.name,
        content: markdown,
        ...(page.description && { description: page.description }),
      };

      desktopIcons.push({
        id: `${contentId}-icon`,
        label: page.name,
        iconType: 'file',
        appType: 'simpletext',
        contentId,
      });
    }
  }

  // Build folder contents and desktop icons for folders
  for (const [folderId, folder] of Object.entries(folderMap)) {
    folderContents[folderId] = {
      id: folderId,
      title: folder.title,
      items: folder.items,
    };

    desktopIcons.push({
      id: `${folderId}-icon`,
      label: folder.title,
      iconType: 'folder',
      appType: 'folder',
      contentId: folderId,
    });
  }

  return { textContents, folderContents, desktopIcons };
}
