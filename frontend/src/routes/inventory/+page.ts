import type { PageLoad } from './$types';
import type { InventoryStatusFilter, InventoryTypeFilter } from './inventoryTypes';

const TYPE_FILTERS = new Set<InventoryTypeFilter>(['all', 'cloud', 'software', 'service']);
const STATUS_FILTERS = new Set<InventoryStatusFilter>([
	'all',
	'active',
	'pending',
	'error',
	'idle',
	'shadow',
	'expiring'
]);

function readType(value: string | null): InventoryTypeFilter {
	if (TYPE_FILTERS.has(value as InventoryTypeFilter)) {
		return value as InventoryTypeFilter;
	}
	return 'all';
}

function readStatus(value: string | null): InventoryStatusFilter {
	if (STATUS_FILTERS.has(value as InventoryStatusFilter)) {
		return value as InventoryStatusFilter;
	}
	return 'all';
}

function readPage(value: string | null): number {
	const parsed = Number(value);
	if (!Number.isInteger(parsed) || parsed < 1) return 1;
	return parsed;
}

export const load: PageLoad = async ({ parent, url }) => {
	await parent();
	return {
		inventoryType: readType(url.searchParams.get('type')),
		inventoryStatus: readStatus(url.searchParams.get('status')),
		inventorySearch: url.searchParams.get('q')?.slice(0, 120) ?? '',
		inventoryPage: readPage(url.searchParams.get('page'))
	};
};
