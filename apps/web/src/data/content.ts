import { TextContent, FolderContent, StickyNote, DesktopIconConfig } from '@/types/window';

// Text file contents
export const textContents: Record<string, TextContent> = {
  'about-me': {
    id: 'about-me',
    title: 'About Me.txt',
    content: `Welcome to my corner of the internet!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hello, I'm [Your Name].

I'm a developer, creator, and digital explorer 
who appreciates the charm of vintage computing.

This website is a love letter to the golden age
of personal computing - when interfaces had
character and every pixel was intentional.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INTERESTS:
• Building things on the web
• Retro computing & pixel art
• Coffee and good conversations

CONTACT:
• Email: hello@example.com
• GitHub: @username
• Twitter: @username

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Thanks for visiting! Feel free to leave
a note in the Guestbook.

- Created with <3 in 2026
`,
  },
  'thought-1': {
    id: 'thought-1',
    title: 'On Simplicity.txt',
    content: `On Simplicity
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Date: January 15, 2026

There's something beautiful about constraints.

When you have limited resources, limited pixels,
limited colors - you're forced to be intentional
about every decision you make.

Modern software often suffers from feature bloat.
We add more because we can, not because we should.

The old Mac interfaces understood this. Every
element had a purpose. Every interaction was
considered.

Maybe that's why they still feel so satisfying
to use, even decades later.

Sometimes less really is more.

- End of file -
`,
  },
  'thought-2': {
    id: 'thought-2',
    title: 'Digital Gardens.txt',
    content: `Digital Gardens
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Date: January 10, 2026

I've been thinking about websites as gardens.

Not the manicured, corporate kind - but the
wild, personal kind. The kind that grows
organically over time.

A digital garden is:
• Always a work in progress
• Personal and imperfect
• A place for ideas to grow
• Connected through winding paths

This desktop is my garden. Each file is a
seed. Some might grow into something bigger.
Others might just stay as little notes.

And that's okay.

- End of file -
`,
  },
  'thought-3': {
    id: 'thought-3',
    title: 'Hello World.txt',
    content: `Hello, World!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Date: January 1, 2026

The classic first program. The tradition that
spans decades and countless programming languages.

    10 PRINT "HELLO, WORLD!"
    20 END

Why do we start here?

Maybe because it's a greeting. A first word.
A declaration that we exist in this digital
space and we have something to say.

Hello, World. Nice to meet you.

- End of file -
`,
  },
};

// Folder contents
export const folderContents: Record<string, FolderContent> = {
  'thoughts': {
    id: 'thoughts',
    title: 'Thoughts',
    items: [
      {
        id: 'thought-1-icon',
        label: 'On Simplicity.txt',
        iconType: 'file',
        appType: 'simpletext',
        contentId: 'thought-1',
      },
      {
        id: 'thought-2-icon',
        label: 'Digital Gardens.txt',
        iconType: 'file',
        appType: 'simpletext',
        contentId: 'thought-2',
      },
      {
        id: 'thought-3-icon',
        label: 'Hello World.txt',
        iconType: 'file',
        appType: 'simpletext',
        contentId: 'thought-3',
      },
    ],
  },
};

// Initial guestbook notes (mock data)
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

// Desktop icons configuration
export const desktopIcons: DesktopIconConfig[] = [
  {
    id: 'about-me-icon',
    label: 'About Me.txt',
    iconType: 'file',
    appType: 'simpletext',
    contentId: 'about-me',
  },
  {
    id: 'thoughts-icon',
    label: 'Thoughts',
    iconType: 'folder',
    appType: 'folder',
    contentId: 'thoughts',
  },
  {
    id: 'guestbook-icon',
    label: 'Guestbook',
    iconType: 'app',
    appType: 'stickies',
  },
];

// Helper functions to get content
export function getTextContent(id: string): TextContent | undefined {
  return textContents[id];
}

export function getFolderContent(id: string): FolderContent | undefined {
  return folderContents[id];
}
