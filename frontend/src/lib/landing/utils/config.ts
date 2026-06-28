export type LandingMotionProfile = 'subtle' | 'cinematic';

export { DEFAULT_ASSIGNMENTS as DEFAULT_EXPERIMENT_ASSIGNMENTS } from '../telemetry/experiments';

const SNAPSHOT_ROTATION_MS = 4400;
const DEMO_ROTATION_MS = 3200;
const LANDING_SCROLL_MILESTONES = Object.freeze([25, 50, 75, 95]);
const LANDING_CONSENT_KEY = 'valdrics.cookie_consent.v1';
export function resolveLandingMotionProfile(url: URL): LandingMotionProfile {
	const value = url.searchParams.get('motion')?.trim().toLowerCase();
	return value === 'cinematic' ? 'cinematic' : 'subtle';
}
