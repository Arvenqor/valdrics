import { z } from '$lib/validation/clientZod';

const optionalString = (maxLength: number) => z.optional(z.string().check(z.maxLength(maxLength)));

export const NotificationSettingsSchema = z.object({
	slack_enabled: z.boolean(),
	slack_channel_override: optionalString(50),
	jira_enabled: z.boolean(),
	jira_base_url: optionalString(255),
	jira_email: z.optional(z.string().check(z.email(), z.maxLength(255))),
	jira_project_key: optionalString(32),
	jira_issue_type: optionalString(64),
	jira_api_token: optionalString(1024),
	clear_jira_api_token: z.optional(z.boolean()),
	teams_enabled: z.boolean(),
	teams_webhook_url: optionalString(1024),
	clear_teams_webhook_url: z.optional(z.boolean()),
	workflow_github_enabled: z.boolean(),
	workflow_github_owner: optionalString(100),
	workflow_github_repo: optionalString(100),
	workflow_github_workflow_id: optionalString(200),
	workflow_github_ref: z.string().check(z.maxLength(100)),
	workflow_github_token: optionalString(1024),
	clear_workflow_github_token: z.optional(z.boolean()),
	workflow_gitlab_enabled: z.boolean(),
	workflow_gitlab_base_url: z.string().check(z.maxLength(255)),
	workflow_gitlab_project_id: optionalString(128),
	workflow_gitlab_ref: z.string().check(z.maxLength(100)),
	workflow_gitlab_trigger_token: optionalString(1024),
	clear_workflow_gitlab_trigger_token: z.optional(z.boolean()),
	workflow_webhook_enabled: z.boolean(),
	workflow_webhook_url: optionalString(500),
	workflow_webhook_bearer_token: optionalString(1024),
	clear_workflow_webhook_bearer_token: z.optional(z.boolean()),
	digest_schedule: z.enum(['daily', 'weekly', 'disabled']),
	digest_hour: z.number().check(z.minimum(0), z.maximum(23)),
	digest_minute: z.number().check(z.minimum(0), z.maximum(59)),
	alert_on_budget_warning: z.boolean(),
	alert_on_budget_exceeded: z.boolean(),
	alert_on_zombie_detected: z.boolean()
});

export const CarbonSettingsSchema = z.object({
	carbon_budget_kg: z.number().check(z.minimum(1), z.maximum(100000)),
	alert_threshold_percent: z.number().check(z.minimum(1), z.maximum(100)),
	default_region: z.string().check(z.minLength(2)),
	email_enabled: z.boolean(),
	email_recipients: z.optional(z.string())
});

export const LLMSettingsSchema = z.object({
	monthly_limit_usd: z.number().check(z.minimum(0), z.maximum(10000)),
	alert_threshold_percent: z.number().check(z.minimum(0), z.maximum(100)),
	hard_limit: z.boolean(),
	preferred_provider: z.string(),
	preferred_model: z.string(),
	openai_api_key: z.union([z.optional(z.string().check(z.minLength(20))), z.literal('')]),
	claude_api_key: z.union([z.optional(z.string().check(z.minLength(20))), z.literal('')]),
	google_api_key: z.union([z.optional(z.string().check(z.minLength(20))), z.literal('')]),
	groq_api_key: z.union([z.optional(z.string().check(z.minLength(20))), z.literal('')])
});

export const ActiveOpsSettingsSchema = z.object({
	auto_pilot_enabled: z.boolean(),
	min_confidence_threshold: z.number().check(z.minimum(0.5), z.maximum(1.0)),
	policy_enabled: z.boolean(),
	policy_block_production_destructive: z.boolean(),
	policy_require_gpu_override: z.boolean(),
	policy_low_confidence_warn_threshold: z.number().check(z.minimum(0.5), z.maximum(1.0)),
	policy_violation_notify_slack: z.boolean(),
	policy_violation_notify_jira: z.boolean(),
	policy_escalation_required_role: z.enum(['owner', 'admin']),
	license_auto_reclaim_enabled: z.boolean(),
	license_inactive_threshold_days: z.number().check(z.minimum(7), z.maximum(365)),
	license_reclaim_grace_period_days: z.number().check(z.minimum(1), z.maximum(30)),
	license_downgrade_recommendations_enabled: z.boolean()
});
