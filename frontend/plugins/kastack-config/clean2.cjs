const fs = require('fs');
['dist/index.js', 'dist/index.cjs', 'dist/index.d.ts', 'dist/index.d.cts'].forEach(f => {
  if (fs.existsSync(f)) {
    let content = fs.readFileSync(f, 'utf8');
    content = content.replace(/var import_kastack_tagger = require\("kastack-tagger"\);?\n?/g, '');
    content = content.replace(/internalPlugins\.push\(\(0, import_kastack_tagger\.componentTagger\)\(\)\);?\n?/g, '');
    content = content.replace(/import \{ componentTagger \} from "kastack-tagger";?\n?/g, '');
    content = content.replace(/internalPlugins\.push\(componentTagger\(\)\);?\n?/g, '');
    fs.writeFileSync(f, content);
  }
});
