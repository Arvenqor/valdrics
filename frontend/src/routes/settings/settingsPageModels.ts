export type PolicyChannelDiagnostics = {
	enabled_for_policy: boolean;
	enabled_in_notifications: boolean;
	ready: boolean;
	reasons: string[];
};

export type PolicyDiagnostics = {
	tier: string;
	has_activeops_settings: boolean;
	has_notification_settings: boolean;
	policy_enabled: boolean;
	slack: PolicyChannelDiagnostics & {
		feature_allowed_by_tier: boolean;
		has_bot_token: boolean;
		has_default_channel: boolean;
		has_channel_override: boolean;
		selected_channel?: string | null;
		channel_source: string;
	};
	jira: PolicyChannelDiagnostics & {
		feature_allowed_by_tier: boolean;
		has_base_url: boolean;
		has_email: boolean;
		has_project_key: boolean;
		has_api_token: boolean;
		issue_type: string;
	};
};

export type SafetyStatus = {
	circuit_state: string;
	failure_count: number;
	daily_savings_used: number;
	daily_savings_limit: number;
	last_failure_at: string | null;
	can_execute: boolean;
};

export function formatCircuitState(state: string): string {
	const normalized = state.replaceAll('_', ' ');
	return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

export function safetyUsagePercent(status: SafetyStatus | null): number {
	if (!status || status.daily_savings_limit <= 0) return 0;
	return Math.min((status.daily_savings_used / status.daily_savings_limit) * 100, 100);
}

export function formatSafetyDate(value: string | null): string {
	if (!value) return 'None';
	const parsed = new Date(value);
	if (Number.isNaN(parsed.getTime())) return value;
	return parsed.toLocaleString();
}
