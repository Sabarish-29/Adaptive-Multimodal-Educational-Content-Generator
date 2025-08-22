import * as Y from 'yjs';

// Singleton Yjs document for authoring (could namespace later)
const ydoc = new Y.Doc();
export const yText = ydoc.getText('author');
export function getDoc(){ return ydoc; }
