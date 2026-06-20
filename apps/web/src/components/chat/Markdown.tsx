'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// Rendered markdown with GFM (tables, strikethrough, task lists, autolinks).
export function Markdown({ children }: { children: string }) {
  return (
    <div className="chat-prose">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: (props) => <a {...props} target="_blank" rel="noopener noreferrer" />,
          code: ({ className, children, ...rest }) => {
            const inline = !className;
            return inline ? (
              <code className="chat-code-inline" {...rest}>{children}</code>
            ) : (
              <code className={className} {...rest}>{children}</code>
            );
          },
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
