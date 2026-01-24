'use client';

import React from 'react';
import Image from 'next/image';
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

  const isAboutMe = contentId === 'about-me';

  return (
    <div className="p-4 h-full overflow-auto">
      {isAboutMe && (
        <div className="mb-4 flex justify-center">
          <Image 
            src="/pfp.svg" 
            alt="Profile Picture" 
            width={78} 
            height={78}
            className="border-2 border-[#3A3530]"
            style={{ imageRendering: 'auto' }}
          />
        </div>
      )}
      <div className="whitespace-pre-wrap text-xs leading-relaxed">
        {content.content}
      </div>
    </div>
  );
}
