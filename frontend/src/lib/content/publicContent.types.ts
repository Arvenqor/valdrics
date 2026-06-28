export type PublicContentKind = 'docs' | 'resources' | 'insights' | 'proof';

type PublicContentAudience =
	'engineering' | 'finance' | 'platform' | 'security' | 'procurement' | 'executive';

type PublicContentStage = 'learn' | 'evaluate' | 'validate';

interface PublicContentLink {
	label: string;
	href: string;
}

interface PublicContentSectionInput {
	title: string;
	body: string[];
	bullets?: string[];
}

interface PublicContentSection extends Omit<PublicContentSectionInput, 'bullets'> {
	bullets: string[];
}

interface PublicContentRelatedEntry {
	kind: PublicContentKind;
	slug: string;
}

export interface PublicContentEntryInput {
	kind: PublicContentKind;
	slug: string;
	title: string;
	summary: string;
	kicker: string;
	seoTitle: string;
	seoDescription: string;
	updatedAt: string;
	stage: PublicContentStage;
	readingMinutes: number;
	audiences: PublicContentAudience[];
	primaryCta: PublicContentLink;
	secondaryCta?: PublicContentLink;
	downloads?: PublicContentLink[];
	sections: PublicContentSectionInput[];
	related?: PublicContentRelatedEntry[];
}

export interface PublicContentEntry extends Omit<
	PublicContentEntryInput,
	'downloads' | 'related' | 'sections'
> {
	downloads: PublicContentLink[];
	sections: PublicContentSection[];
	related: PublicContentRelatedEntry[];
}
