import { TextContent, FolderContent, StickyNote, DesktopIconConfig } from '@/types/window';
import generatedContent from './generated-content.json';

// Type assertion for generated JSON content
interface GeneratedContent {
  textContents: Record<string, TextContent>;
  folderContents: Record<string, FolderContent>;
  desktopIcons: DesktopIconConfig[];
}

const content = generatedContent as unknown as GeneratedContent;

// Load content from generated JSON (created by scripts/generate-content.js)
export const textContents: Record<string, TextContent> = content.textContents;
export const folderContents: Record<string, FolderContent> = content.folderContents;
export const desktopIcons: DesktopIconConfig[] = content.desktopIcons;

// Initial guestbook notes (mock data - not file-based yet)
export const initialNotes: StickyNote[] = [
  {
    id: 'note-1',
    author: 'Visitor',
    message: 'Love the retro vibes! Takes me back to my first computer.',
    createdAt: new Date('2026-01-15'),
  },
  {
    id: 'note-2',
    author: 'Time Traveler',
    message: 'Is this 1995 or 2026? Either way, I\'m here for it.',
    createdAt: new Date('2026-01-10'),
  },
  {
    id: 'note-3',
    author: 'Pixel Fan',
    message: 'Finally, a website that doesn\'t need a loading spinner!',
    createdAt: new Date('2026-01-05'),
  },
];

// Helper functions to get content
export function getTextContent(id: string): TextContent | undefined {
  return textContents[id];
}

export function getFolderContent(id: string): FolderContent | undefined {
  return folderContents[id];
}
