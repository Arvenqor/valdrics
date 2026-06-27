import { describe, it, expect, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/svelte';
import DateRangePicker from './DateRangePicker.svelte';

describe('DateRangePicker Component', () => {
	afterEach(() => {
		cleanup();
	});

	it('mounts with the correct active preset', () => {
		render(DateRangePicker, { value: '30d' });
		const activeBtn = screen.getByText('30 Days');
		expect(activeBtn).toBeTruthy();
		expect(activeBtn.className).toContain('active');
	});

	it('switches preset when clicking a different preset', async () => {
		render(DateRangePicker, { value: '7d' });
		const ninetyDaysBtn = screen.getByText('90 Days');
		await fireEvent.click(ninetyDaysBtn);
		expect(ninetyDaysBtn.className).toContain('active');
	});

	it('disables apply when a custom date field is cleared', async () => {
		render(DateRangePicker, { value: '30d' });
		const customBtn = screen.getByText(/Custom/);
		await fireEvent.click(customBtn);

		const applyBtn = screen.getByText('Apply') as HTMLButtonElement;
		expect(applyBtn.disabled).toBe(false);

		const toInput = screen.getByLabelText('To') as HTMLInputElement;
		await fireEvent.input(toInput, { target: { value: '' } });
		expect(applyBtn.disabled).toBe(true);
	});
});
