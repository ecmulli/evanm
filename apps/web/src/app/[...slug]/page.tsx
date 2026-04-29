import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import Desktop from '@/components/Desktop';
import { ContentProvider } from '@/context/ContentContext';
import { getCachedContent } from '@/server/content/cached';

const KNOWN_FOLDERS = ['thoughts', 'projects'];

function slugToContentId(slug: string[]): string {
  if (slug.length === 2 && KNOWN_FOLDERS.includes(slug[0])) {
    return `${slug[0]}-${slug[1]}`;
  }
  return slug.join('-');
}

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

  const url = `/${slug.join('/')}`;
  const ogImage = `/api/og/${slug.join('/')}`;
  const isThought = slug[0] === 'thoughts';

  // OG image is generated on demand by /api/og/[...slug]/route.tsx — kept
  // outside the catch-all because Next.js disallows segments after a
  // catch-all (which co-located `opengraph-image.tsx` would create).
  return {
    title: `${content.title} - evanm.xyz`,
    description,
    alternates: { canonical: url },
    openGraph: {
      title: content.title,
      description,
      url,
      siteName: 'evanm.xyz',
      type: isThought ? 'article' : 'website',
      images: [{ url: ogImage, width: 1200, height: 630, alt: content.title }],
      ...(isThought && {
        authors: ['Evan Mullins'],
      }),
    },
    twitter: {
      card: 'summary_large_image',
      title: content.title,
      description,
      creator: '@evancmullins',
      images: [ogImage],
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
