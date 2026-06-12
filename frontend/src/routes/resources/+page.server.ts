import type { PageServerLoad } from './$types';
import { listPublicContent, mustGetPublicContentEntry } from '$lib/content/publicContent';

export const load: PageServerLoad = () => {
	const resources = listPublicContent('resources');

	// Helper to safely resolve entries to prevent total page failure if one is missing
	const getSafeEntries = (ids: string[]) =>
		ids.map((id) => mustGetPublicContentEntry('resources', id));

	return {
		resources,
		guidedPaths: [
			{
				kicker: 'Internal alignment',
				title: 'Make the business case without a long deck rewrite',
				copy: 'Use concise assets when finance, leadership, or procurement needs the short version before the deeper review surfaces.',
				entries: getSafeEntries([
					'executive-one-pager',
					'roi-assumptions',
					'enterprise-governance-overview'
				])
			},
			{
				kicker: 'Operating rhythm',
				title: 'Give the team a repeatable review loop',
				copy: 'Use these assets when you want one cost-review ritual, clearer owner routing, and a practical GreenOps conversation.',
				entries: getSafeEntries([
					'cloud-waste-review-checklist',
					'greenops-decision-framework',
					'saas-license-governance-starter-pack'
				])
			},
			{
				kicker: 'Buyer diligence',
				title: 'Move into procurement and security without losing the thread',
				copy: 'These are the assets that help the product story survive security, procurement, and rollout conversations.',
				entries: getSafeEntries([
					'enterprise-governance-overview',
					'saas-license-governance-starter-pack',
					'roi-assumptions'
				])
			}
		],
		stageColumns: [
			{
				label: 'Learn',
				title: 'Run the first review with less noise',
				copy: 'Operational guides for teams that need a practical first loop.',
				entries: resources.filter((resource) => resource.stage === 'learn')
			},
			{
				label: 'Evaluate',
				title: 'Prepare the buying and rollout conversation',
				copy: 'Assets for leadership, procurement, and rollout planning.',
				entries: resources.filter((resource) => resource.stage === 'evaluate')
			},
			{
				label: 'Validate',
				title: 'Pressure-test the modeled case',
				copy: 'Artifacts that support a deeper diligence or planning review.',
				entries: resources.filter((resource) => resource.stage === 'validate')
			}
		]
	};
};
