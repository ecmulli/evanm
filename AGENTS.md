# Agent Guide: evanm.xyz Content Management

This guide helps AI agents (Cursor, Claude, etc.) understand how to add and manage content on evanm.xyz.

## Architecture Overview

```
evanm.xyz/           → Retro Mac OS desktop (homepage)
evanm.xyz/chat       → AI task creation agent
evanm.xyz/login      → Authentication
```

The site is a Next.js app with a retro Mac OS desktop interface. Content appears as files and folders on the desktop.

## Content System

Content is **file-based**. The directory structure mirrors the website:

```
apps/web/src/content/
├── about-me.txt              → Desktop file "About Me.txt"
├── projects/                 → Desktop folder "Projects"
│   ├── evanm-xyz.txt         → File inside Projects folder
│   └── task-agent.txt        → File inside Projects folder
└── thoughts/                 → Desktop folder "Thoughts"
    ├── on-simplicity.txt     → File inside Thoughts folder
    ├── digital-gardens.txt   → File inside Thoughts folder
    └── hello-world.txt       → File inside Thoughts folder
```

**Adding content is as simple as adding a file to the appropriate directory.**

## File Format

Each `.txt` file uses a simple frontmatter format:

```
---
title: Display Title.txt
---
Your content here...
```

### Example: Adding a New Thought

Create `apps/web/src/content/thoughts/my-new-thought.txt`:

```
---
title: My New Thought.txt
---
Title Here
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Date: January 24, 2026

Your thought content here...

- End of file -
```

### Example: Adding a New Project

Create `apps/web/src/content/projects/my-project.txt`:

```
---
title: My Project.txt
---
My Project Name
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status: Active
Tech: List, Of, Technologies

DESCRIPTION:
What the project does and why it matters.

LINKS:
• Live: https://example.com
• Source: github.com/user/repo

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tagline.
```

### Example: Adding a New Folder

Create a new directory: `apps/web/src/content/my-folder/`

Then add `.txt` files inside it. The folder will automatically appear on the desktop.

## How It Works

1. Content files live in `apps/web/src/content/`
2. `npm run generate-content` reads all files and creates `generated-content.json`
3. The app imports this JSON at build time
4. Directory structure → Desktop folders
5. `.txt` files → Files inside folders (or on desktop if at root)

## Quick Reference

| Task | Action |
|------|--------|
| Add a thought | Create `src/content/thoughts/filename.txt` |
| Add a project | Create `src/content/projects/filename.txt` |
| Add desktop file | Create `src/content/filename.txt` |
| Add new folder | Create `src/content/foldername/` directory |
| Edit About Me | Edit `src/content/about-me.txt` |

## Content Style Guide

### Text Formatting
- Use `━` (box drawing character) for decorative lines
- Start files with a title and separator line
- Use `• ` for bullet points
- End files with `- End of file -` or a signature

### Naming Conventions
- Filenames: lowercase with hyphens (e.g., `my-project.txt`)
- The `title` in frontmatter is what displays in the UI

### Content Templates

**Thought Template:**
```
---
title: Thought Title.txt
---
Title
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Date: Month Day, Year

Content paragraphs here...

- End of file -
```

**Project Template:**
```
---
title: Project Name.txt
---
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
├── scripts/
│   └── generate-content.js    # Builds content JSON from files
├── src/
│   ├── content/               # ⭐ CONTENT LIVES HERE
│   │   ├── about-me.txt
│   │   ├── projects/
│   │   │   └── *.txt
│   │   └── thoughts/
│   │       └── *.txt
│   ├── data/
│   │   ├── content.ts         # Exports content (imports JSON)
│   │   └── generated-content.json  # Auto-generated, don't edit
│   ├── app/
│   │   ├── page.tsx           # Homepage (renders Desktop)
│   │   ├── chat/page.tsx      # Agent chat UI
│   │   └── login/page.tsx     # Auth page
│   └── components/
│       ├── Desktop.tsx        # Main desktop container
│       └── apps/
│           ├── SimpleText.tsx # Text file viewer
│           ├── Folder.tsx     # Folder viewer
│           └── Stickies.tsx   # Guestbook
```

## Build Process

1. `npm run generate-content` - Reads content files, creates JSON
2. `npm run build` - Runs generate-content, then builds Next.js

The `generate-content` script runs automatically before `dev` and `build`.

## Deployment

The site auto-deploys from the `desktop-app` branch via Railway.

After making changes:
1. Add/edit content files in `src/content/`
2. Commit changes
3. Push to `desktop-app` branch
4. Railway auto-deploys

## Notes

- The generated JSON (`generated-content.json`) is committed to git for simplicity
- The guestbook (`stickies`) uses mock data (not file-based)
- Windows open centered by default
- Desktop icons appear in the top-right corner
- Brand colors are defined in `globals.css`
