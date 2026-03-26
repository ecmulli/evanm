'use client';

import React from 'react';
import { PixelFileIcon } from '@/components/PixelIcons';
import { useOpenApp } from '@/hooks/useWindow';
import { useFolderContent } from '@/context/ContentContext';

interface FolderProps {
  contentId: string;
}

export default function Folder({ contentId }: FolderProps) {
  const { openSimpleText } = useOpenApp();
  const folder = useFolderContent(contentId);

  if (!folder) {
    return (
      <div className="p-4">
        <p className="text-gray-500">Folder not found.</p>
      </div>
    );
  }

  const handleClick = (item: { id: string; label: string; contentId?: string }) => {
    openSimpleText(item.label, item.contentId || item.id);
  };

  return (
    <div className="p-4 h-full overflow-auto bg-white">
      <div className="grid grid-cols-3 gap-4">
        {folder.items.map((item) => (
          <div
            key={item.id}
            className="flex flex-col items-center p-2 cursor-pointer hover:bg-[#A0584A]/10"
            onClick={() => handleClick(item)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleClick(item);
              }
            }}
          >
            <div className="w-14 h-14 flex items-center justify-center">
              <PixelFileIcon color="#152A54" />
            </div>
            <span className="text-xs text-center mt-1 max-w-[100px] break-words text-gray-800">
              {item.label}
            </span>
          </div>
        ))}
        {folder.items.length === 0 && (
          <p className="text-xs text-gray-500 col-span-3">
            This folder is empty.
          </p>
        )}
      </div>
    </div>
  );
}
