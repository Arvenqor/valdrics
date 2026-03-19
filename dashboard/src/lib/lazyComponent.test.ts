import { describe, expect, it, vi } from 'vitest';
import type { Component } from 'svelte';

import { createLazyComponent } from './lazyComponent';

describe('createLazyComponent', () => {
	it('memoizes the first successful loader promise', async () => {
		const module = {
			default: {} as Component<Record<string, unknown>>
		};
		const loader = vi.fn().mockResolvedValue(module);
		const load = createLazyComponent(loader);

		const first = load();
		const second = load();

		expect(first).toBe(second);
		await expect(first).resolves.toBe(module);
		expect(loader).toHaveBeenCalledTimes(1);
	});

	it('retries after a failed lazy import', async () => {
		const error = new Error('chunk failed');
		const module = {
			default: {} as Component<Record<string, unknown>>
		};
		const loader = vi.fn().mockRejectedValueOnce(error).mockResolvedValueOnce(module);
		const load = createLazyComponent(loader);

		await expect(load()).rejects.toThrow('chunk failed');
		await expect(load()).resolves.toBe(module);
		expect(loader).toHaveBeenCalledTimes(2);
	});
});
