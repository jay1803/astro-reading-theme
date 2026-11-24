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
npm i github:jay1803/astro-reading-theme#v0.1.0
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
      name: 'Example',
      lang: 'en',                        // <html lang>
      description: 'Home page description',
      tagline: 'every entry links back to its source', // footer
      nav: [{ label: 'About', href: '/about/' }],
      footerLink: { label: 'Archive', href: '/' },
      features: { stats: false, browse: true },
    }),
  ],
  markdown: { gfm: false, remarkPlugins: [[remarkGfm, { singleTilde: false }]], rehypePlugins: [rehypePangu] },
  build: { inlineStylesheets: 'always' },
});
```

In a site's own pages (e.g. `about.astro`):
`import BaseLayout from 'astro-reading-theme/layouts/BaseLayout.astro';`

A site-owned file in `src/pages/` wins over an injected route with the same pattern.

## Releasing a change

1. Edit here, `git tag vX.Y.Z`, push with tags.
2. In each site: `npm i github:jay1803/astro-reading-theme#vX.Y.Z`, build, push.

## Local development against a site

```bash
cd ../astro-reading-theme && npm install
cd ../some-site && npm install --no-save ../astro-reading-theme && npm run dev
```

(`--no-save` keeps the local link out of the site's `package.json`.)

## Status

Pilot: `agent-learning`. Not yet migrated: `reading` (needs only config), `oddly`
(custom `PostEntry`, category tabs, `ask-chatgpt` — needs component overrides).
