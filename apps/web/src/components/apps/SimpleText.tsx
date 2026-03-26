'use client';

import React from 'react';
import Image from 'next/image';
import ReactMarkdown from 'react-markdown';
import { useTextContent } from '@/context/ContentContext';
import { useOpenApp } from '@/hooks/useWindow';

interface SimpleTextProps {
  contentId: string;
}

export default function SimpleText({ contentId }: SimpleTextProps) {
  const content = useTextContent(contentId);
  const { openFolder, openSimpleText } = useOpenApp();

  if (!content) {
    return (
      <div className="p-4">
        <p className="text-gray-500">File not found.</p>
      </div>
    );
  }

  const isAboutMe = contentId === 'about-me';

  // Determine parent folder for back navigation
  const KNOWN_FOLDERS = ['thoughts', 'projects'];
  const parentFolder = KNOWN_FOLDERS.find(f => contentId.startsWith(`${f}-`));

  // Handle internal links like #folder/projects or #file/about-me
  const handleInternalLink = (href: string) => {
    if (href.startsWith('#folder/')) {
      const folderId = href.replace('#folder/', '');
      const folderName = folderId.charAt(0).toUpperCase() + folderId.slice(1);
      openFolder(folderName, folderId);
      return true;
    }
    if (href.startsWith('#file/')) {
      const fileId = href.replace('#file/', '');
      openSimpleText(fileId, fileId);
      return true;
    }
    return false;
  };

  return (
    <div className="px-6 py-5 h-full overflow-auto sm:px-8 sm:py-6">
      {parentFolder && (
        <button
          onClick={() => openFolder(
            parentFolder.charAt(0).toUpperCase() + parentFolder.slice(1),
            parentFolder
          )}
          className="mb-4 text-xs tracking-wide uppercase text-[#A0584A] hover:text-[#152A54] cursor-pointer flex items-center gap-1.5 opacity-80 hover:opacity-100 transition-opacity"
        >
          <span>&larr;</span>
          <span>Back to {parentFolder.charAt(0).toUpperCase() + parentFolder.slice(1)}</span>
        </button>
      )}
      {isAboutMe && (
        <div className="mb-5 flex justify-center">
          <Image 
            src="/pfp.svg" 
            alt="Profile Picture" 
            width={78} 
            height={78}
            style={{ imageRendering: 'auto' }}
          />
        </div>
      )}
      <div className="markdown-content leading-[1.75] text-[#2A2520] max-w-[620px] mx-auto">
        <ReactMarkdown
          components={{
            img: ({ src, alt }) => (
              <span className="block my-4">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img 
                  src={src || ''} 
                  alt={alt || ''} 
                  className="max-w-full h-auto rounded"
                />
              </span>
            ),
            a: ({ href, children }) => {
              const isInternal = href?.startsWith('#folder/') || href?.startsWith('#file/');
              
              if (isInternal) {
                return (
                  <button
                    onClick={() => handleInternalLink(href || '')}
                    className="text-[#A0584A] underline decoration-[#A0584A]/40 underline-offset-2 hover:text-[#152A54] hover:decoration-[#152A54]/40 cursor-pointer transition-colors"
                  >
                    {children}
                  </button>
                );
              }
              
              return (
                <a 
                  href={href} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-[#A0584A] underline decoration-[#A0584A]/40 underline-offset-2 hover:text-[#152A54] hover:decoration-[#152A54]/40 transition-colors"
                >
                  {children}
                </a>
              );
            },
            h1: ({ children }) => (
              <h1 className="text-[1.65rem] font-bold mt-6 mb-4 text-[#152A54] border-b border-[#A0584A]/30 pb-2 leading-snug">{children}</h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-xl font-semibold mt-7 mb-3 text-[#152A54] leading-snug">{children}</h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-[1.05rem] font-semibold mt-5 mb-2 text-[#3A3530] leading-snug">{children}</h3>
            ),
            p: ({ children }) => (
              <p className="mb-4">{children}</p>
            ),
            ul: ({ children }) => (
              <ul className="list-disc ml-5 mb-4 space-y-1">{children}</ul>
            ),
            ol: ({ children }) => (
              <ol className="list-decimal ml-5 mb-4 space-y-1">{children}</ol>
            ),
            li: ({ children }) => (
              <li className="pl-1">{children}</li>
            ),
            code: ({ children, className }) => {
              const isBlock = className?.includes('language-');
              if (isBlock) {
                return (
                  <code className="block bg-[#f5f0eb] p-3 my-4 rounded text-[0.8rem] overflow-x-auto font-mono leading-relaxed border border-[#e8e0d8]">
                    {children}
                  </code>
                );
              }
              return (
                <code className="bg-[#f5f0eb] px-1.5 py-0.5 rounded text-[0.85em] font-mono border border-[#e8e0d8]">
                  {children}
                </code>
              );
            },
            blockquote: ({ children }) => (
              <blockquote className="border-l-[3px] border-[#A0584A]/50 pl-4 my-5 italic text-[#6B6560]">
                {children}
              </blockquote>
            ),
            hr: () => (
              <hr className="my-6 border-t border-[#e8e0d8]" />
            ),
            strong: ({ children }) => (
              <strong className="font-semibold text-[#1A1714]">{children}</strong>
            ),
            em: ({ children }) => (
              <em className="italic">{children}</em>
            ),
          }}
        >
          {content.content}
        </ReactMarkdown>
      </div>
    </div>
  );
}
