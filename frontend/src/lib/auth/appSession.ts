import { z } from 'zod';

const nonEmptyString = z.string().trim().min(1);
const optionalNonEmptyString = z
	.string()
	.trim()
	.min(1)
	.optional()
	.or(z.literal('').transform(() => undefined));

export const AppUserSchema = z.object({
	id: nonEmptyString,
	email: nonEmptyString.email().or(nonEmptyString),
	tenantId: optionalNonEmptyString,
	role: nonEmptyString.default('member'),
	tier: nonEmptyString.default('free'),
	persona: nonEmptyString.default('engineering'),
	platformOperator: z.boolean().default(false)
});

export const AppSessionSchema = z.object({
	accessToken: nonEmptyString,
	user: AppUserSchema
});

export type AppUser = z.infer<typeof AppUserSchema>;
export type AppSession = z.infer<typeof AppSessionSchema>;

type LooseUser = {
	id?: unknown;
	email?: unknown;
	tenant_id?: unknown;
	role?: unknown;
	tier?: unknown;
	persona?: unknown;
	user_metadata?: Record<string, unknown> | null;
	app_metadata?: Record<string, unknown> | null;
};

type LooseSession = {
	access_token?: unknown;
	user?: LooseUser | null;
};

function stringFrom(...values: unknown[]): string | undefined {
	for (const value of values) {
		if (typeof value !== 'string') continue;
		const trimmed = value.trim();
		if (trimmed.length > 0) return trimmed;
	}
	return undefined;
}

export function resolveAppSession(input: {
	session?: LooseSession | null;
	user?: LooseUser | null;
	profile?: {
		role?: unknown;
		tier?: unknown;
		persona?: unknown;
		platform_operator?: unknown;
	} | null;
}): AppSession | null {
	const session = input.session;
	const user = input.user ?? session?.user ?? null;
	const accessToken = stringFrom(session?.access_token);
	const userId = stringFrom(user?.id);
	const email = stringFrom(user?.email);

	if (!accessToken || !userId || !email) return null;

	const candidate = {
		accessToken,
		user: {
			id: userId,
			email,
			tenantId: stringFrom(
				user?.tenant_id,
				user?.user_metadata?.tenant_id,
				session?.user?.user_metadata?.tenant_id
			),
			role: stringFrom(input.profile?.role, user?.role, user?.app_metadata?.role) ?? 'member',
			tier: stringFrom(input.profile?.tier, user?.tier, user?.app_metadata?.tier) ?? 'free',
			persona:
				stringFrom(input.profile?.persona, user?.persona, user?.user_metadata?.persona) ??
				'engineering',
			platformOperator: Boolean(input.profile?.platform_operator)
		}
	};

	return AppSessionSchema.parse(candidate);
}
