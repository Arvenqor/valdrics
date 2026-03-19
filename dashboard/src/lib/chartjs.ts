let chartJsPromise: Promise<Pick<typeof import('chart.js'), 'Chart'>> | null = null;

/**
 * Lazy-load only the Chart.js primitives required by the dashboard charts.
 *
 * Keeping the loader behind a local runtime module lets Vite tree-shake the
 * unused Chart.js controllers out of the finance route chunk.
 */
export async function loadChartJs(): Promise<Pick<typeof import('chart.js'), 'Chart'>> {
	if (!chartJsPromise) {
		chartJsPromise = import('./chartjsRuntime').then((module) => module.getChartJs());
	}

	return chartJsPromise;
}
