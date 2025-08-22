// Markdown parsing worker: receives { id, body } and returns { id, html }
import { marked } from 'marked';

self.onmessage = (e: MessageEvent) => {
  try {
    const { id, body } = e.data || {};
    const html = marked.parse(body || '') as string;
    // @ts-ignore
    self.postMessage({ id, html });
  } catch (err) {
    // @ts-ignore
    self.postMessage({ id: e.data?.id, html: '<p>Error parsing</p>' });
  }
};
