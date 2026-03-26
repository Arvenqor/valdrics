type ValidationIssue = {
	message?: string;
	path?: PropertyKey[];
};

export function isValidationError(error: unknown): error is { issues: ValidationIssue[] } {
	return (
		typeof error === 'object' &&
		error !== null &&
		Array.isArray((error as { issues?: unknown }).issues)
	);
}

export function formatValidationIssues(error: unknown, includePath = false): string {
	if (!isValidationError(error)) {
		return error instanceof Error ? error.message : 'Invalid input';
	}

	return error.issues
		.map((issue) => {
			const message =
				typeof issue.message === 'string' && issue.message.trim() ? issue.message : 'Invalid input';
			if (!includePath || !Array.isArray(issue.path) || issue.path.length === 0) {
				return message;
			}
			return `${issue.path.join('.')}: ${message}`;
		})
		.join(', ');
}
