import * as z from 'zod/mini';
import { formatValidationIssues, isValidationError } from './formatValidationIssues';

let configured = false;

function ensureEnglishLocale(): void {
	if (configured) return;
	z.config(z.locales.en());
	configured = true;
}

ensureEnglishLocale();

export { z };
export { formatValidationIssues, isValidationError };
