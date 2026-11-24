// astro-reading-theme: shared integration for reading-log sites.
// Usage (astro.config.mjs):
//   import readingTheme from 'astro-reading-theme';
//   export default defineConfig({ integrations: [readingTheme({ name: 'Readar', ... })] });
import { fileURLToPath } from 'node:url';

/**
 * @typedef {Object} ThemeConfig
 * @property {string} name                 Site name (wordmark, <title> suffix, manifest, RSS)
 * @property {string} [lang]               <html lang>, default 'en'
 * @property {string} [description]        Home page meta description
 * @property {string} [tagline]            Footer text after the site name
 * @property {string} [rssDescription]     RSS channel description
 * @property {string} [manifestDescription] PWA manifest description
 * @property {{label:string, href:string}[]} [nav]  Header links, hrefs relative to base (e.g. '/about/')
 * @property {{label:string, href:string}} [footerLink]
 * @property {{stats?:boolean, browse?:boolean}} [features]  stats page; author/category/domain pages
 */

/** @param {ThemeConfig} user */
export function resolveConfig(user) {
  if (!user?.name) throw new Error('[astro-reading-theme] `name` is required');
  return {
    lang: 'en',
    description: '',
    tagline: 'every entry links back to its source',
    rssDescription: user.description ?? user.name,
    manifestDescription: user.description ?? user.name,
    nav: [{ label: 'About', href: '/about/' }],
    footerLink: { label: 'Archive', href: '/' },
    ...user,
    features: { stats: false, browse: true, ...(user.features ?? {}) },
  };
}

const VIRTUAL = 'virtual:astro-reading-theme/config';

/** @param {ThemeConfig} user */
export default function readingTheme(user) {
  const config = resolveConfig(user);
  const page = (p) => fileURLToPath(new URL(`./src/pages/${p}`, import.meta.url));
  return {
    name: 'astro-reading-theme',
    hooks: {
      'astro:config:setup': ({ injectRoute, updateConfig }) => {
        updateConfig({
          vite: {
            plugins: [
              {
                name: 'astro-reading-theme-config',
                resolveId: (id) => (id === VIRTUAL ? '\0' + VIRTUAL : null),
                load: (id) => (id === '\0' + VIRTUAL ? `export default ${JSON.stringify(config)};` : null),
              },
            ],
          },
        });
        const routes = [
          ['/[...page]', '[...page].astro'],
          ['/[...slug]', '[...slug].astro'],
          ['/offline', 'offline.astro'],
          ['/manifest.webmanifest', 'manifest.webmanifest.ts'],
          ['/offline-manifest.json', 'offline-manifest.json.ts'],
          ['/rss.xml', 'rss.xml.js'],
        ];
        if (config.features.stats) routes.push(['/stats', 'stats.astro']);
        if (config.features.browse) {
          routes.push(
            ['/category/[category]/[...page]', 'category/[category]/[...page].astro'],
            ['/author/[author]/[...page]', 'author/[author]/[...page].astro'],
            ['/domain/[domain]/[...page]', 'domain/[domain]/[...page].astro']
          );
        }
        for (const [pattern, file] of routes) injectRoute({ pattern, entrypoint: page(file) });
      },
    },
  };
}
