/* eslint-disable @next/next/no-img-element */
import { ImageResponse } from 'next/og';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { getCachedContent } from '@/server/content/cached';

export const runtime = 'nodejs';

const SIZE = { width: 1200, height: 630 };
const KNOWN_FOLDERS = ['thoughts', 'projects'];

function slugToContentId(slug: string[]): string {
  if (slug.length === 2 && KNOWN_FOLDERS.includes(slug[0])) {
    return `${slug[0]}-${slug[1]}`;
  }
  return slug.join('-');
}

function stripMarkdown(s: string): string {
  return s
    .replace(/```[\s\S]*?```/g, '')
    .replace(/!\[[^\]]*]\([^)]*\)/g, '')
    .replace(/\[([^\]]*)]\([^)]*\)/g, '$1')
    .replace(/[#*_>`~|-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function headlineSize(title: string): number {
  if (title.length <= 28) return 88;
  if (title.length <= 44) return 74;
  if (title.length <= 64) return 60;
  return 50;
}

// Fonts are bundled in /public/fonts as TTF (Satori does not accept woff2).
// Reading from disk avoids a runtime network hop and works the same in dev & prod.
async function loadFont(filename: string): Promise<ArrayBuffer> {
  const fontPath = path.join(process.cwd(), 'public', 'fonts', filename);
  const buf = await readFile(fontPath);
  return buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength) as ArrayBuffer;
}

interface RouteContext {
  params: Promise<{ slug: string[] }>;
}

export async function GET(_req: Request, { params }: RouteContext) {
  const { slug } = await params;
  const contentId = slugToContentId(slug);
  const { textContents } = await getCachedContent();
  const content = textContents[contentId];

  const title = content?.title ?? 'evanm.xyz';
  const description =
    content?.description ||
    (content
      ? stripMarkdown(content.content).slice(0, 160) + '…'
      : 'A retro Mac OS inspired personal site');

  const kicker =
    slug[0] && KNOWN_FOLDERS.includes(slug[0]) ? slug[0].toUpperCase() : 'EVANM.XYZ';
  const filename = `${slug[slug.length - 1] ?? 'index'}.txt`;

  const [serifBold, serifMedium, mono] = await Promise.all([
    loadFont('EBGaramond-700.ttf'),
    loadFont('EBGaramond-500.ttf'),
    loadFont('JetBrainsMono-600.ttf'),
  ]);

  const colors = {
    desktop: '#0D1A2D',
    window: '#FDFCFA',
    titlebarBg: '#E8E4E0',
    titlebarActive: '#A0584A',
    titlebarActiveAlt: '#BEA09A',
    border: '#3A3530',
    text: '#1c1a17',
    textMuted: '#4a463f',
  };

  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          background: colors.desktop,
          position: 'relative',
          fontFamily: 'EB Garamond',
        }}
      >
        {/* Star field */}
        {[
          { x: 100, y: 80, s: 3, o: 0.9 },
          { x: 240, y: 140, s: 2, o: 0.6 },
          { x: 380, y: 50, s: 3, o: 0.8 },
          { x: 540, y: 120, s: 2, o: 0.7 },
          { x: 720, y: 70, s: 3, o: 0.7 },
          { x: 880, y: 100, s: 2, o: 1 },
          { x: 1060, y: 40, s: 3, o: 0.6 },
          { x: 1140, y: 90, s: 2, o: 0.8 },
          { x: 60, y: 540, s: 2, o: 0.5 },
          { x: 980, y: 580, s: 3, o: 0.5 },
        ].map((d, i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: d.x,
              top: d.y,
              width: d.s,
              height: d.s,
              background: 'rgba(255,250,245,1)',
              opacity: d.o,
              borderRadius: 999,
              display: 'flex',
            }}
          />
        ))}

        {/* Window */}
        <div
          style={{
            position: 'absolute',
            top: 70,
            left: 70,
            width: 1060,
            height: 490,
            background: colors.window,
            border: `4px solid ${colors.border}`,
            boxShadow: `10px 10px 0 ${colors.border}`,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Titlebar */}
          <div
            style={{
              height: 42,
              borderBottom: `3px solid ${colors.border}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 12px',
              background: `linear-gradient(90deg, ${colors.titlebarActive} 0%, ${colors.titlebarActiveAlt} 50%, ${colors.titlebarActive} 100%)`,
            }}
          >
            <div
              style={{
                width: 20,
                height: 20,
                background: colors.window,
                border: `2px solid ${colors.border}`,
                color: colors.border,
                fontSize: 14,
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: 'JetBrains Mono',
              }}
            >
              ×
            </div>
            <div
              style={{
                background: colors.titlebarActive,
                color: 'white',
                border: '1px solid rgba(255,255,255,0.3)',
                padding: '3px 18px',
                fontSize: 16,
                fontWeight: 700,
                fontFamily: 'JetBrains Mono',
                maxWidth: 480,
                display: 'flex',
                textAlign: 'center',
              }}
            >
              {filename}
            </div>
            <div style={{ width: 20, display: 'flex' }} />
          </div>

          {/* Body */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              padding: '56px 70px 0 70px',
            }}
          >
            <div
              style={{
                fontFamily: 'JetBrains Mono',
                fontSize: 18,
                letterSpacing: 4,
                color: colors.titlebarActive,
                marginBottom: 26,
                display: 'flex',
              }}
            >
              {kicker}
            </div>
            <div
              style={{
                fontSize: headlineSize(title),
                lineHeight: 1.05,
                fontWeight: 700,
                color: colors.text,
                letterSpacing: '-0.01em',
                marginBottom: 28,
                display: 'flex',
                maxWidth: 880,
              }}
            >
              {title}
            </div>
            <div
              style={{
                fontSize: 26,
                lineHeight: 1.4,
                color: colors.textMuted,
                fontWeight: 500,
                maxWidth: 820,
                display: '-webkit-box',
                WebkitBoxOrient: 'vertical',
                WebkitLineClamp: 3,
                overflow: 'hidden',
              }}
            >
              {description}
            </div>
          </div>

          {/* Footer */}
          <div
            style={{
              position: 'absolute',
              bottom: 28,
              left: 70,
              right: 70,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: 999,
                  background: colors.titlebarActive,
                  border: `2px solid ${colors.border}`,
                  color: 'white',
                  fontWeight: 700,
                  fontSize: 18,
                  fontFamily: 'JetBrains Mono',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginRight: 16,
                }}
              >
                EM
              </div>
              <div style={{ fontSize: 22, color: colors.textMuted, display: 'flex' }}>
                Evan Mullins
              </div>
            </div>
            <div
              style={{
                fontFamily: 'JetBrains Mono',
                fontSize: 18,
                color: colors.border,
                background: colors.titlebarBg,
                border: `2px solid ${colors.border}`,
                padding: '6px 16px',
                display: 'flex',
              }}
            >
              evanm.xyz
            </div>
          </div>
        </div>
      </div>
    ),
    {
      ...SIZE,
      fonts: [
        { name: 'EB Garamond', data: serifBold, weight: 700, style: 'normal' },
        { name: 'EB Garamond', data: serifMedium, weight: 500, style: 'normal' },
        { name: 'JetBrains Mono', data: mono, weight: 600, style: 'normal' },
      ],
    }
  );
}
