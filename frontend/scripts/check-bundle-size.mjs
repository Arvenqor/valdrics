import fs from 'node:fs/promises';
import path from 'node:path';

const projectRoot = process.cwd();
const IMMUTABLE_DIR_CANDIDATES = [
	path.join(projectRoot, 'build', 'client', '_app', 'immutable'),
	path.join(projectRoot, '.svelte-kit', 'output', 'client', '_app', 'immutable')
];

const MAX_CHUNK_KB = Number(process.env.BUNDLE_MAX_CHUNK_KB ?? '350');
const MAX_TOTAL_KB = Number(process.env.BUNDLE_MAX_TOTAL_KB ?? '4000');
const MAX_CSS_CHUNK_KB = Number(process.env.BUNDLE_MAX_CSS_CHUNK_KB ?? '120');
const MAX_CSS_TOTAL_KB = Number(process.env.BUNDLE_MAX_CSS_TOTAL_KB ?? '600');

const MAX_CHUNK_BYTES = Math.max(1, MAX_CHUNK_KB) * 1024;
const MAX_TOTAL_BYTES = Math.max(1, MAX_TOTAL_KB) * 1024;
const MAX_CSS_CHUNK_BYTES = Math.max(1, MAX_CSS_CHUNK_KB) * 1024;
const MAX_CSS_TOTAL_BYTES = Math.max(1, MAX_CSS_TOTAL_KB) * 1024;

async function listFiles(dir) {
	const entries = await fs.readdir(dir, { withFileTypes: true });
	const files = [];
	for (const entry of entries) {
		const fullPath = path.join(dir, entry.name);
		if (entry.isDirectory()) {
			files.push(...(await listFiles(fullPath)));
			continue;
		}
		files.push(fullPath);
	}
	return files;
}

function formatKb(bytes) {
	return `${(bytes / 1024).toFixed(2)} KB`;
}

async function main() {
	const existingCandidates = [];
	for (const candidate of IMMUTABLE_DIR_CANDIDATES) {
		try {
			const stat = await fs.stat(candidate);
			existingCandidates.push({ candidate, mtimeMs: stat.mtimeMs });
		} catch {
			// Try next candidate path.
		}
	}

	const immutableDir =
		existingCandidates.sort((a, b) => b.mtimeMs - a.mtimeMs)[0]?.candidate ?? null;

	if (!immutableDir) {
		console.error(
			`Bundle directory not found. Checked:\n` +
				IMMUTABLE_DIR_CANDIDATES.map((candidate) => `- ${candidate}`).join('\n') +
				`\nRun 'pnpm -C frontend build' before checking bundle budgets.`
		);
		process.exit(2);
	}

	const allFiles = await listFiles(immutableDir);
	const jsFiles = allFiles
		.filter((file) => file.endsWith('.js'))
		.filter((file) => !file.endsWith('.map.js'));
	const cssFiles = allFiles
		.filter((file) => file.endsWith('.css'))
		.filter((file) => !file.endsWith('.map.css'));

	const jsSizes = await Promise.all(
		jsFiles.map(async (file) => {
			const stat = await fs.stat(file);
			return { file, bytes: stat.size };
		})
	);
	const cssSizes = await Promise.all(
		cssFiles.map(async (file) => {
			const stat = await fs.stat(file);
			return { file, bytes: stat.size };
		})
	);

	jsSizes.sort((a, b) => b.bytes - a.bytes);
	cssSizes.sort((a, b) => b.bytes - a.bytes);

	const totalJs = jsSizes.reduce((sum, item) => sum + item.bytes, 0);
	const totalCss = cssSizes.reduce((sum, item) => sum + item.bytes, 0);
	const largestJs = jsSizes[0];
	const largestCss = cssSizes[0];

	const failures = [];
	if (largestJs && largestJs.bytes > MAX_CHUNK_BYTES) {
		failures.push(
			`Largest JS chunk exceeds budget: ${formatKb(largestJs.bytes)} > ${MAX_CHUNK_KB} KB\n` +
				`  ${path.relative(projectRoot, largestJs.file)}`
		);
	}

	if (totalJs > MAX_TOTAL_BYTES) {
		failures.push(
			`Total client JS exceeds budget: ${formatKb(totalJs)} > ${MAX_TOTAL_KB} KB\n` +
				`  (sum of all .js files under build/client/_app/immutable)`
		);
	}

	if (largestCss && largestCss.bytes > MAX_CSS_CHUNK_BYTES) {
		failures.push(
			`Largest CSS chunk exceeds budget: ${formatKb(largestCss.bytes)} > ${MAX_CSS_CHUNK_KB} KB\n` +
				`  ${path.relative(projectRoot, largestCss.file)}`
		);
	}

	if (totalCss > MAX_CSS_TOTAL_BYTES) {
		failures.push(
			`Total client CSS exceeds budget: ${formatKb(totalCss)} > ${MAX_CSS_TOTAL_KB} KB\n` +
				`  (sum of all .css files under build/client/_app/immutable)`
		);
	}

	if (failures.length > 0) {
		console.error(failures.join('\n\n'));
		console.error('\nTop JS chunks:');
		for (const item of jsSizes.slice(0, 10)) {
			console.error(
				`- ${formatKb(item.bytes).padStart(10)}  ${path.relative(projectRoot, item.file)}`
			);
		}
		console.error('\nTop CSS chunks:');
		for (const item of cssSizes.slice(0, 10)) {
			console.error(
				`- ${formatKb(item.bytes).padStart(10)}  ${path.relative(projectRoot, item.file)}`
			);
		}
		process.exit(1);
	}

	console.log(
		`Bundle budgets OK: ` +
			`largest-js=${largestJs ? formatKb(largestJs.bytes) : 'n/a'} (<= ${MAX_CHUNK_KB} KB), ` +
			`total-js=${formatKb(totalJs)} (<= ${MAX_TOTAL_KB} KB), ` +
			`largest-css=${largestCss ? formatKb(largestCss.bytes) : 'n/a'} (<= ${MAX_CSS_CHUNK_KB} KB), ` +
			`total-css=${formatKb(totalCss)} (<= ${MAX_CSS_TOTAL_KB} KB)`
	);
}

await main();
