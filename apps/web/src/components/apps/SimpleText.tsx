'use client';

import React from 'react';
import Image from 'next/image';
import ReactMarkdown from 'react-markdown';
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
      <div className="markdown-content text-xs leading-relaxed">
        <ReactMarkdown
          components={{
            // Custom image rendering with Next.js Image
            img: ({ src, alt }) => (
              <span className="block my-2">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img 
                  src={src || ''} 
                  alt={alt || ''} 
                  className="max-w-full h-auto rounded"
                />
              </span>
            ),
            // Style links
            a: ({ href, children }) => (
              <a 
                href={href} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-[#A0584A] underline hover:text-[#152A54]"
              >
                {children}
              </a>
            ),
            // Style headers
            h1: ({ children }) => (
              <h1 className="text-base font-bold mt-3 mb-2">{children}</h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-sm font-bold mt-3 mb-1">{children}</h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-xs font-bold mt-2 mb-1">{children}</h3>
            ),
            // Style paragraphs
            p: ({ children }) => (
              <p className="mb-2">{children}</p>
            ),
            // Style lists
            ul: ({ children }) => (
              <ul className="list-disc ml-4 mb-2">{children}</ul>
            ),
            ol: ({ children }) => (
              <ol className="list-decimal ml-4 mb-2">{children}</ol>
            ),
            // Style code
            code: ({ children, className }) => {
              const isBlock = className?.includes('language-');
              if (isBlock) {
                return (
                  <code className="block bg-[#f5f5f5] p-2 my-2 rounded text-[10px] overflow-x-auto">
                    {children}
                  </code>
                );
              }
              return (
                <code className="bg-[#f5f5f5] px-1 rounded text-[10px]">
                  {children}
                </code>
              );
            },
            // Style blockquotes
            blockquote: ({ children }) => (
              <blockquote className="border-l-2 border-[#A0584A] pl-2 my-2 italic text-gray-600">
                {children}
              </blockquote>
            ),
            // Style horizontal rules
            hr: () => (
              <hr className="my-3 border-t border-gray-300" />
            ),
          }}
        >
          {content.content}
        </ReactMarkdown>
      </div>
    </div>
  );
}
