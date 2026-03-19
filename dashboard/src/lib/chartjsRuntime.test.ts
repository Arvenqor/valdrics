import { beforeEach, describe, expect, it, vi } from 'vitest';

const chartJsMock = vi.hoisted(() => ({
	Chart: {
		register: vi.fn()
	},
	ArcElement: Symbol('ArcElement'),
	CategoryScale: Symbol('CategoryScale'),
	DoughnutController: Symbol('DoughnutController'),
	Filler: Symbol('Filler'),
	Legend: Symbol('Legend'),
	LineController: Symbol('LineController'),
	LineElement: Symbol('LineElement'),
	LinearScale: Symbol('LinearScale'),
	PointElement: Symbol('PointElement'),
	Tooltip: Symbol('Tooltip')
}));

vi.mock('chart.js', () => chartJsMock);

describe('getChartJs', () => {
	beforeEach(() => {
		vi.resetModules();
		chartJsMock.Chart.register.mockReset();
	});

	it('registers only the chart primitives used by dashboard visualizations once', async () => {
		const { getChartJs } = await import('./chartjsRuntime');

		const first = getChartJs();
		const second = getChartJs();

		expect(first.Chart).toBe(chartJsMock.Chart);
		expect(second.Chart).toBe(chartJsMock.Chart);
		expect(chartJsMock.Chart.register).toHaveBeenCalledTimes(1);
		expect(chartJsMock.Chart.register).toHaveBeenCalledWith(
			chartJsMock.ArcElement,
			chartJsMock.CategoryScale,
			chartJsMock.DoughnutController,
			chartJsMock.Filler,
			chartJsMock.Legend,
			chartJsMock.LineController,
			chartJsMock.LineElement,
			chartJsMock.LinearScale,
			chartJsMock.PointElement,
			chartJsMock.Tooltip
		);
	});
});
