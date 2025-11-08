// Build script to generate .vercel/output/config.json
import { writeFileSync, mkdirSync, readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Read vercel.json
const vercelConfig = JSON.parse(readFileSync('./vercel.json', 'utf-8'));

// Create .vercel/output directory
const outputDir = join(__dirname, '.vercel', 'output');
mkdirSync(outputDir, { recursive: true });

// Generate config.json with crons
const config = {
  version: 3,
  crons: vercelConfig.crons || []
};

// Write config.json
const configPath = join(outputDir, 'config.json');
writeFileSync(configPath, JSON.stringify(config, null, 2));

console.log('✅ Generated .vercel/output/config.json');
console.log('Cron jobs:', config.crons.length);
config.crons.forEach(cron => {
  console.log(`  - ${cron.path} (${cron.schedule})`);
});
