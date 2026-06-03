/**
 * TypeScript Declarations for App
 *
 * Extends SvelteKit's types with our Supabase integration.
 */

import type { SupabaseClient, Session, User } from '@supabase/supabase-js';
import type { AppSession } from '$lib/auth/appSession';

type RootSubscription = {
	tier?: string;
	status?: string;
	next_payment_date?: string | null;
};

type RootProfile = {
	persona?: string;
	role?: string;
	tier?: string;
	platform_operator?: boolean;
};

declare global {
	namespace App {
		interface Locals {
			supabase: SupabaseClient;
			safeGetSession: () => Promise<{ session: Session | null; user: User | null }>;
		}

		interface PageData {
			session: Session | null;
			user: User | null;
			appSession?: AppSession | null;
			subscription: RootSubscription;
			profile: RootProfile | null;
		}
		// interface Error {}
		// interface Platform {}
	}
}

export {};
