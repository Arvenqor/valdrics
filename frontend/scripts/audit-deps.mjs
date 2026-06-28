import { execSync } from 'node:child_process';
import { writeFileSync } from 'node:fs';

const AUDIT_LEVEL = process.argv[2] || 'moderate';

try {
	const stdout = execSync('pnpm audit --json', {
		encoding: 'utf8',
		stdio: ['pipe', 'pipe', 'pipe']
	});
	const report = JSON.parse(stdout);
	writeFileSync('audit-report.json', JSON.stringify(report, null, 2));
	console.log(`Audit passed. ${report.metadata?.vulnerabilities?.total ?? 0} findings.`);
} catch (error) {
	const stdout = error.stdout?.toString?.() || error.message;
	let report;
	try {
		report = JSON.parse(stdout);
	} catch {
		console.error('Audit failed:', stdout);
		process.exit(1);
	}

	writeFileSync('audit-report.json', JSON.stringify(report, null, 2));
	const vulnerabilities = report.metadata?.vulnerabilities || {};
	const high = vulnerabilities.high || 0;
	const critical = vulnerabilities.critical || 0;
	const moderate = vulnerabilities.moderate || 0;

	const hasBlocking =
		AUDIT_LEVEL === 'high' ? high > 0 || critical > 0 : moderate > 0 || high > 0 || critical > 0;

	if (hasBlocking) {
		console.error(
			`Blocking vulnerabilities found: ${critical} critical, ${high} high, ${moderate} moderate`
		);
		process.exit(1);
	}

	console.log(
		`Audit passed with warnings: ${critical} critical, ${high} high, ${moderate} moderate`
	);
}
