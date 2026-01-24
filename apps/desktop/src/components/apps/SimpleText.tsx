'use client';

import React from 'react';
import { getTextContent } from '@/data/content';

interface SimpleTextProps {
  contentId: string;
}

export default function SimpleText({ contentId }: SimpleTextProps) {
  const content = getTextContent(contentId);

  if (!content) {
    return (
      <div className="p-4">
        <p className="text-gray-500">File not found.</p>
      </div>
    );
  }

  return (
    <div className="p-4 h-full overflow-auto">
      <div className="whitespace-pre-wrap text-xs leading-relaxed">
        {content.content}
      </div>
    </div>
  );
}
