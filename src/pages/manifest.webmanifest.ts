import site from 'virtual:astro-reading-theme/config';
import type { APIRoute } from 'astro';
import { base } from '../lib/base';

export const GET: APIRoute = () =>
  new Response(
    JSON.stringify({
      id: `${base}/`,
      name: site.name,
      short_name: site.name,
      description: site.manifestDescription,
      start_url: `${base}/`,
      scope: `${base}/`,
      display: 'standalone',
      background_color: '#f7f4ed',
      theme_color: '#f7f4ed',
      icons: [
        { src: `${base}/icons/icon-192.png`, sizes: '192x192', type: 'image/png', purpose: 'any' },
        {
          src: `${base}/icons/icon-512.png`,
          sizes: '512x512',
          type: 'image/png',
          purpose: 'any maskable',
        },
      ],
    }),
    { headers: { 'Content-Type': 'application/manifest+json; charset=utf-8' } }
  );
