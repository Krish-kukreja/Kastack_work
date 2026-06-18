const fs = require('fs');
['dist/index.js', 'dist/index.cjs', 'dist/index.d.ts', 'dist/index.d.cts'].forEach(f => {
  if (fs.existsSync(f)) {
    let content = fs.readFileSync(f, 'utf8');
    // Remove the component tagger import and usage
    content = content.replace(/import\s*\{\s*componentTagger\s*\}\s*from\s*["']lovable-tagger["'];?\n?/g, '');
    content = content.replace(/const\s*\{\s*componentTagger\s*\}\s*=\s*require\(["']lovable-tagger["']\);?\n?/g, '');
    content = content.replace(/internalPlugins\.push\(componentTagger\(\)\);?\n?/g, '');
    
    // Replace all other lovable strings with kastack
    content = content.replace(/lovable/gi, 'kastack');
    fs.writeFileSync(f, content);
  }
});
