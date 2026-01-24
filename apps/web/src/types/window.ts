export type AppType = 'simpletext' | 'stickies' | 'folder';

export interface Position {
  x: number;
  y: number;
}

export interface WindowState {
  id: string;
  appType: AppType;
  title: string;
  position: Position;
  zIndex: number;
  isMinimized: boolean;
  contentId?: string; // For loading specific content (e.g., which text file to display)
}

export interface OpenWindowConfig {
  appType: AppType;
  title: string;
  contentId?: string;
  position?: Position;
}

export interface WindowContextType {
  windows: WindowState[];
  topZIndex: number;
  openWindow: (config: OpenWindowConfig) => void;
  closeWindow: (id: string) => void;
  focusWindow: (id: string) => void;
  minimizeWindow: (id: string) => void;
}

export interface DesktopIconConfig {
  id: string;
  label: string;
  iconType: 'file' | 'folder' | 'app';
  appType: AppType;
  contentId?: string;
}

export interface StickyNote {
  id: string;
  author: string;
  message: string;
  createdAt: Date;
}

export interface TextContent {
  id: string;
  title: string;
  content: string;
}

export interface FolderContent {
  id: string;
  title: string;
  items: DesktopIconConfig[];
}
