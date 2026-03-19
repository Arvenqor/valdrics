import {
	ArcElement,
	CategoryScale,
	Chart,
	DoughnutController,
	Filler,
	Legend,
	LineController,
	LineElement,
	LinearScale,
	PointElement,
	Tooltip
} from 'chart.js';

let registered = false;

export function getChartJs(): Pick<typeof import('chart.js'), 'Chart'> {
	if (!registered) {
		Chart.register(
			ArcElement,
			CategoryScale,
			DoughnutController,
			Filler,
			Legend,
			LineController,
			LineElement,
			LinearScale,
			PointElement,
			Tooltip
		);
		registered = true;
	}

	return { Chart };
}
