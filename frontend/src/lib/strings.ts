export function trimToUndefined(input: string | null | undefined): string | undefined {
	const trimmed = (input || '').trim();
	return trimmed ? trimmed : undefined;
}

export function truncate(input: string | null | undefined, maxLength: number): string | undefined {
	const trimmed = (input || '').trim();
	if (!trimmed) return undefined;
	return trimmed.slice(0, maxLength);
}

export function lowercaseEnumToken(input: string | null | undefined): string {
	return (input || '').trim().toLowerCase();
}
