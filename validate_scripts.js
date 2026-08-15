const fs = require('fs');
const html = fs.readFileSync('index.html', 'utf8');
const scriptBlocks = [];
const regex = /<script\b[^>]*>([\s\S]*?)<\/script>/gi;
let match;
while ((match = regex.exec(html)) !== null) {
  const fullTag = match[0];
  if (!/src\s*=/i.test(fullTag)) {
    scriptBlocks.push(match[1]);
  }
}
console.log('Found block count:', scriptBlocks.length);
let success = true;
scriptBlocks.forEach((code, index) => {
  try {
    new Function(code);
    console.log(`Block ${index}: Compilation OK`);
  } catch (err) {
    console.error(`Block ${index} compilation failed:`, err.message);
    success = false;
  }
});
if (!success) {
  process.exit(1);
}
