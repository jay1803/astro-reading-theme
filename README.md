# astro-reading-theme

Shared Astro theme for personal reading-log sites (`reading`, `oddly`, `agent-learning`, ...).
Fix or improve the front end **once here**, then bump the dependency in each site.

## What it provides

- `BaseLayout`, `PostEntry`, `InfiniteFeed`, `ListenButton` components and `lib/*` helpers
- An Astro integration that injects the standard routes: home/pagination, post pages,
  offline page + manifest, PWA manifest, RSS, and optionally stats and author/category/domain browsing
- Per-site differences (name, language, nav, footer, descriptions) via config instead of forks

Sites keep only: `src/content/`, `src/content.config.ts`, `src/pages/about.astro`, `public/`, `astro.config.mjs`.

## Use in a site

```bash
npm i github:jay1803/astro-reading-theme#v0.3.1
```

```js
// astro.config.mjs
import { defineConfig } from 'astro/config';
import remarkGfm from 'remark-gfm';
import readingTheme from 'astro-reading-theme';
import rehypePangu from 'astro-reading-theme/rehype-pangu';

export default defineConfig({
  site: 'https://example.maxoxo.me',
  integrations: [
    readingTheme({
      name: 'Example',                   // also the big home page title, one word per line
      lang: 'en',                        // <html lang>; 'zh-CN' etc. switches UI labels to Chinese
      description: 'Home page description',
      dek: ['Line one.', 'Line two.'],   // lines under the home page title; defaults to description
      tagline: 'every entry links back to its source', // footer
      nav: [{ label: 'About', href: '/about/' }],
      footerLink: { label: 'Archive', href: '/' },
      features: { stats: false, category: true, author: true, domain: true, listen: true },
      overrides: {}, // see below
    }),
  ],
  markdown: { gfm: false, remarkPlugins: [[remarkGfm, { singleTilde: false }]], rehypePlugins: [rehypePangu] },
  build: { inlineStylesheets: 'always' },
});
```

In a site's own pages (e.g. `about.astro`):
`import BaseLayout from 'astro-reading-theme/layouts/BaseLayout.astro';`

A site-owned file in `src/pages/` wins over an injected route with the same pattern.

## Overriding theme files

When a site needs different markup (e.g. `oddly`'s `PostEntry` and post page), keep its own copy
under `src/overrides/` and register it. Keys are paths relative to the theme's `src/`, values are
paths relative to the site root:

```js
readingTheme({
  name: 'oddly',
  overrides: {
    'components/PostEntry.astro': 'src/overrides/components/PostEntry.astro',
    'pages/[...slug].astro': 'src/overrides/pages/[...slug].astro',
    'lib/feed.ts': 'src/lib/feed.ts',
  },
});
```

This replaces both injected routes and the theme's own relative imports (so `InfiniteFeed`
picks up the site's `PostEntry`). Inside override files import theme code via the package, e.g.
`import { base } from 'astro-reading-theme/lib/base.ts'`. A wrong key fails the build immediately.
Keep overrides to a minimum: each one is a copy that will not receive theme fixes.

## Releasing a change

1. Edit here, `git tag vX.Y.Z`, push with tags.
2. In each site: `npm i github:jay1803/astro-reading-theme#vX.Y.Z`, build, push.

## Local development against a site

```bash
cd ../astro-reading-theme && npm install
cd ../some-site && npm install --no-save ../astro-reading-theme && npm run dev
```

(`--no-save` keeps the local link out of the site's `package.json`.)

## Sites

| Site | Overrides |
| --- | --- |
| `reading` | none (stats on) |
| `agent-learning` | none (stats on) |
| `oddly` | PostEntry, post page, home, category page, offline page, `lib/feed.ts` |

## Changelog

- 0.3.0: new default design (monochrome, sans-serif, left-aligned).
  - Feed entries get a large entry number, a sticky side rail on wide screens (source, author, length,
    saved date, section list, source link) and a second top-bar row that tracks the entry being read
    and opens an index of loaded entries. Post pages number their `##` sections and get the same rail.
  - Stats page: summary tiles, domain/author breakdown with share and latest title.
  - New config: `dek`. UI labels follow `lang` (`zh*` → Chinese, otherwise English).
  - The integration now appends `rehype-reading` to the site's rehype plugins: it marks bold runs that
    open a line as labels (`strong.lead-in`, plain bold) so inline bold gets a highlight, keeps short
    single-token table cells on one line, and wraps tables for horizontal scroll.
  - No web fonts: Inter if installed, else the system UI font; Chinese uses PingFang / YaHei / Noto Sans.
  - Removed the scroll-progress bar; the refresh button is an icon and its status is a transient toast.
  - Upgrading a site: the old CSS variable names (`--paper`, `--accent`, `--ink-soft`, `--font-mono`, …)
    still resolve, but overrides of `PostEntry`, `[...page]` or `[...slug]` keep the 0.2 markup and
    should be compared against the new files. Sites that cache pages in a service worker should bump
    the page cache name so readers get the new HTML. Locally, delete `node_modules/.astro` once so
    Astro re-renders markdown with the new plugin.
- 0.2.1: deterministic ordering (date ties broken by id; stats ties by name) via `lib/sort.ts`.
- 0.2.0: `overrides` option; `features.browse` split into `category`/`author`/`domain`; `features.listen`;
  offline manifest follows `nav` instead of hard-coding `/stats/`.
- 0.1.0: initial extraction.
