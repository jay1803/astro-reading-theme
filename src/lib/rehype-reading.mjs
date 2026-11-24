// Rehype plugin injected by the theme integration (runs after the site's own plugins).
//
// 1. A bold run that opens a paragraph or list item ("**Label**：text") is a label, not
//    emphasis. It gets class "lead-in" so CSS can keep it plain bold while inline bold
//    phrases get the highlighter mark.
// 2. Tables are wrapped in <div class="table-wrap"> so wide tables scroll sideways on
//    phones instead of overflowing the page.

function firstMeaningfulChild(node) {
  for (const child of node.children ?? []) {
    if (child.type === 'text' && !child.value.trim()) continue;
    return child;
  }
  return null;
}

function addClass(node, name) {
  const props = (node.properties ??= {});
  const current = props.className;
  const list = Array.isArray(current) ? current : current ? [String(current)] : [];
  if (!list.includes(name)) props.className = [...list, name];
}

function textOf(node) {
  if (node.type === 'text') return node.value;
  return (node.children ?? []).map(textOf).join('');
}

function walk(node) {
  if (!node || !Array.isArray(node.children)) return;
  // A short single-token cell ("Qwen2.5-32B", "26.85%") should not break at its hyphen.
  if (node.type === 'element' && (node.tagName === 'td' || node.tagName === 'th')) {
    const text = textOf(node).trim();
    if (text && text.length <= 24 && !/\s/.test(text)) addClass(node, 'nowrap');
  }
  for (let i = 0; i < node.children.length; i++) {
    const child = node.children[i];
    if (child.type === 'element' && child.tagName === 'table') {
      node.children[i] = {
        type: 'element',
        tagName: 'div',
        properties: { className: ['table-wrap'] },
        children: [child],
      };
    }
    walk(child);
  }
  if (node.type === 'element' && (node.tagName === 'p' || node.tagName === 'li')) {
    const first = firstMeaningfulChild(node);
    if (first?.type === 'element' && (first.tagName === 'strong' || first.tagName === 'b')) {
      addClass(first, 'lead-in');
    }
  }
}

export default function rehypeReading() {
  return (tree) => {
    walk(tree);
  };
}
