<script lang="ts">
	export let appPath: (path: string) => string;
	export let loginHref: () => string;
	export let signupHref: (source: string) => string;
	export let scrolled = false;
	export let mobileMenuOpen = false;
</script>

<header class="nav" class:nav--scrolled={scrolled}>
	<nav class="nav__inner" aria-label="Primary navigation">
		<a href={appPath('/')} class="nav__logo" aria-label="Valdrics home">
			<div class="nav__mark" aria-hidden="true">
				<img src={appPath('/valdrics_icon.png')} alt="" width="24" height="24" />
			</div>
			<span>VALDRICS</span>
		</a>
		<ul class="nav__links" role="list">
			<li><a href="#features">Features</a></li>
			<li><a href="#how-it-works">How it works</a></li>
			<li><a href="#pricing">Pricing</a></li>
			<li><a href={appPath('/insights')}>Insights</a></li>
		</ul>
		<div class="nav__actions">
			<a href={loginHref()} class="btn btn--ghost btn--sm">Sign in</a>
			<a href={signupHref('landing_nav_desktop')} class="btn btn--jade btn--sm"
				>Get started free →</a
			>
		</div>
		<button
			type="button"
			class="nav__burger"
			aria-label="Toggle menu"
			aria-expanded={mobileMenuOpen}
			on:click={() => (mobileMenuOpen = !mobileMenuOpen)}
		>
			<span></span><span></span><span></span>
		</button>
	</nav>
	{#if mobileMenuOpen}
		<nav id="public-mobile-menu" class="nav__mobile" aria-label="Mobile navigation">
			<a href="#features" on:click={() => (mobileMenuOpen = false)}>Features</a>
			<a href="#how-it-works" on:click={() => (mobileMenuOpen = false)}>How it works</a>
			<a href="#pricing" on:click={() => (mobileMenuOpen = false)}>Pricing</a>
			<a href={appPath('/insights')} on:click={() => (mobileMenuOpen = false)}>Insights</a>
			<div class="nav__mobile-actions">
				<a href={loginHref()} class="btn btn--ghost">Sign in</a>
				<a href={signupHref('landing_nav_mobile')} class="btn btn--jade">Start Free</a>
			</div>
		</nav>
	{/if}
</header>

<style>
	.nav {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		z-index: 100;
		height: 64px;
		padding: 0 40px;
		display: flex;
		align-items: center;
		background: rgba(3, 9, 18, 0);
		border-bottom: 1px solid transparent;
		transition: all 0.3s ease;
	}
	.nav--scrolled {
		background: rgba(3, 9, 18, 0.93);
		backdrop-filter: blur(14px);
		border-bottom-color: var(--bdr);
	}
	.nav__inner {
		display: flex;
		align-items: center;
		width: 100%;
		gap: 32px;
	}
	.nav__links {
		display: flex;
		align-items: center;
		gap: 26px;
		list-style: none;
		margin-left: auto;
	}
	.nav__links a {
		font-size: 13px;
		color: var(--sub);
		text-decoration: none;
		transition: color 0.15s;
	}
	.nav__links a:hover {
		color: var(--text);
	}
	.nav__actions {
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.nav__burger {
		display: none;
		flex-direction: column;
		gap: 5px;
		background: none;
		border: none;
		cursor: pointer;
		padding: 6px;
	}
	.nav__burger span {
		display: block;
		width: 22px;
		height: 2px;
		background: var(--sub);
		border-radius: 1px;
	}
	.nav__mobile {
		position: fixed;
		top: 64px;
		right: 0;
		left: 0;
		display: flex;
		flex-direction: column;
		gap: 6px;
		max-height: calc(100vh - 64px);
		overflow-y: auto;
		padding: 20px 24px;
		background: var(--base);
		border-bottom: 1px solid var(--bdr);
		animation: navMenuIn 0.22s cubic-bezier(0.22, 1, 0.36, 1) both;
	}
	.nav__mobile a {
		font-size: 14px;
		color: var(--sub);
		text-decoration: none;
		padding: 6px 0;
		border-bottom: 1px solid var(--bdr);
	}
	.nav__mobile a.btn--jade {
		color: #030912;
		border-bottom-color: transparent;
	}
	.nav__mobile-actions {
		display: flex;
		gap: 10px;
		margin-top: 8px;
		padding-top: 8px;
	}
	@keyframes navMenuIn {
		from {
			opacity: 0;
			transform: translateY(-8px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
	@media (max-width: 900px) {
		.nav__links,
		.nav__actions {
			display: none;
		}
		.nav__burger {
			display: flex;
		}
		.nav {
			padding: 0 24px;
		}
	}
</style>
