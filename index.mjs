// astro-reading-theme: shared integration for reading-log sites.
// Usage (astro.config.mjs):
//   import readingTheme from 'astro-reading-theme';
//   export default defineConfig({ integrations: [readingTheme({ name: 'Readar', ... })] });
import { fileURLToPath } from 'node:url';
import { realpathSync } from 'node:fs';
import path from 'node:path';
import rehypeReading from './src/lib/rehype-reading.mjs';

/**
 * @typedef {Object} ThemeConfig
 * @property {string} name                 Site name (wordmark, <title> suffix, manifest, RSS)
 * @property {string} [lang]               <html lang>, default 'en'. 'zh*' switches UI labels to Chinese
 *           and the body font stack to CJK-first.
 * @property {string} [description]        Home page meta description
 * @property {string | string[]} [dek]     Lines shown under the home page title; defaults to `description`
 * @property {string} [tagline]            Footer text after the site name
 * @property {string} [rssDescription]     RSS channel description
 * @property {string} [manifestDescription] PWA manifest description
 * @property {{label:string, href:string}[]} [nav]  Header links, hrefs relative to base (e.g. '/about/')
 * @property {{label:string, href:string}} [footerLink]
 * @property {{stats?:boolean, category?:boolean, author?:boolean, domain?:boolean, listen?:boolean, feedback?:boolean}} [features]
 *           stats page; category/author/domain browse pages; ListenButton on post pages;
 *           feedback = owner-only 👍/👎 (needs the site to provide `/api/vote`, see FeedbackButtons.astro)
 * @property {Record<string,string>} [overrides]  Replace theme files with site files. Keys are paths relative to
 *           the theme's `src/` (e.g. 'components/PostEntry.astro', 'pages/[...slug].astro', 'lib/feed.ts'),
 *           values are site paths relative to the project root. Works for injected routes and for
 *           relative imports inside the theme.
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
    overrides: {},
    ...user,
    dek: [user.dek ?? user.description ?? []].flat().filter(Boolean),
    features: { stats: false, category: true, author: true, domain: true, listen: true, feedback: false, ...(user.features ?? {}) },
  };
}

const VIRTUAL = 'virtual:astro-reading-theme/config';

/** @param {ThemeConfig} user */
export default function readingTheme(user) {
  const config = resolveConfig(user);
  const themeSrc = path.join(realpathSync(fileURLToPath(new URL('.', import.meta.url))), 'src');
  return {
    name: 'astro-reading-theme',
    hooks: {
      'astro:config:setup': ({ injectRoute, updateConfig, config: astroConfig }) => {
        const root = fileURLToPath(astroConfig.root);
        const overrides = new Map(
          Object.entries(config.overrides).map(([k, v]) => {
            const abs = path.resolve(root, v);
            // validate early: a typo'd key silently doing nothing is the worst failure mode
            realpathSync(path.join(themeSrc, k));
            realpathSync(abs);
            return [path.join(themeSrc, k), abs];
          })
        );
        const page = (p) => {
          const file = path.join(themeSrc, 'pages', p);
          return overrides.get(file) ?? file;
        };
        const isTheme = (id) => id && id.startsWith(themeSrc + path.sep);
        const stripQuery = (id) => id.split('?')[0];
        updateConfig({
          // Appended after the site's own rehype plugins (Astro concatenates arrays on merge).
          markdown: { rehypePlugins: [rehypeReading] },
          vite: {
            plugins: [
              {
                name: 'astro-reading-theme-config',
                enforce: 'pre',
                resolveId(source, importer) {
                  if (source === VIRTUAL) return '\0' + VIRTUAL;
                  if (overrides.size && importer && source.startsWith('.') && isTheme(stripQuery(importer))) {
                    const target = path.resolve(path.dirname(stripQuery(importer)), source);
                    for (const [file, abs] of overrides) {
                      // imports may omit the extension (e.g. '../lib/base')
                      if (target === file || target === file.replace(/\.[^./\\]+$/, '')) return abs;
                    }
                  }
                  return null;
                },
                load: (id) => (id === '\0' + VIRTUAL ? `export default ${JSON.stringify(config)};` : null),
              },
            ],
          },
        });
        const f = config.features;
        const routes = [
          ['/[...page]', '[...page].astro'],
          ['/[...slug]', '[...slug].astro'],
          ['/offline', 'offline.astro'],
          ['/manifest.webmanifest', 'manifest.webmanifest.ts'],
          ['/offline-manifest.json', 'offline-manifest.json.ts'],
          ['/rss.xml', 'rss.xml.js'],
        ];
        if (f.stats) routes.push(['/stats', 'stats.astro']);
        if (f.category) routes.push(['/category/[category]/[...page]', 'category/[category]/[...page].astro']);
        if (f.author) routes.push(['/author/[author]/[...page]', 'author/[author]/[...page].astro']);
        if (f.domain) routes.push(['/domain/[domain]/[...page]', 'domain/[domain]/[...page].astro']);
        for (const [pattern, file] of routes) injectRoute({ pattern, entrypoint: page(file) });
      },
    },
  };
}
