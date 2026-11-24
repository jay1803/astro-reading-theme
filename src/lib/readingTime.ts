import fs from 'node:fs';
import path from 'node:path';

const CJK_RE = /[一-鿿぀-ヿ가-힯]/g;
const CONTENT_DIR = path.join(process.cwd(), 'src/content/posts');

function stripFrontmatter(raw: string): string {
  const parts = raw.split('---\n');
  return parts.length > 2 ? parts.slice(2).join('---\n') : raw;
}

/** Estimated reading time in whole minutes (at least 1). */
export function readingMinutes(postId: string): number {
  let raw: string;
  try {
    raw = fs.readFileSync(path.join(CONTENT_DIR, `${postId}.md`), 'utf-8');
  } catch {
    return 1;
  }
  const body = stripFrontmatter(raw);
  const cjkCount = (body.match(CJK_RE) || []).length;
  const wordCount = (body.replace(CJK_RE, ' ').match(/\S+/g) || []).length;
  return Math.max(1, Math.round(wordCount / 235 + cjkCount / 400));
}

/** English label kept for site overrides written against 0.2.x. */
export function estimateReadingTime(postId: string): string {
  return `${readingMinutes(postId)} min read`;
}
