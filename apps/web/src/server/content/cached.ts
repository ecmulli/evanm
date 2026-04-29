import { unstable_cache } from 'next/cache';
import { fetchNotionContent } from './notion-content';

// Cache content fetching with 60-second revalidation.
// Same cache key across page.tsx, generateMetadata, and opengraph-image.tsx
// so we only hit Notion once per ISR window.
export const getCachedContent = unstable_cache(
  async () => fetchNotionContent(),
  ['site-content'],
  { revalidate: 60 }
);
