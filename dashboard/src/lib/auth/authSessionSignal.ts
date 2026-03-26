export const AUTH_SESSION_SIGNAL_KEY = 'valdrics.auth.signal.v1';

export function broadcastAuthSessionChanged(): void {
	if (typeof window === 'undefined') return;
	try {
		window.localStorage.setItem(AUTH_SESSION_SIGNAL_KEY, String(Date.now()));
	} catch {
		// Ignore storage failures in restricted environments.
	}
}
