import { DEFAULT_PRICING_PLANS } from '$lib/pricing/publicPlans';

export type FaqItem = {
	q: string;
	a: string;
};

export type GovernanceScenario = {
	saving: string;
	quote: string;
	name: string;
	role: string;
	co: string;
	initials: string;
	avatarClass: string;
};

export type TickerItem = {
	before: string;
	strong?: string;
	after?: string;
};

export const FAQS: FaqItem[] = [
	{
		q: 'What is cloud and software spend governance?',
		a: "Governance is the layer of controls that decides which cloud resources and software tools get approved, who owns them, and whether they comply with your organisation's policies — before the spend is committed. Valdrics makes governance automatic: every request triggers a policy check, and every resource has an assigned owner. The result is that waste gets stopped before it reaches the bill, not discovered after."
	},
	{
		q: 'How long does setup take?',
		a: 'Your first governed workflow can start from the free workspace and expand as provider coverage matures. Cloud onboarding uses read-only access where supported, and SaaS or license connectors stay tied to the production connector contracts instead of a one-off professional-services path.'
	},
	{
		q: 'Does Valdrics need write access to my cloud accounts?',
		a: 'Never. Valdrics is entirely read-only. We read your billing and usage data to build the inventory and detect anomalies. All governance actions — approving a resource, cancelling a SaaS subscription, rightsizing an instance — are carried out by your team. Valdrics tells you what to do and tracks that it was done.'
	},
	{
		q: 'How does Valdrics handle both cloud and SaaS in one platform?',
		a: "Most tools pick one or the other. Cloud cost platforms ignore the $40K/year your team spends on SaaS tools nobody uses. SaaS management tools ignore the EC2 instances nobody owns. Valdrics treats every paid resource — whether it's an RDS cluster or a Figma seat — as an asset that needs approval, ownership, and periodic justification. One inventory, one approval queue, one governance layer."
	},
	{
		q: 'What governance policies can Valdrics enforce?',
		a: 'Valdrics supports production-backed guardrails for approval requirements, budget and credit controls, production-safe modes, owner routing, and remediation policy checks. New policy controls should appear in the UI only after the corresponding backend enforcement contract and tests exist.'
	},
	{
		q: 'How does Valdrics measure the return on governance?',
		a: 'Every saving is attributed to the specific governance action that produced it. A denied over-budget request, a reclaimed unused licence, a shadow IT tool cancelled — each is tagged with a dollar amount and a reason. Finance gets a governance ROI report that shows exactly what governance enforcement saved, not just a cost chart with no narrative.'
	},
	{
		q: 'How is Valdrics different from Torii or Zylo?',
		a: "Torii and Zylo are SaaS management tools — they track software licences but don't touch cloud infrastructure, don't run approval workflows before spend is committed, and don't enforce policy rules. Valdrics unifies cloud and SaaS governance in one platform, adds a proactive approval gate, and measures the ROI from governance enforcement. The core difference: Torii tells you what you're spending. Valdrics stops you spending what you shouldn't."
	},
	{
		q: 'How does Valdrics handle security and compliance?',
		a: 'Valdrics is designed for security-sensitive FinOps workflows: read-only cloud access, limited cost and usage metadata, tenant-aware controls, and audit evidence exports. Enterprise customers can request private deployment reviews, DPAs, and security documentation during onboarding.'
	}
];

export const GOVERNANCE_SCENARIOS: GovernanceScenario[] = [
	{
		saving: 'Software renewal gate',
		quote:
			'A team requests another SaaS renewal. Valdrics ties the request to an owner, justification, approval status, and policy history before the invoice becomes a surprise.',
		name: 'SaaS governance',
		role: 'Ownership, DPA, and renewal control',
		co: 'Example workflow',
		initials: 'SG',
		avatarClass: 'tcard__avatar--saas'
	},
	{
		saving: 'Cloud budget guardrail',
		quote:
			'An expensive infrastructure request crosses a team budget threshold. Valdrics routes it for finance review and keeps the policy decision attached to the resource.',
		name: 'Cloud governance',
		role: 'Budget, region, and instance policy checks',
		co: 'Example workflow',
		initials: 'CG',
		avatarClass: 'tcard__avatar--cloud'
	},
	{
		saving: 'Board-ready evidence',
		quote:
			'Every spend-changing decision carries a requester, approver, reason, and timestamp, giving finance and engineering one evidence trail instead of scattered screenshots.',
		name: 'Executive reporting',
		role: 'Traceable governance ROI',
		co: 'Example workflow',
		initials: 'ER',
		avatarClass: 'tcard__avatar--reporting'
	}
];

export const HOW_STEPS = [
	{
		n: '01',
		title: 'Connect your clouds & tools',
		desc: 'Read-only IAM role for AWS, service account for GCP, Azure app registration. OAuth for 100+ SaaS tools. 3–4 minutes per provider.'
	},
	{
		n: '02',
		title: 'Valdrics maps your inventory',
		desc: 'We build a full registry of every cloud resource and software tool — with costs, teams, and ownership inferred from tags automatically.'
	},
	{
		n: '03',
		title: 'Set your governance policies',
		desc: 'Pick from 40+ pre-built templates or write custom rules. Budget limits, vendor lists, DPA requirements — all live in minutes.'
	},
	{
		n: '04',
		title: 'Requests flow through the gate',
		desc: 'Every new resource request triggers a policy check and approval workflow. The right approver is notified in Slack with a one-click decision.'
	},
	{
		n: '05',
		title: 'Measure governance ROI',
		desc: 'Every denied request, reclaimed licence, and consolidated tool is tagged to a dollar saving. Share the report with Finance in one click.'
	}
];

