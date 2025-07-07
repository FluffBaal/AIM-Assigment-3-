#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Fix paths in index.html after build
const indexPath = path.join(__dirname, '../dist/index.html');

if (fs.existsSync(indexPath)) {
  let content = fs.readFileSync(indexPath, 'utf8');
  
  // Replace relative paths with absolute paths
  content = content.replace(/href="\.\/assets\//g, 'href="/assets/');
  content = content.replace(/src="\.\/assets\//g, 'src="/assets/');
  content = content.replace(/href="\.\/vite\.svg"/g, 'href="/vite.svg"');
  
  fs.writeFileSync(indexPath, content);
  console.log('Fixed asset paths in index.html');
} else {
  console.error('index.html not found in dist directory');
}