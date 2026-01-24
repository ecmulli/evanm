# Agent Guide: evanm.xyz Content Management

This guide helps AI agents (Cursor, Claude, etc.) understand how to add and manage content on evanm.xyz.

## Architecture Overview

```
evanm.xyz/           → Retro Mac OS desktop (homepage)
evanm.xyz/chat       → AI task creation agent
evanm.xyz/login      → Authentication
```

The site is a Next.js app with a retro Mac OS desktop interface. Content appears as files and folders on the desktop.

## Content Location

All site content lives in a single file:

```
apps/web/src/data/content.ts
```

## Content Types

### 1. Text Files (SimpleText)
Used for: About Me, Thoughts, Projects, any text content

```typescript
// Add to textContents object
'my-content-id': {
  id: 'my-content-id',
  title: 'Display Title.txt',
  content: `Your content here.

Use backticks for multi-line strings.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ (decorative line)

Content supports plain text formatting.
`,
},
```

### 2. Folders
Used for: Grouping related files (Projects, Thoughts, etc.)

```typescript
// Add to folderContents object
'my-folder': {
  id: 'my-folder',
  title: 'Folder Name',
  items: [
    {
      id: 'item-1-icon',
      label: 'File Name.txt',
      iconType: 'file',
      appType: 'simpletext',
      contentId: 'my-content-id',  // References textContents
    },
    // More items...
  ],
},
```

### 3. Desktop Icons
Files and folders that appear on the desktop background.

```typescript
// Add to desktopIcons array
{
  id: 'my-icon',
  label: 'Display Name',
  iconType: 'file' | 'folder' | 'app',
  appType: 'simpletext' | 'folder' | 'stickies',
  contentId: 'content-or-folder-id',  // Optional for 'stickies'
},
```

## How to Add Content

### Adding a New Thought

1. Add the text content:
```typescript
// In textContents:
'thought-new': {
  id: 'thought-new',
  title: 'My New Thought.txt',
  content: `Title Here
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Date: Month Day, Year

Your thought content here...

- End of file -
`,
},
```

2. Add to Thoughts folder:
```typescript
// In folderContents['thoughts'].items:
{
  id: 'thought-new-icon',
  label: 'My New Thought.txt',
  iconType: 'file',
  appType: 'simpletext',
  contentId: 'thought-new',
},
```

### Adding a New Project

1. Add the project text content:
```typescript
// In textContents:
'project-myproject': {
  id: 'project-myproject',
  title: 'My Project.txt',
  content: `My Project Name
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status: Active | Completed | In Progress
Tech: List, Of, Technologies

DESCRIPTION:
What the project does and why it matters.

Features:
• Feature one
• Feature two

LINKS:
• Live: https://example.com
• Source: github.com/user/repo

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tagline or closing thought.
`,
},
```

2. Add to Projects folder:
```typescript
// In folderContents['projects'].items:
{
  id: 'project-myproject-icon',
  label: 'My Project.txt',
  iconType: 'file',
  appType: 'simpletext',
  contentId: 'project-myproject',
},
```

### Adding a New Desktop Folder

1. Create the folder content:
```typescript
// In folderContents:
'my-folder': {
  id: 'my-folder',
  title: 'My Folder',
  items: [
    // Add items here
  ],
},
```

2. Add desktop icon:
```typescript
// In desktopIcons:
{
  id: 'my-folder-icon',
  label: 'My Folder',
  iconType: 'folder',
  appType: 'folder',
  contentId: 'my-folder',
},
```

## Content Style Guide

### Text Formatting
- Use `━` (box drawing character) for decorative lines
- Start files with a title and separator line
- Use `• ` for bullet points
- End files with `- End of file -` or a signature

### Naming Conventions
- Content IDs: `type-slug` (e.g., `thought-on-simplicity`, `project-evanm-xyz`)
- Icon IDs: `content-id-icon` (e.g., `thought-1-icon`)
- Use lowercase with hyphens

### Content Templates

**Thought Template:**
```
Title
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Date: Month Day, Year

Content paragraphs here...

- End of file -
```

**Project Template:**
```
Project Name
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status: Active
Tech: Tech, Stack, Here

DESCRIPTION:
What it does.

LINKS:
• Live: url
• Source: repo

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tagline.
```

## File Structure

```
apps/web/
├── src/
│   ├── app/
│   │   ├── page.tsx          # Homepage (renders Desktop)
│   │   ├── chat/page.tsx     # Agent chat UI
│   │   └── login/page.tsx    # Auth page
│   ├── components/
│   │   ├── Desktop.tsx       # Main desktop container
│   │   ├── MenuBar.tsx       # Top menu bar
│   │   ├── DesktopIcon.tsx   # Clickable icons
│   │   ├── WindowFrame.tsx   # Draggable windows
│   │   └── apps/
│   │       ├── SimpleText.tsx  # Text file viewer
│   │       ├── Folder.tsx      # Folder viewer
│   │       └── Stickies.tsx    # Guestbook
│   ├── context/
│   │   └── WindowContext.tsx # Window state management
│   ├── data/
│   │   └── content.ts        # ⭐ ALL CONTENT LIVES HERE
│   └── types/
│       └── window.ts         # TypeScript types
```

## Quick Reference

| Task | Location | What to Edit |
|------|----------|--------------|
| Add thought | `content.ts` | `textContents` + `folderContents['thoughts'].items` |
| Add project | `content.ts` | `textContents` + `folderContents['projects'].items` |
| Add desktop icon | `content.ts` | `desktopIcons` array |
| Add new folder | `content.ts` | `folderContents` + `desktopIcons` |
| Edit About Me | `content.ts` | `textContents['about-me']` |

## Deployment

The site auto-deploys from the `desktop-app` branch via Railway.

After making changes:
1. Commit to `desktop-app` branch
2. Push to origin
3. Railway auto-deploys

## Notes

- The guestbook (`stickies`) currently uses mock data
- Windows open centered by default, with cascading for multiple windows
- Desktop icons appear in the top-right corner
- The site uses brand colors defined in `globals.css`
