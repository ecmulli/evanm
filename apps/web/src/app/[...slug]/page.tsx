import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import Desktop from '@/components/Desktop';
import { textContents } from '@/data/content';

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

export function generateStaticParams() {
  return Object.keys(textContents).map((contentId) => {
    for (const folder of KNOWN_FOLDERS) {
      if (contentId.startsWith(`${folder}-`)) {
        const fileSlug = contentId.slice(folder.length + 1);
        return { slug: [folder, fileSlug] };
      }
    }
    return { slug: [contentId] };
  });
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const contentId = slugToContentId(slug);
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
  const content = textContents[contentId];

  if (!content) {
    notFound();
  }

  return <Desktop initialContentId={contentId} />;
}
