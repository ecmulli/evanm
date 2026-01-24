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

Content is **file-based with full Markdown support**. The directory structure mirrors the website:

```
apps/web/src/content/
├── about-me.md               → Desktop file "About Me.md"
├── projects/                 → Desktop folder "Projects"
│   ├── evanm-xyz.md          → File inside Projects folder
│   └── task-agent.md         → File inside Projects folder
└── thoughts/                 → Desktop folder "Thoughts"
    ├── on-simplicity.md      → File inside Thoughts folder
    ├── digital-gardens.md    → File inside Thoughts folder
    └── hello-world.md        → File inside Thoughts folder
```

**Adding content is as simple as adding a file to the appropriate directory.**

## File Format

Each `.md` file uses frontmatter + markdown content:

```markdown
---
title: Display Title.md
---
# Your Title

Your **markdown** content here with *formatting*!

- Bullet points
- [Links](https://example.com)
- Images, code blocks, etc.
```

## Markdown Features

Full markdown support including:

- **Bold** and *italic* text
- [Links](https://example.com) (open in new tab)
- Headers (`#`, `##`, `###`)
- Bullet and numbered lists
- `inline code` and code blocks
- > Blockquotes
- Horizontal rules (`---`)
- Images: `![alt text](/images/photo.png)`

### Images

Place images in `apps/web/public/images/` and reference them:

```markdown
![Screenshot](/images/my-screenshot.png)
```

### Example: Adding a New Thought

Create `apps/web/src/content/thoughts/my-new-thought.md`:

```markdown
---
title: My New Thought.md
---
# My New Thought

*January 24, 2026*

Your thought content here with **bold** and *italic* text.

> A blockquote for emphasis

- Point one
- Point two
```

### Example: Adding a New Project

Create `apps/web/src/content/projects/my-project.md`:

```markdown
---
title: My Project.md
---
# My Project Name

**Status:** Active  
**Tech:** React, Node.js, PostgreSQL

## Description

What the project does and why it matters.

![Screenshot](/images/my-project.png)

## Links

- [Live Site](https://example.com)
- [Source Code](https://github.com/user/repo)

---

*Tagline here.*
```

### Example: Adding a New Folder

Create a new directory: `apps/web/src/content/my-folder/`

Then add `.md` files inside it. The folder will automatically appear on the desktop.

## How It Works

1. Content files live in `apps/web/src/content/`
2. `npm run generate-content` reads all files and creates `generated-content.json`
3. The app imports this JSON at build time
4. Directory structure → Desktop folders
5. `.md` files → Files inside folders (or on desktop if at root)

## Quick Reference

| Task | Action |
|------|--------|
| Add a thought | Create `src/content/thoughts/filename.md` |
| Add a project | Create `src/content/projects/filename.md` |
| Add desktop file | Create `src/content/filename.md` |
| Add new folder | Create `src/content/foldername/` directory |
| Add an image | Place in `public/images/`, reference as `/images/name.png` |
| Edit About Me | Edit `src/content/about-me.md` |

## Naming Conventions

- Filenames: lowercase with hyphens (e.g., `my-project.md`)
- The `title` in frontmatter is what displays in the UI
- Use `.md` extension (`.txt` also works for plain text)

## Content Templates

**Thought Template:**
```markdown
---
title: Thought Title.md
---
# Thought Title

*Month Day, Year*

Content paragraphs here...

> Key insight or quote
```

**Project Template:**
```markdown
---
title: Project Name.md
---
# Project Name

**Status:** Active/Complete/WIP  
**Tech:** Tech, Stack, Here

## Description

What it does.

## Links

- [Live](https://url)
- [Source](https://repo)

---

*Tagline.*
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
