import Desktop from "@/components/Desktop";
import { ContentProvider } from "@/context/ContentContext";
import { fetchNotionContent } from "@/server/content/notion-content";
import { unstable_cache } from "next/cache";

const getCachedContent = unstable_cache(
  async () => fetchNotionContent(),
  ['site-content'],
  { revalidate: 60 }
);

export default async function Home() {
  const content = await getCachedContent();

  return (
    <ContentProvider content={content}>
      <Desktop />
    </ContentProvider>
  );
}
