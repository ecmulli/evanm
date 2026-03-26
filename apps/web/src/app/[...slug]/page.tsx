import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import Desktop from '@/components/Desktop';
import { ContentProvider } from '@/context/ContentContext';
import { fetchNotionContent } from '@/server/content/notion-content';
import { unstable_cache } from 'next/cache';

const KNOWN_FOLDERS = ['thoughts', 'projects'];

function slugToContentId(slug: string[]): string {
  if (slug.length === 2 && KNOWN_FOLDERS.includes(slug[0])) {
    return `${slug[0]}-${slug[1]}`;
  }
  return slug.join('-');
}

// Cache content fetching with 60-second revalidation
const getCachedContent = unstable_cache(
  async () => fetchNotionContent(),
  ['site-content'],
  { revalidate: 60 }
);

interface PageProps {
  params: Promise<{ slug: string[] }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const contentId = slugToContentId(slug);
  const { textContents } = await getCachedContent();
  const content = textContents[contentId];

  if (!content) {
    return { title: 'Not Found - evanm.xyz' };
  }

  const description =
    content.description ||
    content.content.replace(/[#*_\-=>`]/g, '').trim().slice(0, 155) + '...';

  return {
    title: `${content.title} - evanm.xyz`,
    description,
    openGraph: {
      title: content.title,
      description,
      url: `https://evanm.xyz/${slug.join('/')}`,
      siteName: 'evanm.xyz',
      type: 'article',
    },
  };
}

export default async function ContentPage({ params }: PageProps) {
  const { slug } = await params;
  const contentId = slugToContentId(slug);
  const content = await getCachedContent();

  if (!content.textContents[contentId]) {
    notFound();
  }

  return (
    <ContentProvider content={content}>
      <Desktop initialContentId={contentId} />
    </ContentProvider>
  );
}