export const INTEGRATIONS = [
	{ logo: 'aws.svg', name: 'AWS', tone: 'default' },
	{ logo: 'gcp.svg', name: 'GCP', tone: 'ion' },
	{ logo: 'azure.svg', name: 'Azure', tone: 'violet' },
	{ logo: 'slack.svg', name: 'Slack', tone: 'default' },
	{ logo: 'teams.svg', name: 'Teams', tone: 'default' },
	{ logo: 'jira.svg', name: 'Jira', tone: 'default' },
	{ logo: 'okta.svg', name: 'Okta', tone: 'default' },
	{ logo: 'github.svg', name: 'GitHub', tone: 'default' },
	{ logo: 'terraform.svg', name: 'Terraform', tone: 'default' },
	{ logo: 'pagerduty.svg', name: 'PagerDuty', tone: 'default' },
	{ logo: 'datadog.svg', name: 'Datadog', tone: 'default' },
	{ logo: 'figma.svg', name: 'Figma', tone: 'default' },
	{ logo: 'notion.svg', name: 'Notion', tone: 'default' },
	{ logo: 'stripe.svg', name: 'Stripe', tone: 'default' },
	{ logo: 'rippling.svg', name: 'Rippling', tone: 'default' },
	{ icon: '+', name: '+90 more', tone: 'muted' }
];

export const COMPARISON_ROWS = [
	['Approval workflows', '✓ policy-checked', 'Partial — SaaS only', '✕', '✕'],
	['Ownership tracking', '✓ cloud + SaaS', 'Partial — SaaS only', '✕', '✕'],
	['Policy engine', '✓ 40+ templates', 'Partial — basic rules', 'Partial', '✕'],
	['Shadow IT detection', '✓ cloud + SaaS', '✓ SaaS only', '✕', '✕'],
	['Unified cloud + SaaS', '✓', '✕ SaaS only', '✕ cloud only', '✕ AWS only'],
	['Proactive governance', '✓', '✕', '✕', '✕'],
	['Starting price', '$0 free tier / $49 paid entry', '$$$$ custom', '$$$$ custom', 'Free']
];

export const TICKER_ITEMS: TickerItem[] = [
	{ before: 'Avg. ', strong: '$34K/mo', after: ' saved in first 90 days' },
	{ before: 'Cloud ', strong: '+', after: ' SaaS in one governance view' },
	{ before: 'Audit evidence · DPA support' },
	{ before: '', strong: 'Shadow IT', after: ' detected and consolidated' },
	{ before: 'First approval workflow live in ', strong: '< 20 min' },
	{ before: '', strong: '100+ SaaS', after: ' integrations via OAuth' },
	{ before: 'Read-only access · ', strong: 'no write permissions' }
];

export const TRUST_BADGES = [
	'Read-only access',
	'Tenant-aware controls',
	'Approval workflows',
	'Audit evidence exports',
	'DPA support',
	'Secure data handling'
];

export const FOOTER_COLUMNS = [
	{ title: 'Product', links: ['Features', 'Pricing', 'Changelog', 'Integrations', 'Roadmap'] },
	{
		title: 'Learn',
		links: ['Documentation', 'Insights', 'Governance Guides', 'Case Studies', 'Glossary']
	},
	{ title: 'Company', links: ['About', 'Careers', 'Contact', 'Press', 'Security'] },
	{
		title: 'Legal',
		links: ['Privacy Policy', 'Terms of Service', 'DPA', 'Cookie Policy', 'SLA']
	}
];

export const structuredData = {
	'@context': 'https://schema.org',
	'@graph': [
		{
			'@type': 'WebSite',
			'@id': 'https://www.valdrics.com/#website',
			url: 'https://www.valdrics.com/',
			name: 'Valdrics',
			description: 'Cloud and software spend governance platform',
			publisher: { '@id': 'https://www.valdrics.com/#org' }
		},
		{
			'@type': 'Organization',
			'@id': 'https://www.valdrics.com/#org',
			name: 'Valdrics',
			url: 'https://www.valdrics.com',
			description:
				'Valdrics helps companies govern cloud and software spend through approval workflows, ownership tracking, and policy controls.',
			sameAs: ['https://twitter.com/valdrics', 'https://linkedin.com/company/valdrics']
		},
		{
			'@type': 'SoftwareApplication',
			name: 'Valdrics',
			applicationCategory: 'BusinessApplication',
			operatingSystem: 'Web, SaaS',
			description:
				'Cloud and software spend governance platform with approval workflows, ownership tracking, policy engine, and shadow IT detection.',
			offers: DEFAULT_PRICING_PLANS.map((plan) => ({
				'@type': 'Offer',
				name: plan.name,
				price: String(plan.price_monthly),
				priceCurrency: 'USD',
				description: plan.description
			}))
		},
		{
			'@type': 'FAQPage',
			mainEntity: [
				{
					'@type': 'Question',
					name: 'What is cloud and software spend governance?',
					acceptedAnswer: {
						'@type': 'Answer',
						text: 'Governance is the layer of controls that decides which cloud resources and software tools get approved, who owns them, and whether they comply with your policies before spend is committed.'
					}
				},
				{
					'@type': 'Question',
					name: 'How long does Valdrics setup take?',
					acceptedAnswer: {
						'@type': 'Answer',
						text: 'Your first approval workflow can be live in under 20 minutes. Cloud providers connect via read-only roles, and SaaS tools connect through supported integrations.'
					}
				},
				{
					'@type': 'Question',
					name: 'Does Valdrics need write access to cloud accounts?',
					acceptedAnswer: {
						'@type': 'Answer',
						text: "No. Valdrics is designed around read-only cloud access and keeps governance actions in your team's approval workflow."
					}
				}
			]
		}
	]
} as const;
