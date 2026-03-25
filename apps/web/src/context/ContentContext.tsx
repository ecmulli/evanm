'use client';

import React, { createContext, useContext } from 'react';
import type { TextContent, FolderContent, DesktopIconConfig } from '@/types/window';

interface ContentContextType {
  textContents: Record<string, TextContent>;
  folderContents: Record<string, FolderContent>;
  desktopIcons: DesktopIconConfig[];
}

const ContentContext = createContext<ContentContextType>({
  textContents: {},
  folderContents: {},
  desktopIcons: [],
});

export function ContentProvider({
  content,
  children,
}: {
  content: ContentContextType;
  children: React.ReactNode;
}) {
  return (
    <ContentContext.Provider value={content}>
      {children}
    </ContentContext.Provider>
  );
}

export function useContent() {
  return useContext(ContentContext);
}

export function useTextContent(id: string): TextContent | undefined {
  const { textContents } = useContent();
  return textContents[id];
}

export function useFolderContent(id: string): FolderContent | undefined {
  const { folderContents } = useContent();
  return folderContents[id];
}

export function useDesktopIcons(): DesktopIconConfig[] {
  const { desktopIcons } = useContent();
  return desktopIcons;
}
