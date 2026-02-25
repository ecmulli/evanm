// Quick test: node test-notion.mjs <your-notion-api-key>
const apiKey = process.argv[2];
if (!apiKey) {
  console.error('Usage: node test-notion.mjs <NOTION_API_KEY>');
  process.exit(1);
}

const DB_ID = '25b0a348-5687-8091-9ae6-e160343ec336';

const res = await fetch(`https://api.notion.com/v1/databases/${DB_ID}/query`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${apiKey}`,
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    filter: {
      and: [
        { property: 'Status', status: { does_not_equal: 'Completed' } },
        { property: 'Status', status: { does_not_equal: 'Cancelled' } },
      ],
    },
    sorts: [{ property: 'Due date', direction: 'ascending' }],
    page_size: 5,
  }),
});

const data = await res.json();

if (!res.ok) {
  console.error('FAILED:', res.status, data);
  process.exit(1);
}

console.log(`SUCCESS — got ${data.results.length} tasks from Work DB\n`);
for (const page of data.results) {
  const title = page.properties['Task name']?.title?.[0]?.plain_text ?? '(untitled)';
  const status = page.properties['Status']?.status?.name ?? '?';
  console.log(`  [${status}] ${title}`);
}
