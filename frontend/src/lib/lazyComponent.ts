import type { Component } from 'svelte';

export type LazyComponentModule<Props extends object = Record<string, unknown>> = {
	default: Component<Props>;
};

export function createLazyComponent<Props extends object>(
	loader: () => Promise<LazyComponentModule<Props>>
): () => Promise<LazyComponentModule<Props>> {
	let promise: Promise<LazyComponentModule<Props>> | null = null;

	return () => {
		if (!promise) {
			promise = loader().catch((error) => {
				promise = null;
				throw error;
			});
		}
		return promise;
	};
}
