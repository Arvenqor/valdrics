import type { PageServerLoad } from './$types';
import {
	listRelatedPublicContent,
	getPublicContentEntry,
	type PublicContentKind
} from '$lib/content/publicContent';
import { error } from '@sveltejs/kit';

export const load: PageServerLoad = ({ params }) => {
	const kinds: PublicContentKind[] = ['resources', 'insights', 'proof'];
	let entry;
	for (const kind of kinds) {
		entry = getPublicContentEntry(kind, params.slug);
		if (entry) break;
	}
	if (!entry) {
		throw error(404, `Unknown resource: ${params.slug}`);
	}
	return {
		entry,
		relatedEntries: listRelatedPublicContent(entry)
	};
};
