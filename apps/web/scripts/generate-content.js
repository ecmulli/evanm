#!/usr/bin/env node

/**
 * This script reads content files and generates a JSON file
 * that can be imported by the app.
 * 
 * Run: node scripts/generate-content.js
 * Or: npm run generate-content
 */

const fs = require('fs');
const path = require('path');

const CONTENT_DIR = path.join(__dirname, '../src/content');
const OUTPUT_FILE = path.join(__dirname, '../src/data/generated-content.json');

/**
 * Parse frontmatter from a text file
 */
function parseFrontmatter(fileContent) {
  const frontmatterRegex = /^---\n([\s\S]*?)\n---\n([\s\S]*)$/;
  const match = fileContent.match(frontmatterRegex);
  
  if (match) {
    const frontmatter = match[1];
    const content = match[2].trim();
    
    const titleMatch = frontmatter.match(/title:\s*(.+)/);
    const title = titleMatch ? titleMatch[1].trim() : 'Untitled.txt';
    
    return { title, content };
  }
  
  return { title: 'Untitled.txt', content: fileContent.trim() };
}

/**
 * Convert filename to content ID
 */
function filenameToId(filename) {
  return filename.replace(/\.(txt|md)$/, '');
}

/**
 * Check if file is a content file (.txt or .md)
 */
function isContentFile(filename) {
  return filename.endsWith('.txt') || filename.endsWith('.md');
}

/**
 * Load all content and generate the data structure
 */
function generateContent() {
  const textContents = {};
  const folderContents = {};
  const desktopIcons = [];
  
  // Check if content directory exists
  if (!fs.existsSync(CONTENT_DIR)) {
    console.error('Content directory not found:', CONTENT_DIR);
    process.exit(1);
  }
  
  // Load root-level files (like about-me.txt or about-me.md)
  const rootFiles = fs.readdirSync(CONTENT_DIR).filter(f => isContentFile(f));
  for (const filename of rootFiles) {
    const filePath = path.join(CONTENT_DIR, filename);
    const fileContent = fs.readFileSync(filePath, 'utf-8');
    const { title, content } = parseFrontmatter(fileContent);
    const id = filenameToId(filename);
    
    textContents[id] = { id, title, content };
    
    // Add to desktop icons
    desktopIcons.push({
      id: `${id}-icon`,
      label: title,
      iconType: 'file',
      appType: 'simpletext',
      contentId: id,
    });
  }
  
  // Load subdirectories
  const subdirs = fs.readdirSync(CONTENT_DIR).filter(f => {
    const fullPath = path.join(CONTENT_DIR, f);
    return fs.statSync(fullPath).isDirectory();
  });
  
  for (const subdir of subdirs) {
    const subdirPath = path.join(CONTENT_DIR, subdir);
    const files = fs.readdirSync(subdirPath).filter(f => isContentFile(f));
    
    const folderTitle = subdir.charAt(0).toUpperCase() + subdir.slice(1);
    const items = [];
    
    for (const filename of files) {
      const filePath = path.join(subdirPath, filename);
      const fileContent = fs.readFileSync(filePath, 'utf-8');
      const { title, content } = parseFrontmatter(fileContent);
      const contentId = `${subdir}-${filenameToId(filename)}`;
      
      textContents[contentId] = { id: contentId, title, content };
      
      items.push({
        id: `${contentId}-icon`,
        label: title,
        iconType: 'file',
        appType: 'simpletext',
        contentId,
      });
    }
    
    folderContents[subdir] = {
      id: subdir,
      title: folderTitle,
      items,
    };
    
    // Add folder to desktop icons
    desktopIcons.push({
      id: `${subdir}-icon`,
      label: folderTitle,
      iconType: 'folder',
      appType: 'folder',
      contentId: subdir,
    });
  }
  
  // Guestbook is hidden until persistence is implemented
  // See AGENTS.md for details on resuming this feature
  // desktopIcons.push({
  //   id: 'guestbook-icon',
  //   label: 'Guestbook',
  //   iconType: 'app',
  //   appType: 'stickies',
  // });
  
  return { textContents, folderContents, desktopIcons };
}

// Generate and write content
const content = generateContent();
fs.writeFileSync(OUTPUT_FILE, JSON.stringify(content, null, 2));
console.log('✅ Generated content:', OUTPUT_FILE);
console.log(`   - ${Object.keys(content.textContents).length} text files`);
console.log(`   - ${Object.keys(content.folderContents).length} folders`);
console.log(`   - ${content.desktopIcons.length} desktop icons`);
