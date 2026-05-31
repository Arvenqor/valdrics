export type RevealParams = {
	threshold?: number;
	delay?: number;
};

export function reveal(node: Element, { threshold = 0.12, delay = 0 }: RevealParams = {}) {
	node.classList.add('v-hidden');
	const observer = new IntersectionObserver(
		([entry]) => {
			if (entry.isIntersecting) {
				setTimeout(() => node.classList.add('v-visible'), delay);
				observer.disconnect();
			}
		},
		{ threshold, rootMargin: '0px 0px -32px 0px' }
	);
	observer.observe(node);
	return { destroy: () => observer.disconnect() };
}
