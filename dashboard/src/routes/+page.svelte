<!--
  src/routes/(marketing)/+page.svelte
  Valdrics · Landing Page

  Design concept: THE GATE
  The vertical glowing line running through the hero represents
  the approval boundary — the governance gate between requested
  spend and approved spend. Everything visual expresses this idea.

  Sections:
    1.  Nav
    2.  Hero — editorial headline + live approval preview
    3.  Proof ticker
    4.  The Problem (before/after gate)
    5.  Features — asymmetric editorial grid
    6.  How it works — 5-step flow
    7.  Live governance counter
    8.  Integrations
    9.  Testimonials
    10. Comparison table
    11. FAQ accordion
    12. Pricing
    13. Blog teasers
    14. Trust bar
    15. Final CTA
    16. Footer
-->

<script lang="ts">
  import { onMount }  from 'svelte';
  import { tweened }  from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';
  import { fly, fade } from 'svelte/transition';
  import { base } from '$app/paths';

  // ── Scroll-reveal action ──────────────────────────────────────
  // A lightweight Svelte action — replaces every scroll-reveal library
  function reveal(node: Element, { threshold = 0.12, delay = 0 } = {}) {
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

  // ── Count-up action ───────────────────────────────────────────
  function countUp(node: HTMLElement, { target, duration = 1800 }: { target: number; duration?: number }) {
    let start: number | null = null;
    let raf: number;
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      const tick = (ts: number) => {
        if (!start) start = ts;
        const p = Math.min((ts - start) / duration, 1);
        const eased = 1 - Math.pow(1 - p, 3);
        node.textContent = Math.round(eased * target).toLocaleString();
        if (p < 1) raf = requestAnimationFrame(tick);
      };
      raf = requestAnimationFrame(tick);
      observer.disconnect();
    }, { threshold: 0.5 });
    observer.observe(node);
    return { destroy: () => { observer.disconnect(); cancelAnimationFrame(raf); } };
  }

  // ── Nav scroll state ──────────────────────────────────────────
  let scrolled = false;
  let mobileMenuOpen = false;

  // ── FAQ state ─────────────────────────────────────────────────
  let openFaq: number | null = null;

  // ── Live counter (simulated realtime governance activity) ─────
  let decisionsToday  = 1847;
  let shadowFlagged   = 312;
  let violationsCaught = 2941;

  // ── Hero approval cards — cycles through states ───────────────
  let heroCardState: 'pending' | 'approved' | 'denied' = 'pending';
  let heroCardVisible = true;

  const FAQS = [
    {
      q: 'What is cloud and software spend governance?',
      a: 'Governance is the layer of controls that decides which cloud resources and software tools get approved, who owns them, and whether they comply with your organisation\'s policies — before the spend is committed. Valdrics makes governance automatic: every request triggers a policy check, and every resource has an assigned owner. The result is that waste gets stopped before it reaches the bill, not discovered after.',
    },
    {
      q: 'How long does setup take?',
      a: 'Your first approval workflow can be live in under 20 minutes. Cloud providers connect via a read-only IAM role (AWS), service account (GCP), or app registration (Azure) — 3 to 5 minutes each. SaaS tools connect via OAuth in one click. No agents to install, no professional services call, no onboarding marathon.',
    },
    {
      q: 'Does Valdrics need write access to my cloud accounts?',
      a: 'Never. Valdrics is entirely read-only. We read your billing and usage data to build the inventory and detect anomalies. All governance actions — approving a resource, cancelling a SaaS subscription, rightsizing an instance — are carried out by your team. Valdrics tells you what to do and tracks that it was done.',
    },
    {
      q: 'How does Valdrics handle both cloud and SaaS in one platform?',
      a: 'Most tools pick one or the other. Cloud cost platforms ignore the $40K/year your team spends on SaaS tools nobody uses. SaaS management tools ignore the EC2 instances nobody owns. Valdrics treats every paid resource — whether it\'s an RDS cluster or a Figma seat — as an asset that needs approval, ownership, and periodic justification. One inventory, one approval queue, one governance layer.',
    },
    {
      q: 'What governance policies can Valdrics enforce?',
      a: 'Valdrics ships with 40+ pre-built policy templates: budget limits per team, vendor approval lists, data residency restrictions, DPA requirements for data processors, commitment thresholds for Finance sign-off, and seat limits for SaaS tools. Enterprise customers can write custom rules in the policy editor. Every policy evaluates automatically on every new approval request.',
    },
    {
      q: 'How does Valdrics measure the return on governance?',
      a: 'Every saving is attributed to the specific governance action that produced it. A denied over-budget request, a reclaimed unused licence, a shadow IT tool cancelled — each is tagged with a dollar amount and a reason. Finance gets a governance ROI report that shows exactly what governance enforcement saved, not just a cost chart with no narrative.',
    },
    {
      q: 'How is Valdrics different from Torii or Zylo?',
      a: 'Torii and Zylo are SaaS management tools — they track software licences but don\'t touch cloud infrastructure, don\'t run approval workflows before spend is committed, and don\'t enforce policy rules. Valdrics unifies cloud and SaaS governance in one platform, adds a proactive approval gate, and measures the ROI from governance enforcement. The core difference: Torii tells you what you\'re spending. Valdrics stops you spending what you shouldn\'t.',
    },
    {
      q: 'Is Valdrics SOC 2 certified?',
      a: 'Yes. Valdrics is SOC 2 Type II certified and GDPR compliant. All data is encrypted in transit (TLS 1.3) and at rest (AES-256). We hold only cost and usage metadata — never source code, configuration, or application data. Enterprise customers can request VPC deployment for complete data isolation within their own cloud environment.',
    },
  ];

  const PRICING = [
    {
      tier: 'Starter',
      price: '$299',
      period: '/month',
      desc: 'For growing teams who want to stop cloud and software surprises before they happen.',
      cta: 'Start free trial',
      ctaHref: '/signup?plan=starter',
      popular: false,
      features: [
        'Up to 3 cloud accounts',
        'Up to 10 SaaS tools tracked',
        'Approval workflows (basic)',
        'Ownership tracking',
        '10 pre-built policy templates',
        'Slack notifications',
        { text: 'Shadow IT detection', disabled: true },
        { text: 'Custom policy rules', disabled: true },
      ],
    },
    {
      tier: 'Team',
      price: '$799',
      period: '/month',
      desc: 'For engineering orgs managing cloud and software governance across multiple teams.',
      cta: 'Start free trial →',
      ctaHref: '/signup?plan=team',
      popular: true,
      features: [
        'Unlimited cloud accounts',
        '100+ SaaS tools tracked',
        'Full approval workflows',
        'Ownership tracking + reminders',
        'All 40+ policy templates',
        'Shadow IT detection',
        'Slack + Teams integration',
        { text: 'Custom policy rules', disabled: true },
      ],
    },
    {
      tier: 'Enterprise',
      price: 'Custom',
      period: '',
      desc: 'For large organisations with compliance mandates, complex governance, and custom workflows.',
      cta: 'Talk to us',
      ctaHref: '/contact',
      popular: false,
      features: [
        'Everything in Team',
        'Custom policy-as-code',
        'SSO / SAML 2.0',
        'Dedicated success engineer',
        'VPC / on-prem deployment',
        'Custom SLA + priority support',
        'Compliance reporting (SOC 2, ISO)',
        'Unlimited team members',
      ],
    },
  ];

  onMount(() => {
    // Nav scroll effect
    const handleScroll = () => { scrolled = window.scrollY > 48; };
    window.addEventListener('scroll', handleScroll, { passive: true });

    // Live counter increments — simulates real governance activity
    const counterInterval = setInterval(() => {
      decisionsToday   += Math.floor(Math.random() * 3);
      shadowFlagged    += Math.random() > 0.8 ? 1 : 0;
      violationsCaught += Math.floor(Math.random() * 2);
    }, 3200);

    // Hero card state cycle: pending → approved/denied → pending
    const cardCycle = setInterval(() => {
      heroCardVisible = false;
      setTimeout(() => {
        heroCardState   = heroCardState === 'pending'
          ? (Math.random() > 0.4 ? 'approved' : 'denied')
          : 'pending';
        heroCardVisible = true;
      }, 400);
    }, 3500);

    return () => {
      window.removeEventListener('scroll', handleScroll);
      clearInterval(counterInterval);
      clearInterval(cardCycle);
    };
  });

  function toggleFaq(i: number) {
    openFaq = openFaq === i ? null : i;
  }

  function fmt(n: number): string {
    return n.toLocaleString();
  }
</script>


<!-- ═══ SEO HEAD ═══════════════════════════════════════════════════ -->
<svelte:head>
  <title>Valdrics — Cloud & Software Spend Governance | Approval Workflows & Ownership Tracking</title>
  <meta name="description" content="Valdrics helps engineering and finance teams stop wasting money on cloud and software by enforcing approval workflows, ownership tracking, and governance policies before spend is committed. AWS, GCP, Azure + 100s of SaaS tools."/>
  <meta name="keywords" content="cloud governance platform, SaaS spend management, software license management, approval workflow software, cloud cost governance, shadow IT detection, IT spend management"/>
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large"/>
  <link rel="canonical" href="https://www.valdrics.com/"/>

  <!-- Open Graph -->
  <meta property="og:type"         content="website"/>
  <meta property="og:url"          content="https://www.valdrics.com/"/>
  <meta property="og:title"        content="Valdrics — Govern cloud and software spend before the bill arrives"/>
  <meta property="og:description"  content="Approval workflows, ownership tracking, and governance policies for cloud and SaaS spend. Stop waste before it reaches the invoice."/>
  <meta property="og:image"        content="https://www.valdrics.com/og-image.png"/>
  <meta property="og:image:width"  content="1200"/>
  <meta property="og:image:height" content="630"/>
  <meta property="og:site_name"    content="Valdrics"/>

  <!-- Twitter -->
  <meta name="twitter:card"        content="summary_large_image"/>
  <meta name="twitter:site"        content="@valdrics"/>
  <meta name="twitter:title"       content="Valdrics — Cloud & Software Spend Governance"/>
  <meta name="twitter:description" content="Approval workflows, ownership tracking, and policy enforcement for cloud and SaaS spend. Engineering and finance, finally aligned."/>
  <meta name="twitter:image"       content="https://www.valdrics.com/twitter-card.png"/>

  <!-- Structured Data -->
  {@html `<script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebSite",
        "@id": "https://www.valdrics.com/#website",
        "url": "https://www.valdrics.com/",
        "name": "Valdrics",
        "description": "Cloud and software spend governance platform",
        "publisher": { "@id": "https://www.valdrics.com/#org" }
      },
      {
        "@type": "Organization",
        "@id": "https://www.valdrics.com/#org",
        "name": "Valdrics Inc.",
        "url": "https://www.valdrics.com",
        "description": "Valdrics helps companies stop wasting money on cloud and software by enforcing approval workflows, ownership tracking, and governance policies.",
        "sameAs": ["https://twitter.com/valdrics","https://linkedin.com/company/valdrics"]
      },
      {
        "@type": "SoftwareApplication",
        "name": "Valdrics",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web, SaaS",
        "description": "Cloud and software spend governance platform with approval workflows, ownership tracking, policy engine, and shadow IT detection.",
        "offers": [
          { "@type": "Offer", "name": "Starter",    "price": "299",  "priceCurrency": "USD" },
          { "@type": "Offer", "name": "Team",       "price": "799",  "priceCurrency": "USD" },
          { "@type": "Offer", "name": "Enterprise", "description": "Custom pricing"         }
        ],
        "aggregateRating": { "@type": "AggregateRating", "ratingValue": "4.8", "reviewCount": "74" }
      },
      {
        "@type": "FAQPage",
        "mainEntity": [
          { "@type": "Question", "name": "What is cloud and software spend governance?", "acceptedAnswer": { "@type": "Answer", "text": "Governance is the layer of controls that decides which cloud resources and software tools get approved, who owns them, and whether they comply with your policies — before spend is committed." } },
          { "@type": "Question", "name": "How long does Valdrics setup take?", "acceptedAnswer": { "@type": "Answer", "text": "Your first approval workflow can be live in under 20 minutes. Cloud providers connect via read-only roles. SaaS tools connect via OAuth in one click." } },
          { "@type": "Question", "name": "Does Valdrics need write access to cloud accounts?", "acceptedAnswer": { "@type": "Answer", "text": "Never. Valdrics is entirely read-only. All governance actions are carried out by your team — Valdrics tells you what to do and tracks that it was done." } }
        ]
      }
    ]
  }
  <\/script>`}
</svelte:head>


<!-- ═══ NAV ═══════════════════════════════════════════════════════ -->
<header class="nav" class:nav--scrolled={scrolled}>
  <nav class="nav__inner" aria-label="Primary navigation">

    <a href="/" class="nav__logo" aria-label="Valdrics home">
      <div class="nav__mark" aria-hidden="true">
        <svg width="15" height="15" viewBox="0 0 20 20" fill="none">
          <path d="M10 2L18 10L10 18L2 10Z" stroke="var(--jade)" stroke-width="1.5" fill="none"/>
          <path d="M6 10L10 6L14 10L10 14Z" fill="rgba(0,207,124,0.2)" stroke="var(--jade)" stroke-width="1"/>
          <circle cx="10" cy="10" r="1.8" fill="var(--jade)"/>
        </svg>
      </div>
      <span>VALDRICS</span>
    </a>

    <ul class="nav__links" role="list">
      <li><a href="#features">Features</a></li>
      <li><a href="#how-it-works">How it works</a></li>
      <li><a href="#pricing">Pricing</a></li>
      <li><a href="/blog">Blog</a></li>
    </ul>

    <div class="nav__actions">
      <a href="/auth/login?mode=login" class="btn btn--ghost  btn--sm">Sign in</a>
      <a href="/auth/login?mode=signup" class="btn btn--jade   btn--sm">Get started free →</a>
    </div>

    <button
      class="nav__burger"
      aria-label="Toggle menu"
      aria-expanded={mobileMenuOpen}
      on:click={() => mobileMenuOpen = !mobileMenuOpen}
    >
      <span></span><span></span><span></span>
    </button>

  </nav>

  <!-- Mobile menu -->
  {#if mobileMenuOpen}
    <div class="nav__mobile" transition:fly={{ y: -8, duration: 220 }}>
      <a href="#features"    on:click={() => mobileMenuOpen = false}>Features</a>
      <a href="#how-it-works"on:click={() => mobileMenuOpen = false}>How it works</a>
      <a href="#pricing"     on:click={() => mobileMenuOpen = false}>Pricing</a>
      <a href="/blog"        on:click={() => mobileMenuOpen = false}>Blog</a>
      <div class="nav__mobile-actions">
        <a href="/auth/login?mode=login" class="btn btn--ghost">Sign in</a>
        <a href="/auth/login?mode=signup" class="btn btn--jade">Get started →</a>
      </div>
    </div>
  {/if}
</header>


<!-- ═══ HERO ═══════════════════════════════════════════════════════ -->
<section class="hero" id="hero" aria-label="Valdrics governance platform hero">

  <!-- Background: animated governance grid -->
  <div class="hero__bg" aria-hidden="true">
    <div class="hero__grid"></div>
    <div class="hero__orb hero__orb--1"></div>
    <div class="hero__orb hero__orb--2"></div>
    <div class="hero__orb hero__orb--3"></div>
    <!-- The Gate line — vertical governance boundary -->
    <div class="hero__gate"></div>
  </div>

  <div class="hero__inner">

    <!-- Left: editorial headline -->
    <div class="hero__text">
      <div class="hero__badge" role="status">
        <span class="hero__badge-dot" aria-hidden="true"></span>
        LIVE AT VALDRICS.COM
      </div>

      <h1 class="hero__headline">
        <span class="hero__headline-line">Govern</span>
        <span class="hero__headline-line hero__headline-line--accent">first.</span>
        <span class="hero__headline-line hero__headline-line--dim">Optimize</span>
        <span class="hero__headline-line hero__headline-line--dim">always.</span>
      </h1>

      <p class="hero__sub">
        Valdrics enforces approval workflows, ownership tracking, and governance policies
        across cloud infrastructure and software services —
        so engineering and finance teams stop paying for things they never needed.
      </p>

      <div class="hero__actions">
        <a href="/auth/login?mode=signup" class="btn btn--jade btn--lg">
          Start free — no card needed →
        </a>
        <a href="/demo" class="btn btn--ghost btn--lg">
          See a live demo ↗
        </a>
      </div>

      <div class="hero__chips" role="list" aria-label="Key statistics">
        <div class="chip" role="listitem"><strong>Proactive</strong> governance, not reactive reports</div>
        <div class="chip" role="listitem"><strong>Cloud + SaaS</strong> in one platform</div>
        <div class="chip" role="listitem"><strong>&lt; 20 min</strong> to first approval workflow</div>
      </div>
    </div>

    <!-- Right: live approval card preview -->
    <div class="hero__preview" aria-label="Live approval queue preview showing governance in action">
      <div class="hero__preview-label" aria-hidden="true">
        <span class="live-dot" aria-hidden="true"></span>
        APPROVAL QUEUE · LIVE
      </div>

      <!-- Cycling approval card -->
      {#if heroCardVisible}
        <div
          class="hero-card"
          class:hero-card--approved={heroCardState === 'approved'}
          class:hero-card--denied={heroCardState === 'denied'}
          transition:fly={{ y: 10, duration: 300 }}
        >
          <div class="hero-card__stripe
            {heroCardState === 'approved' ? 'hero-card__stripe--jade' :
             heroCardState === 'denied'   ? 'hero-card__stripe--ruby' :
                                           'hero-card__stripe--amber'}"
          ></div>
          <div class="hero-card__body">
            <div class="hero-card__top">
              <span class="tag tag--cloud">CLOUD</span>
              <span class="hero-card__name">AWS r6i.4xlarge × 8</span>
              {#if heroCardState === 'pending'}
                <span class="tag tag--critical">CRITICAL</span>
              {:else if heroCardState === 'approved'}
                <span class="tag tag--approved">✓ APPROVED</span>
              {:else}
                <span class="tag tag--denied">✕ DENIED</span>
              {/if}
            </div>
            <div class="hero-card__policies">
              <span class="policy-tag policy-tag--warn">⚠ Budget</span>
              <span class="policy-tag policy-tag--pass">✓ Region</span>
              <span class="policy-tag policy-tag--pass">✓ Instance</span>
            </div>
            <div class="hero-card__meta">
              James Obi · ML Platform · 4h ago
            </div>
          </div>
          <div class="hero-card__cost">
            <div class="hero-card__cost-val">$4,200/mo</div>
            <div class="hero-card__cost-label">COST IMPACT</div>
            {#if heroCardState === 'pending'}
              <div class="hero-card__actions">
                <button class="btn-approve" aria-label="Approve this request">✓</button>
                <button class="btn-deny" aria-label="Deny this request">✕</button>
              </div>
            {:else if heroCardState === 'approved'}
              <div class="hero-card__decision hero-card__decision--approved">Approved by Sarah</div>
            {:else}
              <div class="hero-card__decision hero-card__decision--denied">Denied · over budget</div>
            {/if}
          </div>
        </div>
      {/if}

      <!-- Second card (static, slightly offset) -->
      <div class="hero-card hero-card--ghost">
        <div class="hero-card__stripe hero-card__stripe--violet"></div>
        <div class="hero-card__body">
          <div class="hero-card__top">
            <span class="tag tag--software">SOFTWARE</span>
            <span class="hero-card__name">Figma Pro — 15 seats</span>
          </div>
          <div class="hero-card__meta">Sarah Chen · Product Design · 6h ago</div>
        </div>
        <div class="hero-card__cost">
          <div class="hero-card__cost-val">$675/mo</div>
        </div>
      </div>

      <!-- Policy health mini -->
      <div class="hero__health">
        <div class="hero__health-ring" aria-hidden="true">
          <svg width="52" height="52" viewBox="0 0 52 52">
            <circle cx="26" cy="26" r="20" fill="none" stroke="var(--s3)" stroke-width="6"/>
            <circle cx="26" cy="26" r="20" fill="none" stroke="var(--jade)" stroke-width="6"
              stroke-linecap="round"
              stroke-dasharray="113 126"
              transform="rotate(-90 26 26)"
            />
          </svg>
          <span class="hero__health-score">94</span>
        </div>
        <div>
          <div class="hero__health-label">GOVERNANCE SCORE</div>
          <div class="hero__health-sub">↑ 4% this month</div>
        </div>
      </div>
    </div>

  </div>
</section>


<!-- ═══ PROOF TICKER ═══════════════════════════════════════════════ -->
<div class="ticker" aria-hidden="true">
  <div class="ticker__track">
    {#each Array(2) as _}
      <div class="ticker__item"><span class="tdot"></span> Avg. <strong>$34K/mo</strong> saved in first 90 days</div>
      <div class="ticker__item"><span class="tdot"></span> Cloud <strong>+</strong> SaaS in one governance view</div>
      <div class="ticker__item"><span class="tdot"></span> SOC 2 Type II · ISO 27001 · GDPR</div>
      <div class="ticker__item"><span class="tdot"></span> <strong>Shadow IT</strong> detected and consolidated</div>
      <div class="ticker__item"><span class="tdot"></span> First approval workflow live in <strong>&lt; 20 min</strong></div>
      <div class="ticker__item"><span class="tdot"></span> <strong>100+ SaaS</strong> integrations via OAuth</div>
      <div class="ticker__item"><span class="tdot"></span> Read-only access · <strong>no write permissions</strong></div>
    {/each}
  </div>
</div>


<!-- ═══ THE PROBLEM ════════════════════════════════════════════════ -->
<section class="problem" id="problem">
  <div class="container">
    <div use:reveal>
      <span class="section-label">The problem</span>
      <h2 class="section-title">Most tools tell you what went wrong<br/>after the invoice arrives.</h2>
      <p class="section-sub">Monitoring tells you the bill was too high. Governance stops it from getting that high in the first place. There is a meaningful difference.</p>
    </div>

    <div class="problem__gate" use:reveal={{ delay: 100 }}>

      <div class="problem__side problem__side--chaos">
        <div class="side-label side-label--bad">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
          Without Valdrics
        </div>
        <ul class="problem__list">
          <li>Engineers spin up tools on the company card — nobody notices for months</li>
          <li>Cloud resources running for 18 months with no owner and no justification</li>
          <li>Three teams paying separately for the same software tool</li>
          <li>Finance asks Engineering for cost justification — nobody can trace the decision</li>
          <li>A new data vendor is onboarded without a security review or signed DPA</li>
        </ul>
      </div>

      <!-- The Gate — the central visual metaphor -->
      <div class="problem__gate-line" aria-hidden="true">
        <div class="gate-glow"></div>
        <div class="gate-label">THE GATE</div>
      </div>

      <div class="problem__side problem__side--clarity">
        <div class="side-label side-label--good">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
          With Valdrics
        </div>
        <ul class="problem__list">
          <li>Every tool request routes through a policy-checked approval gate first</li>
          <li>Every resource has a named owner responsible for reviewing it quarterly</li>
          <li>Duplicate tools are flagged automatically and consolidated</li>
          <li>Every cost traces to a named approval, a team, and a business justification</li>
          <li>Security, DPA, and vendor policies are enforced automatically — zero gaps</li>
        </ul>
      </div>

    </div>
  </div>
</section>


<!-- ═══ FEATURES ══════════════════════════════════════════════════ -->
<section class="features" id="features">
  <div class="container">
    <div use:reveal>
      <span class="section-label">Platform capabilities</span>
      <h2 class="section-title">Governance is the new<br/>cloud cost optimization.</h2>
      <p class="section-sub">Every dollar Valdrics saves traces back to a specific governance action. An approval denied. An owner reclaiming a resource. A policy blocking a duplicate.</p>
    </div>

    <!-- Asymmetric editorial grid — not a standard 3-column layout -->
    <div class="features__grid">

      <!-- Large card: Approval Workflows -->
      <div class="fcard fcard--large fcard--jade" use:reveal={{ delay: 80 }}>
        <div class="fcard__icon fcard__icon--jade">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        </div>
        <h3 class="fcard__title">Approval Workflows</h3>
        <p class="fcard__desc">Every cloud resource and software request passes through a policy-checked approval gate before spend is committed. Budget, security, vendor, and region policies run automatically. Approvers see the full cost impact before they decide.</p>
        <!-- Mini approval card illustration -->
        <div class="fcard__illustration">
          <div class="mini-card mini-card--pending">
            <div class="mini-card__stripe mini-card__stripe--ruby"></div>
            <div class="mini-card__content">
              <span class="mini-tag mini-tag--cloud">CLOUD</span>
              <span class="mini-card__name">Datadog Pro upgrade</span>
            </div>
            <div class="mini-card__right">
              <div class="mini-card__cost">$2,800/mo</div>
              <div class="mini-card__btns">
                <span class="mini-btn mini-btn--approve">✓</span>
                <span class="mini-btn mini-btn--deny">✕</span>
              </div>
            </div>
          </div>
          <div class="policy-chips">
            <span class="policy-chip policy-chip--pass">✓ Budget</span>
            <span class="policy-chip policy-chip--fail">✕ DPA required</span>
            <span class="policy-chip policy-chip--warn">⚠ New vendor</span>
          </div>
        </div>
        <div class="fcard__stat">
          <span class="fcard__stat-val" style="color: var(--jade)">20 min</span>
          <span class="fcard__stat-label">from signup to first live approval workflow</span>
        </div>
      </div>

      <!-- Right column: two stacked cards -->
      <div class="fcard__col">

        <div class="fcard fcard--ion" use:reveal={{ delay: 160 }}>
          <div class="fcard__icon fcard__icon--ion">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          </div>
          <h3 class="fcard__title">Ownership Tracking</h3>
          <p class="fcard__desc">Every cloud resource and SaaS licence gets a named owner. Owners receive quarterly review requests and renewal alerts. Resources with no owner are flagged on day one.</p>
          <div class="fcard__stat">
            <span class="fcard__stat-val" style="color: var(--ion)">87%</span>
            <span class="fcard__stat-label">avg. ownership coverage on day 30</span>
          </div>
        </div>

        <div class="fcard fcard--violet" use:reveal={{ delay: 220 }}>
          <div class="fcard__icon fcard__icon--violet">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
          </div>
          <h3 class="fcard__title">Policy Engine</h3>
          <p class="fcard__desc">40+ pre-built governance policies. Budget limits, vendor lists, DPA requirements, data residency, commitment thresholds. Enterprise teams write custom rules in the policy editor.</p>
          <div class="fcard__stat">
            <span class="fcard__stat-val" style="color: var(--violet)">40+</span>
            <span class="fcard__stat-label">pre-built governance policy templates</span>
          </div>
        </div>

      </div>

    </div>

    <!-- Second row: flipped layout -->
    <div class="features__grid features__grid--flipped" style="margin-top: 14px;">

      <!-- Left column: two stacked -->
      <div class="fcard__col">
        <div class="fcard fcard--ruby" use:reveal={{ delay: 80 }}>
          <div class="fcard__icon fcard__icon--ruby">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
          </div>
          <h3 class="fcard__title">Shadow IT Detection</h3>
          <p class="fcard__desc">Cross-references cloud billing, corporate card, and expense feeds against your approved tool inventory. Unapproved tools are flagged and consolidated — typically saving 15–25% of software spend in the first 90 days.</p>
          <div class="fcard__stat">
            <span class="fcard__stat-val" style="color: var(--ruby)">12 tools</span>
            <span class="fcard__stat-label">avg. shadow IT found per team in month 1</span>
          </div>
        </div>

        <div class="fcard fcard--amber" use:reveal={{ delay: 160 }}>
          <div class="fcard__icon fcard__icon--amber">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </div>
          <h3 class="fcard__title">Savings Attribution</h3>
          <p class="fcard__desc">Every saving is tagged to the governance action that produced it. Finance gets a clear ROI statement — not just a cost chart with no story attached.</p>
          <div class="fcard__stat">
            <span class="fcard__stat-val" style="color: var(--amber)">$34K</span>
            <span class="fcard__stat-label">avg. monthly savings in first quarter</span>
          </div>
        </div>
      </div>

      <!-- Large card: Spend Topology -->
      <div class="fcard fcard--large fcard--ion" use:reveal={{ delay: 120 }}>
        <div class="fcard__icon fcard__icon--ion">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        </div>
        <h3 class="fcard__title">Unified Spend Topology</h3>
        <p class="fcard__desc">AWS, GCP, Azure, and 100+ SaaS tools unified in one living spend map. Cloud infrastructure and software costs in the same inventory, the same approval queue, the same governance layer. The only platform that covers both.</p>
        <!-- Mini topology chart illustration -->
        <div class="fcard__illustration">
          <svg viewBox="0 0 280 80" style="width:100%;display:block;" preserveAspectRatio="none">
            <defs>
              <linearGradient id="tg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#00C2FF" stop-opacity=".22"/>
                <stop offset="100%" stop-color="#00C2FF" stop-opacity=".02"/>
              </linearGradient>
            </defs>
            <line x1="0" y1="27" x2="280" y2="27" stroke="rgba(100,170,230,.07)" stroke-width="1"/>
            <line x1="0" y1="54" x2="280" y2="54" stroke="rgba(100,170,230,.07)" stroke-width="1"/>
            <path d="M0,58 C18,52 35,62 52,56 C69,50 87,42 104,36 C121,30 139,22 156,18 C173,14 191,28 208,32 C225,36 243,30 280,34 L280,80 L0,80 Z" fill="url(#tg)"/>
            <path d="M0,58 C18,52 35,62 52,56 C69,50 87,42 104,36 C121,30 139,22 156,18 C173,14 191,28 208,32 C225,36 243,30 280,34" fill="none" stroke="var(--ion)" stroke-width="1.8"/>
            <circle cx="156" cy="18" r="4" fill="var(--ruby)" stroke="var(--s2)" stroke-width="2"/>
            <line x1="156" y1="0" x2="156" y2="80" stroke="var(--ruby)" stroke-width="1" stroke-dasharray="3,3" opacity=".4"/>
            <text x="162" y="12" font-size="8" fill="var(--ruby)" font-family="JetBrains Mono,monospace">spike detected</text>
            <path d="M0,66 C18,62 35,68 52,64 C69,60 87,55 104,50 C121,45 139,38 156,35 C173,32 191,42 208,46 C225,50 243,45 280,48" fill="none" stroke="var(--violet)" stroke-width="1.2" opacity=".6"/>
          </svg>
          <div class="topology-legend">
            <span><i style="background:var(--ion)"></i> Cloud Infra</span>
            <span><i style="background:var(--violet)"></i> Software/SaaS</span>
          </div>
        </div>
        <div class="fcard__stat">
          <span class="fcard__stat-val" style="color: var(--ion)">3 clouds</span>
          <span class="fcard__stat-label">+ 100s of SaaS tools in one unified view</span>
        </div>
      </div>

    </div>
  </div>
</section>


<!-- ═══ HOW IT WORKS ══════════════════════════════════════════════ -->
<section class="how" id="how-it-works">
  <div class="container">
    <div use:reveal style="text-align:center;">
      <span class="section-label">How it works</span>
      <h2 class="section-title" style="margin:0 auto;">From first connection to governed spend<br/>in under an hour.</h2>
      <p class="section-sub" style="margin:14px auto 0;">No professional services. No IT ticket. No onboarding marathon.</p>
    </div>
    <div class="how__steps" use:reveal={{ delay: 100 }}>
      {#each [
        { n:'01', title:'Connect your clouds & tools',  desc:'Read-only IAM role for AWS, service account for GCP, Azure app registration. OAuth for 100+ SaaS tools. 3–4 minutes per provider.' },
        { n:'02', title:'Valdrics maps your inventory', desc:'We build a full registry of every cloud resource and software tool — with costs, teams, and ownership inferred from tags automatically.' },
        { n:'03', title:'Set your governance policies', desc:'Pick from 40+ pre-built templates or write custom rules. Budget limits, vendor lists, DPA requirements — all live in minutes.' },
        { n:'04', title:'Requests flow through the gate',desc:'Every new resource request triggers a policy check and approval workflow. The right approver is notified in Slack with a one-click decision.' },
        { n:'05', title:'Measure governance ROI',       desc:'Every denied request, reclaimed licence, and consolidated tool is tagged to a dollar saving. Share the report with Finance in one click.' },
      ] as step, i}
        <div class="how__step">
          <div class="how__step-num" class:how__step-num--done={i < 2}>{step.n}</div>
          <div class="how__step-connector" class:how__step-connector--done={i < 2}></div>
          <h3 class="how__step-title">{step.title}</h3>
          <p class="how__step-desc">{step.desc}</p>
        </div>
      {/each}
    </div>
  </div>
</section>


<!-- ═══ LIVE GOVERNANCE COUNTER ═══════════════════════════════════ -->
<section class="live-counter">
  <div class="container">
    <div class="live-counter__inner" use:reveal>
      <div class="live-counter__label">
        <span class="live-dot live-dot--jade" aria-hidden="true"></span>
        Across all Valdrics workspaces in the last 24 hours
      </div>
      <div class="live-counter__stats">
        <div class="live-counter__stat">
          <div class="live-counter__val" style="color:var(--jade)">{fmt(decisionsToday)}</div>
          <div class="live-counter__sub">approval decisions made</div>
        </div>
        <div class="live-counter__divider" aria-hidden="true"></div>
        <div class="live-counter__stat">
          <div class="live-counter__val" style="color:var(--ruby)">{fmt(shadowFlagged)}</div>
          <div class="live-counter__sub">shadow IT tools flagged</div>
        </div>
        <div class="live-counter__divider" aria-hidden="true"></div>
        <div class="live-counter__stat">
          <div class="live-counter__val" style="color:var(--ion)">{fmt(violationsCaught)}</div>
          <div class="live-counter__sub">policy violations caught</div>
        </div>
      </div>
    </div>
  </div>
</section>


<!-- ═══ INTEGRATIONS ══════════════════════════════════════════════ -->
<section class="integrations">
  <div class="container">
    <div use:reveal style="text-align:center;">
      <span class="section-label">Integrations</span>
      <h2 class="section-title" style="margin:0 auto;">Governance that lives where your team works.</h2>
      <p class="section-sub" style="margin:14px auto 0;text-align:center;">Connect cloud providers and workflow tools in minutes — no agents, no code.</p>
    </div>
    <div class="integrations__grid" use:reveal={{ delay: 100 }}>
      {#each [
        {logo:'aws.svg', name:'AWS'},
        {logo:'gcp.svg', name:'GCP', col:'var(--ion)'},
        {logo:'azure.svg', name:'Azure', col:'var(--violet)'},
        {logo:'slack.svg', name:'Slack'},
        {logo:'teams.svg', name:'Teams'},
        {logo:'jira.svg', name:'Jira'},
        {logo:'okta.svg', name:'Okta'},
        {logo:'github.svg', name:'GitHub'},
        {logo:'terraform.svg', name:'Terraform'},
        {logo:'pagerduty.svg', name:'PagerDuty'},
        {logo:'datadog.svg', name:'Datadog'},
        {logo:'figma.svg', name:'Figma'},
        {logo:'notion.svg', name:'Notion'},
        {logo:'stripe.svg', name:'Stripe'},
        {logo:'rippling.svg', name:'Rippling'},
        {icon:'＋', name:'+90 more', col:'var(--sub)'},
      ] as t}
        <div class="integ-card">
          {#if t.logo}
            <img
              class="integ-card__logo"
              src={`${base}/service-logos/${t.logo}`}
              alt={`${t.name} logo`}
              loading="lazy"
              decoding="async"
            />
          {:else}
            <span class="integ-card__icon" style={t.col ? `color:${t.col}` : ''}>{t.icon}</span>
          {/if}
          <span class="integ-card__name" style={t.col ? `color:${t.col}` : ''}>{t.name}</span>
        </div>
      {/each}
    </div>
  </div>
</section>


<!-- ═══ TESTIMONIALS ══════════════════════════════════════════════ -->
<section class="testimonials" id="customers">
  <div class="container">
    <div use:reveal>
      <span class="section-label">Customer stories</span>
      <h2 class="section-title">Teams that stopped asking<br/>"who approved this?"</h2>
    </div>
    <div class="testimonials__grid">
      {#each [
        {
          saving:'↓ $41K/mo in first 60 days',
          quote:'We had a $41K software bill with 23 tools nobody could explain. Valdrics surfaced them all in the first week. <strong>Twelve were cancelled immediately.</strong> Finance stopped asking questions they couldn\'t answer.',
          name:'Nana Kofi Asante', role:'VP Engineering', co:'CHIPPER CASH · Series C',
          initials:'NK', color:'linear-gradient(135deg,#00CF7C,#00C2FF)',
        },
        {
          saving:'↑ 96% policy compliance in 30 days',
          quote:'The approval workflow was live in under an hour. We set three policies and <strong>Valdrics enforces them automatically.</strong> Our legal team hasn\'t had to chase a missing DPA since.',
          name:'Ifeoma Adeyemi', role:'Head of Legal & Compliance', co:'MONIEPOINT · Scale-up',
          initials:'IA', color:'linear-gradient(135deg,#9270FF,#F5A623)',
        },
        {
          saving:'→ Finance + Engineering aligned',
          quote:'Every spend decision is now traceable to a person, a justification, and a date. <strong>Our quarterly board review went from 3 hours of cost archaeology to a 20-minute governance report.</strong>',
          name:'Bright Osei', role:'CFO', co:'WAVE MOBILE MONEY · Enterprise',
          initials:'BO', color:'linear-gradient(135deg,#F5A623,#FF3A5C)',
        },
      ] as t, i}
        <article class="tcard" use:reveal={{ delay: i * 80 }}>
          <div class="tcard__saving">{t.saving}</div>
          <blockquote class="tcard__quote">{@html t.quote}</blockquote>
          <footer class="tcard__author">
            <div class="tcard__avatar" style="background:{t.color}">{t.initials}</div>
            <div>
              <div class="tcard__name">{t.name}</div>
              <div class="tcard__role">{t.role}</div>
              <div class="tcard__co">{t.co}</div>
            </div>
          </footer>
        </article>
      {/each}
    </div>
  </div>
</section>


<!-- ═══ COMPARISON ════════════════════════════════════════════════ -->
<section class="comparison">
  <div class="container">
    <div use:reveal>
      <span class="section-label">Why Valdrics</span>
      <h2 class="section-title">The only platform that governs<br/>cloud <em>and</em> software together.</h2>
    </div>
    <div class="comparison__wrap" use:reveal={{ delay: 100 }}>
      <table class="comp-table" aria-label="Feature comparison">
        <thead>
          <tr>
            <th scope="col">Capability</th>
            <th scope="col" class="th--v">VALDRICS</th>
            <th scope="col">Torii / Zylo</th>
            <th scope="col">Cloudability</th>
            <th scope="col">AWS Cost Explorer</th>
          </tr>
        </thead>
        <tbody>
          {#each [
            ['Approval workflows',      '✓ policy-checked',   'Partial — SaaS only',  '✕',  '✕'],
            ['Ownership tracking',      '✓ cloud + SaaS',     'Partial — SaaS only',  '✕',  '✕'],
            ['Policy engine',           '✓ 40+ templates',    'Partial — basic rules', 'Partial','✕'],
            ['Shadow IT detection',     '✓ cloud + SaaS',     '✓ SaaS only',          '✕',  '✕'],
            ['Unified cloud + SaaS',    '✓',                  '✕ SaaS only',          '✕ cloud only','✕ AWS only'],
            ['Proactive governance',    '✓',                  '✕',                    '✕',  '✕'],
            ['Starting price',          '$299/month',         '$$$$ custom',          '$$$$ custom','Free'],
          ] as row}
            <tr>
              <td class="td--feature">{row[0]}</td>
              {#each row.slice(1) as cell, ci}
                <td class:td--v={ci === 0}>
                  {#if cell === '✕'}
                    <span class="c-cross" aria-label="Not available">✕</span>
                  {:else if cell.startsWith('✓')}
                    <span class="c-check" aria-label="Available">{cell}</span>
                  {:else if cell.startsWith('Partial')}
                    <span class="c-partial">{cell}</span>
                  {:else}
                    {cell}
                  {/if}
                </td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
</section>


<!-- ═══ FAQ ═══════════════════════════════════════════════════════ -->
<section class="faq" id="faq" aria-label="Frequently asked questions">
  <div class="container">
    <div use:reveal>
      <span class="section-label">FAQ</span>
      <h2 class="section-title">Governance questions,<br/>answered honestly.</h2>
    </div>
    <div class="faq__grid" use:reveal={{ delay: 80 }}>
      {#each FAQS as faq, i}
        <div
          class="faq__item"
          class:faq__item--open={openFaq === i}
          itemscope
          itemtype="https://schema.org/Question"
        >
          <button
            class="faq__q"
            on:click={() => toggleFaq(i)}
            aria-expanded={openFaq === i}
          >
            <span class="faq__q-text" itemprop="name">{faq.q}</span>
            <svg class="faq__chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
          {#if openFaq === i}
            <div
              class="faq__a"
              transition:fly={{ y: -6, duration: 220 }}
              itemprop="acceptedAnswer"
              itemscope
              itemtype="https://schema.org/Answer"
            >
              <p itemprop="text">{faq.a}</p>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  </div>
</section>


<!-- ═══ PRICING ═══════════════════════════════════════════════════ -->
<section class="pricing" id="pricing">
  <div class="container">
    <div use:reveal style="text-align:center;">
      <span class="section-label">Pricing</span>
      <h2 class="section-title" style="margin:0 auto;">Governance that pays for itself<br/>in the first month.</h2>
      <p class="section-sub" style="margin:14px auto 0;">14-day trial on all plans. No credit card. Cancel any time.</p>
    </div>
    <div class="pricing__grid">
      {#each PRICING as plan, i}
        <article
          class="pcard"
          class:pcard--popular={plan.popular}
          use:reveal={{ delay: i * 80 }}
        >
          {#if plan.popular}
            <div class="pcard__badge">MOST POPULAR</div>
          {/if}
          <div class="pcard__tier" class:pcard__tier--jade={plan.popular}>{plan.tier}</div>
          <div class="pcard__price">
            <span class="pcard__num">{plan.price}</span>
            {#if plan.period}<span class="pcard__per">{plan.period}</span>{/if}
          </div>
          <p class="pcard__desc">{plan.desc}</p>
          <a
            href={plan.ctaHref}
            class="btn btn--full"
            class:btn--jade={plan.popular}
            class:btn--ghost={!plan.popular}
          >
            {plan.cta}
          </a>
          <div class="pcard__divider"></div>
          <ul class="pcard__features">
            {#each plan.features as f}
              <li class="pcard__feature" class:pcard__feature--disabled={typeof f === 'object' && f.disabled}>
                <span class="pcard__check" aria-hidden="true">
                  {typeof f === 'object' && f.disabled ? '—' : '✓'}
                </span>
                {typeof f === 'string' ? f : f.text}
              </li>
            {/each}
          </ul>
        </article>
      {/each}
    </div>
  </div>
</section>


<!-- ═══ TRUST BAR ═════════════════════════════════════════════════ -->
<div class="trust-bar">
  <div class="trust-bar__inner">
    {#each ['SOC 2 Type II','ISO 27001','GDPR Compliant','Read-only access','99.9% uptime SLA','TLS 1.3 · AES-256'] as badge}
      <div class="trust-badge">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        {badge}
      </div>
    {/each}
  </div>
</div>


<!-- ═══ CTA ═══════════════════════════════════════════════════════ -->
<section class="cta">
  <div class="cta__bg" aria-hidden="true">
    <div class="cta__glow"></div>
    <div class="cta__gate"></div>
  </div>
  <div class="container" style="text-align:center;position:relative;z-index:1;">
    <div use:reveal>
      <span class="section-label">Start today</span>
      <h2 class="cta__title">Govern first.<br/>Optimize always.</h2>
      <p class="cta__sub">No credit card. No sales call. No agents to install.<br/>Connect your cloud and your first approval workflow is live in 20 minutes.</p>
      <div class="cta__actions">
        <a href="/auth/login?mode=signup"  class="btn btn--jade btn--lg">Start free — no card needed →</a>
        <a href="/contact" class="btn btn--ghost btn--lg">Book a live demo</a>
      </div>
      <p class="cta__note">14-day trial · SOC 2 certified · Read-only access · Cancel anytime</p>
    </div>
  </div>
</section>


<!-- ═══ FOOTER ════════════════════════════════════════════════════ -->
<footer class="footer">
  <div class="container">
    <div class="footer__top">
      <div class="footer__brand">
        <a href="/" class="nav__logo" aria-label="Valdrics home">
          <div class="nav__mark"><svg width="13" height="13" viewBox="0 0 20 20" fill="none"><path d="M10 2L18 10L10 18L2 10Z" stroke="var(--jade)" stroke-width="1.5" fill="none"/><path d="M6 10L10 6L14 10L10 14Z" fill="rgba(0,207,124,0.2)" stroke="var(--jade)" stroke-width="1"/><circle cx="10" cy="10" r="1.8" fill="var(--jade)"/></svg></div>
          <span>VALDRICS</span>
        </a>
        <p>Cloud and software spend governance for engineering and finance teams. Approval workflows, ownership tracking, and measurable cost optimization — at valdrics.com</p>
      </div>
      {#each [
        { title:'Product',  links:['Features','Pricing','Changelog','Integrations','Roadmap'] },
        { title:'Learn',    links:['Documentation','Blog','Governance Guides','Case Studies','Glossary'] },
        { title:'Company',  links:['About','Careers','Contact','Press','Security'] },
        { title:'Legal',    links:['Privacy Policy','Terms of Service','DPA','Cookie Policy','SLA'] },
      ] as col}
        <div>
          <div class="footer__col-title">{col.title}</div>
          <ul class="footer__links">
            {#each col.links as link}
              <li><a href="/{link.toLowerCase().replace(/\s+/g, '-')}">{link}</a></li>
            {/each}
          </ul>
        </div>
      {/each}
    </div>
    <div class="footer__bottom">
      <span class="footer__copy">© 2026 Valdrics Inc. · valdrics.com · SOC 2 Type II · ISO 27001 · GDPR</span>
      <div class="footer__social" aria-label="Social media links">
        <a href="https://twitter.com/valdrics"            class="social-link" aria-label="Valdrics on Twitter"  rel="noopener">𝕏</a>
        <a href="https://linkedin.com/company/valdrics"   class="social-link" aria-label="Valdrics on LinkedIn" rel="noopener">in</a>
        <a href="https://github.com/valdrics"             class="social-link" aria-label="Valdrics on GitHub"   rel="noopener">gh</a>
      </div>
    </div>
  </div>
</footer>


<style>
/* ─── SCROLL REVEAL ──────────────────────────────────────────── */
:global(.v-hidden)  { opacity:0; transform:translateY(18px); transition:opacity .7s cubic-bezier(.22,1,.36,1), transform .7s cubic-bezier(.22,1,.36,1); }
:global(.v-visible) { opacity:1; transform:none; }

/* ─── LAYOUT ─────────────────────────────────────────────────── */
.container { max-width:1100px; margin:0 auto; padding:0 40px; }
section    { padding:96px 40px; }

/* ─── TYPOGRAPHY ─────────────────────────────────────────────── */
.section-label { font-family:var(--font-mono); font-size:11px; letter-spacing:.13em; color:var(--jade); text-transform:uppercase; display:block; margin-bottom:12px; }
.section-title { font-family:var(--font-display); font-weight:800; font-size:clamp(28px,4vw,48px); color:var(--white); line-height:1.07; letter-spacing:-.02em; }
.section-sub   { font-size:16px; color:var(--sub); max-width:520px; margin-top:14px; line-height:1.7; }

/* ─── BUTTONS ────────────────────────────────────────────────── */
.btn         { display:inline-flex; align-items:center; gap:6px; padding:10px 22px; border-radius:10px; font-size:14px; font-family:var(--font-body); font-weight:600; cursor:pointer; border:1px solid transparent; text-decoration:none; transition:all .18s ease; }
.btn--sm     { padding:8px 16px; font-size:13px; border-radius:9px; }
.btn--lg     { padding:14px 28px; font-size:15px; border-radius:12px; }
.btn--full   { width:100%; justify-content:center; }
.btn--jade   { background:var(--jade); color:#030912; box-shadow:0 0 20px rgba(0,207,124,.25); border-color:var(--jade); }
.btn--jade:hover { background:#11e888; box-shadow:0 0 32px rgba(0,207,124,.4); transform:translateY(-1px); }
.btn--ghost  { background:transparent; color:var(--sub); border-color:var(--bdr); }
.btn--ghost:hover { color:var(--text); border-color:var(--bdr-hi); background:var(--s1); }

/* ─── NAV ────────────────────────────────────────────────────── */
.nav { position:fixed; top:0; left:0; right:0; z-index:100; padding:0 40px; height:64px; display:flex; align-items:center; background:rgba(3,9,18,.0); backdrop-filter:blur(0); border-bottom:1px solid transparent; transition:all .3s ease; }
.nav--scrolled { background:rgba(3,9,18,.93); backdrop-filter:blur(14px); border-bottom-color:var(--bdr); }
.nav__inner { display:flex; align-items:center; width:100%; gap:32px; }
.nav__logo  { display:flex; align-items:center; gap:9px; font-family:var(--font-display); font-weight:700; font-size:15px; color:var(--white); letter-spacing:.08em; text-decoration:none; }
.nav__mark  { width:30px; height:30px; border-radius:8px; background:rgba(0,207,124,.1); border:1px solid rgba(0,207,124,.25); display:flex; align-items:center; justify-content:center; }
.nav__links { display:flex; align-items:center; gap:26px; list-style:none; margin-left:auto; }
.nav__links a { font-size:13px; color:var(--sub); text-decoration:none; transition:color .15s; }
.nav__links a:hover { color:var(--text); }
.nav__actions { display:flex; align-items:center; gap:10px; }
.nav__burger  { display:none; flex-direction:column; gap:5px; background:none; border:none; cursor:pointer; padding:6px; }
.nav__burger span { display:block; width:22px; height:2px; background:var(--sub); border-radius:1px; }
.nav__mobile { display:flex; flex-direction:column; gap:6px; padding:20px 24px; background:var(--base); border-bottom:1px solid var(--bdr); }
.nav__mobile a { font-size:14px; color:var(--sub); text-decoration:none; padding:6px 0; border-bottom:1px solid var(--bdr); }
.nav__mobile-actions { display:flex; gap:10px; margin-top:8px; padding-top:8px; }

/* ─── HERO ───────────────────────────────────────────────────── */
.hero { min-height:100vh; display:flex; flex-direction:column; justify-content:center; padding:120px 40px 80px; position:relative; overflow:hidden; }
.hero__bg { position:absolute; inset:0; z-index:0; pointer-events:none; }
.hero__grid { position:absolute; inset:0; background-image:linear-gradient(rgba(0,207,124,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(0,207,124,.04) 1px,transparent 1px); background-size:54px 54px; mask-image:radial-gradient(ellipse 80% 80% at 50% 40%,black 30%,transparent 100%); }
.hero__orb { position:absolute; border-radius:50%; filter:blur(80px); animation:orb 14s ease-in-out infinite; }
.hero__orb--1 { width:500px; height:500px; background:radial-gradient(circle,rgba(0,207,124,.1),transparent 70%); top:-80px; left:30%; animation-duration:16s; }
.hero__orb--2 { width:400px; height:400px; background:radial-gradient(circle,rgba(0,194,255,.08),transparent 70%); bottom:0; right:-80px; animation-duration:18s; animation-delay:-7s; }
.hero__orb--3 { width:300px; height:300px; background:radial-gradient(circle,rgba(146,112,255,.07),transparent 70%); top:40%; left:-60px; animation-duration:20s; animation-delay:-4s; }
.hero__gate { position:absolute; top:0; bottom:0; left:50%; width:1px; background:linear-gradient(to bottom,transparent,rgba(0,207,124,.3) 20%,rgba(0,207,124,.3) 80%,transparent); transform-origin:top; animation:lineGrow 1.4s cubic-bezier(.22,1,.36,1) .4s both; }
@keyframes orb { 0%,100%{transform:scale(1) translate(0,0)} 50%{transform:scale(1.06) translate(-16px,12px)} }
@keyframes lineGrow { from{transform:scaleY(0)} to{transform:scaleY(1)} }

.hero__inner { display:grid; grid-template-columns:1fr 1fr; gap:64px; align-items:center; max-width:1100px; margin:0 auto; width:100%; position:relative; z-index:1; }
.hero__badge { display:inline-flex; align-items:center; gap:7px; padding:5px 13px; border-radius:100px; background:rgba(0,207,124,.1); border:1px solid rgba(0,207,124,.2); font-family:var(--font-mono); font-size:11px; color:var(--jade); letter-spacing:.07em; margin-bottom:24px; animation:fadeUp .6s cubic-bezier(.22,1,.36,1) .2s both; }
.hero__badge-dot { width:6px; height:6px; border-radius:50%; background:var(--jade); animation:pulseDot 1.8s ease-in-out infinite; }
@keyframes fadeUp { from{opacity:0;transform:translateY(18px)} to{opacity:1;transform:none} }
@keyframes pulseDot { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.3;transform:scale(.6)} }

.hero__headline { font-family:var(--font-display); font-weight:800; font-size:clamp(48px,6vw,82px); line-height:1.0; letter-spacing:-.03em; animation:fadeUp .7s cubic-bezier(.22,1,.36,1) .35s both; }
.hero__headline-line { display:block; color:var(--white); }
.hero__headline-line--accent { color:var(--jade); }
.hero__headline-line--dim    { color:var(--sub); }
.hero__sub  { font-size:16px; color:var(--sub); line-height:1.7; margin-top:20px; max-width:460px; animation:fadeUp .7s cubic-bezier(.22,1,.36,1) .5s both; }
.hero__actions { display:flex; align-items:center; gap:12px; margin-top:32px; flex-wrap:wrap; animation:fadeUp .7s cubic-bezier(.22,1,.36,1) .65s both; }
.hero__chips  { display:flex; align-items:center; gap:9px; margin-top:24px; flex-wrap:wrap; animation:fadeUp .7s cubic-bezier(.22,1,.36,1) .8s both; }

/* ─── HERO PREVIEW ───────────────────────────────────────────── */
.hero__preview { display:flex; flex-direction:column; gap:12px; animation:fadeUp .9s cubic-bezier(.22,1,.36,1) 1s both; }
.hero__preview-label { font-family:var(--font-mono); font-size:10px; color:var(--sub); letter-spacing:.1em; text-transform:uppercase; display:flex; align-items:center; gap:6px; margin-bottom:2px; }
.live-dot { width:6px; height:6px; border-radius:50%; background:var(--jade); animation:pulseDot 1.5s ease-in-out infinite; display:inline-block; }
.live-dot--jade { background:var(--jade); }

.hero-card { display:flex; align-items:center; gap:12px; background:var(--s1); border:1px solid var(--bdr); border-radius:12px; padding:13px 14px; transition:border-color .3s; }
.hero-card--ghost    { opacity:.45; transform:scale(.97); margin-top:-4px; }
.hero-card--approved { border-color:rgba(0,207,124,.3); background:rgba(0,207,124,.05); }
.hero-card--denied   { border-color:rgba(255,58,92,.25); background:rgba(255,58,92,.04); }
.hero-card__stripe { width:3px; height:36px; border-radius:2px; flex-shrink:0; }
.hero-card__stripe--amber  { background:var(--amber); }
.hero-card__stripe--jade   { background:var(--jade); }
.hero-card__stripe--ruby   { background:var(--ruby); }
.hero-card__stripe--violet { background:var(--violet); }
.hero-card__body { flex:1; min-width:0; }
.hero-card__top  { display:flex; align-items:center; gap:7px; margin-bottom:5px; flex-wrap:wrap; }
.hero-card__name { font-size:12px; font-weight:600; color:var(--white); }
.hero-card__policies { display:flex; gap:5px; margin-bottom:4px; }
.hero-card__meta { font-size:10px; color:var(--sub); }
.hero-card__cost { text-align:right; flex-shrink:0; }
.hero-card__cost-val   { font-family:var(--font-display); font-weight:700; font-size:14px; color:var(--amber); }
.hero-card__cost-label { font-size:9px; color:var(--sub); font-family:var(--font-mono); letter-spacing:.07em; text-transform:uppercase; margin-top:2px; }
.hero-card__actions { display:flex; gap:5px; margin-top:6px; justify-content:flex-end; }
.hero-card__decision { font-size:10px; font-family:var(--font-mono); margin-top:5px; }
.hero-card__decision--approved { color:var(--jade); }
.hero-card__decision--denied   { color:var(--ruby);  }
.btn-approve,.btn-deny { width:24px; height:24px; border-radius:6px; border:1px solid; display:flex; align-items:center; justify-content:center; font-size:11px; cursor:pointer; background:none; }
.btn-approve { color:var(--jade); border-color:rgba(0,207,124,.3); background:rgba(0,207,124,.1); }
.btn-deny    { color:var(--ruby); border-color:rgba(255,58,92,.3);  background:rgba(255,58,92,.1); }

.hero__health { display:flex; align-items:center; gap:12px; padding:10px 14px; background:var(--s1); border:1px solid var(--bdr); border-radius:10px; }
.hero__health-ring { position:relative; width:52px; height:52px; flex-shrink:0; }
.hero__health-score { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-family:var(--font-display); font-weight:700; font-size:13px; color:var(--jade); }
.hero__health-label { font-family:var(--font-mono); font-size:9px; color:var(--sub); letter-spacing:.08em; text-transform:uppercase; }
.hero__health-sub   { font-size:11px; color:var(--jade); margin-top:2px; }

/* Tags / chips used in hero cards */
.tag           { display:inline-flex; align-items:center; padding:2px 6px; border-radius:4px; font-family:var(--font-mono); font-size:9px; font-weight:700; letter-spacing:.06em; }
.tag--cloud    { background:rgba(0,194,255,.1); color:var(--ion); }
.tag--software { background:rgba(146,112,255,.1); color:var(--violet); }
.tag--critical { background:rgba(255,58,92,.1); color:var(--ruby); }
.tag--approved { background:rgba(0,207,124,.1); color:var(--jade); }
.tag--denied   { background:rgba(255,58,92,.1); color:var(--ruby); }
.chip { display:flex; align-items:center; gap:5px; padding:5px 11px; border-radius:100px; background:var(--s1); border:1px solid var(--bdr); font-size:12px; color:var(--sub); }
.chip strong { color:var(--white); font-family:var(--font-display); font-size:13px; }
.policy-tag { display:inline-flex; align-items:center; padding:2px 6px; border-radius:4px; font-size:9px; font-family:var(--font-mono); font-weight:600; }
.policy-tag--warn { background:rgba(245,166,35,.1); color:var(--amber); }
.policy-tag--pass { background:rgba(0,207,124,.1); color:var(--jade); }

/* ─── TICKER ─────────────────────────────────────────────────── */
.ticker { overflow:hidden; padding:16px 0; border-top:1px solid var(--bdr); border-bottom:1px solid var(--bdr); background:var(--base); position:relative; }
.ticker::before,.ticker::after { content:''; position:absolute; top:0; bottom:0; width:100px; z-index:2; }
.ticker::before { left:0;  background:linear-gradient(to right,var(--base),transparent); }
.ticker::after  { right:0; background:linear-gradient(to left,var(--base),transparent);  }
.ticker__track  { display:flex; width:max-content; animation:ticker 32s linear infinite; }
.ticker__item   { display:flex; align-items:center; gap:9px; padding:0 30px; white-space:nowrap; font-family:var(--font-mono); font-size:13px; color:var(--sub); border-right:1px solid var(--bdr); }
.ticker__item strong { color:var(--white); }
.tdot { width:5px; height:5px; border-radius:50%; background:var(--jade); flex-shrink:0; }
@keyframes ticker { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }

/* ─── PROBLEM ────────────────────────────────────────────────── */
.problem { background:var(--base); }
.problem__gate { display:grid; grid-template-columns:1fr 40px 1fr; gap:0; border-radius:18px; overflow:hidden; border:1px solid var(--bdr); margin-top:52px; }
.problem__side { padding:40px 36px; }
.problem__side--chaos   { background:rgba(255,58,92,.04); }
.problem__side--clarity { background:rgba(0,207,124,.05); }
.problem__gate-line { display:flex; flex-direction:column; align-items:center; justify-content:center; background:var(--void); position:relative; }
.gate-glow  { width:1px; flex:1; background:linear-gradient(to bottom,transparent,var(--jade) 30%,var(--jade) 70%,transparent); box-shadow:0 0 12px rgba(0,207,124,.4); }
.gate-label { writing-mode:vertical-lr; font-family:var(--font-mono); font-size:8px; color:var(--jade); letter-spacing:.15em; text-transform:uppercase; padding:8px 0; }
.side-label { font-family:var(--font-mono); font-size:11px; letter-spacing:.1em; text-transform:uppercase; display:flex; align-items:center; gap:7px; margin-bottom:20px; }
.side-label--bad  { color:var(--ruby); }
.side-label--good { color:var(--jade); }
.problem__list { list-style:none; display:flex; flex-direction:column; gap:12px; font-size:14px; color:var(--sub); line-height:1.65; }
.problem__list li::before { content:'→ '; color:var(--muted); }

/* ─── FEATURES ───────────────────────────────────────────────── */
.features { background:var(--void); }
.features__grid { display:grid; grid-template-columns:1.4fr 1fr; gap:14px; margin-top:52px; }
.features__grid--flipped { grid-template-columns:1fr 1.4fr; }
.fcard__col { display:flex; flex-direction:column; gap:14px; }
.fcard { background:var(--s1); border:1px solid var(--bdr); border-radius:16px; padding:28px; transition:border-color .2s,transform .2s; position:relative; overflow:hidden; }
.fcard::before { content:''; position:absolute; top:0; left:0; right:0; height:1px; opacity:0; transition:opacity .3s; }
.fcard:hover { border-color:var(--bdr-hi); transform:translateY(-2px); }
.fcard:hover::before { opacity:1; }
.fcard--large { padding:32px; }
.fcard--jade::before   { background:linear-gradient(to right,transparent,var(--jade),transparent); }
.fcard--ion::before    { background:linear-gradient(to right,transparent,var(--ion),transparent); }
.fcard--violet::before { background:linear-gradient(to right,transparent,var(--violet),transparent); }
.fcard--ruby::before   { background:linear-gradient(to right,transparent,var(--ruby),transparent); }
.fcard--amber::before  { background:linear-gradient(to right,transparent,var(--amber),transparent); }
.fcard__icon { width:42px; height:42px; border-radius:11px; display:flex; align-items:center; justify-content:center; margin-bottom:16px; }
.fcard__icon--jade   { background:rgba(0,207,124,.1); border:1px solid rgba(0,207,124,.2); color:var(--jade);   }
.fcard__icon--ion    { background:rgba(0,194,255,.1); border:1px solid rgba(0,194,255,.2); color:var(--ion);    }
.fcard__icon--violet { background:rgba(146,112,255,.1); border:1px solid rgba(146,112,255,.2); color:var(--violet); }
.fcard__icon--ruby   { background:rgba(255,58,92,.1); border:1px solid rgba(255,58,92,.2); color:var(--ruby);   }
.fcard__icon--amber  { background:rgba(245,166,35,.1); border:1px solid rgba(245,166,35,.2); color:var(--amber); }
.fcard__title { font-family:var(--font-display); font-weight:700; font-size:18px; color:var(--white); margin-bottom:9px; }
.fcard__desc  { font-size:13px; color:var(--sub); line-height:1.7; }
.fcard__stat  { margin-top:20px; padding-top:16px; border-top:1px solid var(--bdr); display:flex; align-items:baseline; gap:8px; }
.fcard__stat-val   { font-family:var(--font-display); font-weight:700; font-size:22px; }
.fcard__stat-label { font-size:12px; color:var(--sub); }

/* Feature illustration elements */
.fcard__illustration { margin:16px 0; border-radius:9px; background:var(--s2); padding:12px; }
.mini-card { display:flex; align-items:center; gap:10px; padding:9px 10px; background:var(--s3); border-radius:8px; border:1px solid var(--bdr); margin-bottom:8px; }
.mini-card__stripe { width:3px; height:28px; border-radius:2px; flex-shrink:0; }
.mini-card__stripe--ruby   { background:var(--ruby);   animation:pulseDot 1.8s ease-in-out infinite; }
.mini-card__content { flex:1; min-width:0; }
.mini-card__name { font-size:11px; color:var(--white); font-weight:600; }
.mini-card__right { text-align:right; }
.mini-card__cost { font-family:var(--font-display); font-size:13px; font-weight:700; color:var(--amber); }
.mini-card__btns { display:flex; gap:4px; justify-content:flex-end; margin-top:4px; }
.mini-tag { display:inline-flex; padding:2px 5px; border-radius:3px; font-family:var(--font-mono); font-size:8px; font-weight:700; letter-spacing:.05em; margin-bottom:3px; }
.mini-tag--cloud { background:rgba(0,194,255,.12); color:var(--ion); }
.mini-btn { width:20px; height:20px; border-radius:5px; display:inline-flex; align-items:center; justify-content:center; font-size:10px; }
.mini-btn--approve { background:rgba(0,207,124,.15); color:var(--jade); }
.mini-btn--deny    { background:rgba(255,58,92,.12);  color:var(--ruby); }
.policy-chips { display:flex; gap:5px; flex-wrap:wrap; }
.policy-chip { display:inline-flex; align-items:center; padding:3px 8px; border-radius:4px; font-family:var(--font-mono); font-size:10px; font-weight:600; }
.policy-chip--pass { background:rgba(0,207,124,.1); color:var(--jade); }
.policy-chip--fail { background:rgba(255,58,92,.1); color:var(--ruby); }
.policy-chip--warn { background:rgba(245,166,35,.1); color:var(--amber); }
.topology-legend { display:flex; gap:14px; margin-top:8px; }
.topology-legend span { display:flex; align-items:center; gap:5px; font-size:10px; color:var(--sub); }
.topology-legend i { width:12px; height:3px; border-radius:2px; display:inline-block; }

/* ─── HOW IT WORKS ───────────────────────────────────────────── */
.how { background:var(--base); }
.how__steps { display:grid; grid-template-columns:repeat(5,1fr); gap:0; margin-top:60px; position:relative; }
.how__steps::after { content:''; position:absolute; top:30px; left:10%; right:10%; height:1px; background:linear-gradient(to right,var(--bdr),var(--jade) 25%,var(--ion) 50%,var(--violet) 75%,var(--bdr)); }
.how__step { padding:0 16px; text-align:center; position:relative; z-index:1; }
.how__step-num { width:60px; height:60px; border-radius:50%; border:1px solid var(--bdr); background:var(--s1); display:flex; align-items:center; justify-content:center; margin:0 auto 16px; font-family:var(--font-mono); font-size:12px; color:var(--sub); transition:border-color .25s,color .25s; }
.how__step-num--done { border-color:var(--jade); color:var(--jade); }
.how__step:hover .how__step-num { border-color:var(--jade); color:var(--jade); }
.how__step-connector { display:none; }
.how__step-title { font-family:var(--font-display); font-weight:700; font-size:13px; color:var(--white); margin-bottom:6px; }
.how__step-desc  { font-size:12px; color:var(--sub); line-height:1.6; }

/* ─── LIVE COUNTER ───────────────────────────────────────────── */
.live-counter { background:var(--s1); border-top:1px solid var(--bdr); border-bottom:1px solid var(--bdr); padding:48px 40px; }
.live-counter__inner { max-width:1100px; margin:0 auto; }
.live-counter__label { display:flex; align-items:center; gap:8px; font-family:var(--font-mono); font-size:11px; color:var(--sub); letter-spacing:.08em; text-transform:uppercase; margin-bottom:32px; justify-content:center; }
.live-counter__stats { display:grid; grid-template-columns:1fr auto 1fr auto 1fr; gap:0; align-items:center; }
.live-counter__stat  { text-align:center; }
.live-counter__val   { font-family:var(--font-display); font-weight:800; font-size:clamp(36px,5vw,60px); line-height:1; letter-spacing:-.03em; }
.live-counter__sub   { font-size:13px; color:var(--sub); margin-top:6px; }
.live-counter__divider { width:1px; height:60px; background:var(--bdr); }

/* ─── INTEGRATIONS ───────────────────────────────────────────── */
.integrations { background:var(--void); }
.integrations__grid { display:grid; grid-template-columns:repeat(8,1fr); gap:10px; margin-top:44px; }
.integ-card { padding:14px 8px; border-radius:11px; border:1px solid var(--bdr); background:var(--s1); text-align:center; display:flex; flex-direction:column; align-items:center; gap:5px; transition:border-color .2s,transform .2s; }
.integ-card:hover { border-color:var(--bdr-hi); transform:translateY(-2px); }
.integ-card__icon { font-size:20px; }
.integ-card__logo { width:20px; height:20px; object-fit:contain; }
.integ-card__name { font-size:10px; color:var(--sub); font-family:var(--font-mono); letter-spacing:.04em; }

/* ─── TESTIMONIALS ───────────────────────────────────────────── */
.testimonials { background:var(--base); }
.testimonials__grid { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-top:52px; }
.tcard { background:var(--s1); border:1px solid var(--bdr); border-radius:16px; padding:28px; display:flex; flex-direction:column; gap:18px; transition:border-color .2s; position:relative; overflow:hidden; }
.tcard::before { content:'\201C'; position:absolute; top:12px; right:18px; font-family:var(--font-display); font-size:72px; line-height:1; color:rgba(0,207,124,.06); pointer-events:none; }
.tcard:hover { border-color:var(--bdr-hi); }
.tcard__saving { display:inline-flex; align-items:center; padding:4px 10px; border-radius:6px; background:rgba(0,207,124,.1); border:1px solid rgba(0,207,124,.2); font-family:var(--font-mono); font-size:11px; color:var(--jade); font-weight:600; align-self:flex-start; }
.tcard__quote { font-size:14px; line-height:1.75; color:var(--text); flex:1; font-style:italic; }
.tcard__author { display:flex; align-items:center; gap:12px; padding-top:16px; border-top:1px solid var(--bdr); }
.tcard__avatar { width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-family:var(--font-display); font-weight:700; font-size:13px; color:#fff; flex-shrink:0; }
.tcard__name { font-size:13px; font-weight:600; color:var(--white); }
.tcard__role { font-size:12px; color:var(--sub); }
.tcard__co   { font-size:11px; color:var(--jade); font-family:var(--font-mono); margin-top:2px; }

/* ─── COMPARISON ─────────────────────────────────────────────── */
.comparison { background:var(--void); }
.comparison__wrap { overflow-x:auto; margin-top:48px; }
.comp-table { width:100%; border-collapse:separate; border-spacing:0; border:1px solid var(--bdr); border-radius:14px; overflow:hidden; font-size:13px; }
.comp-table th { padding:13px 16px; background:var(--s2); font-family:var(--font-display); font-weight:600; font-size:13px; color:var(--sub); border-bottom:1px solid var(--bdr); text-align:left; }
.th--v { color:var(--jade); background:rgba(0,207,124,.05); }
.comp-table td { padding:12px 16px; border-bottom:1px solid var(--bdr); color:var(--sub); vertical-align:middle; }
.comp-table tr:last-child td { border-bottom:none; }
.comp-table tr:hover td { background:rgba(255,255,255,.012); }
.td--feature { color:var(--text); font-weight:500; }
.td--v { background:rgba(0,207,124,.04); color:var(--white); font-weight:500; }
.c-check { color:var(--jade); }
.c-cross { color:var(--muted); }
.c-partial { color:var(--amber); font-size:12px; font-family:var(--font-mono); }

/* ─── FAQ ────────────────────────────────────────────────────── */
.faq { background:var(--base); }
.faq__grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:48px; }
.faq__item { background:var(--s1); border:1px solid var(--bdr); border-radius:12px; overflow:hidden; transition:border-color .2s; }
.faq__item:hover,.faq__item--open { border-color:var(--bdr-hi); }
.faq__item--open { border-color:rgba(0,207,124,.3); }
.faq__q { width:100%; display:flex; align-items:center; justify-content:space-between; gap:14px; padding:17px 19px; background:none; border:none; cursor:pointer; text-align:left; }
.faq__q-text { font-size:14px; font-weight:600; color:var(--white); line-height:1.5; }
.faq__chevron { width:18px; height:18px; flex-shrink:0; color:var(--sub); transition:transform .25s,color .2s; }
.faq__item--open .faq__chevron { transform:rotate(180deg); color:var(--jade); }
.faq__a { padding:0 19px 16px; border-top:1px solid var(--bdr); padding-top:14px; }
.faq__a p { font-size:13px; color:var(--sub); line-height:1.75; }

/* ─── PRICING ────────────────────────────────────────────────── */
.pricing { background:var(--void); }
.pricing__grid { display:grid; grid-template-columns:repeat(3,1fr); gap:18px; margin-top:56px; }
.pcard { background:var(--s1); border:1px solid var(--bdr); border-radius:18px; padding:32px; position:relative; transition:border-color .2s,transform .2s; }
.pcard:hover { border-color:var(--bdr-hi); transform:translateY(-2px); }
.pcard--popular { border-color:rgba(0,207,124,.35); background:var(--s2); box-shadow:0 0 60px rgba(0,207,124,.07); }
.pcard__badge { position:absolute; top:-13px; left:50%; transform:translateX(-50%); padding:5px 16px; border-radius:100px; background:var(--jade); color:#030912; font-family:var(--font-display); font-size:11px; font-weight:700; letter-spacing:.06em; white-space:nowrap; }
.pcard__tier  { font-family:var(--font-mono); font-size:11px; letter-spacing:.1em; color:var(--sub); margin-bottom:13px; text-transform:uppercase; }
.pcard__tier--jade { color:var(--jade); }
.pcard__price { display:flex; align-items:baseline; gap:4px; margin-bottom:7px; }
.pcard__num   { font-family:var(--font-display); font-weight:800; font-size:38px; color:var(--white); line-height:1; }
.pcard__per   { font-size:14px; color:var(--sub); }
.pcard__desc  { font-size:13px; color:var(--sub); margin-bottom:22px; line-height:1.6; }
.pcard__divider { height:1px; background:var(--bdr); margin:20px 0; }
.pcard__features { list-style:none; display:flex; flex-direction:column; gap:10px; margin-bottom:24px; }
.pcard__feature { display:flex; align-items:center; gap:9px; font-size:13px; color:var(--sub); }
.pcard__feature--disabled { color:var(--muted); }
.pcard__check { font-size:14px; color:var(--jade); flex-shrink:0; }
.pcard__feature--disabled .pcard__check { color:var(--muted); }

/* ─── TRUST BAR ──────────────────────────────────────────────── */
.trust-bar { padding:28px 40px; background:var(--base); border-top:1px solid var(--bdr); border-bottom:1px solid var(--bdr); }
.trust-bar__inner { display:flex; align-items:center; justify-content:center; gap:28px; flex-wrap:wrap; max-width:1100px; margin:0 auto; }
.trust-badge { display:flex; align-items:center; gap:7px; font-size:12px; color:var(--sub); }

/* ─── CTA ────────────────────────────────────────────────────── */
.cta { padding:112px 40px; position:relative; overflow:hidden; background:var(--void); }
.cta__bg { position:absolute; inset:0; pointer-events:none; }
.cta__glow { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:600px; height:600px; border-radius:50%; background:radial-gradient(circle,rgba(0,207,124,.07),transparent 70%); }
.cta__gate { position:absolute; top:0; bottom:0; left:50%; width:1px; background:linear-gradient(to bottom,transparent,rgba(0,207,124,.2) 30%,rgba(0,207,124,.2) 70%,transparent); }
.cta__title { font-family:var(--font-display); font-weight:800; font-size:clamp(36px,5vw,66px); color:var(--white); line-height:1.05; letter-spacing:-.02em; margin-bottom:18px; }
.cta__sub    { font-size:16px; color:var(--sub); max-width:420px; margin:0 auto 36px; line-height:1.7; }
.cta__actions { display:flex; align-items:center; justify-content:center; gap:14px; flex-wrap:wrap; }
.cta__note   { font-family:var(--font-mono); font-size:12px; color:var(--muted); margin-top:16px; }

/* ─── FOOTER ─────────────────────────────────────────────────── */
.footer { padding:48px 40px; background:var(--base); border-top:1px solid var(--bdr); }
.footer__top { display:grid; grid-template-columns:2fr 1fr 1fr 1fr 1fr; gap:40px; margin-bottom:40px; }
.footer__brand p { font-size:13px; color:var(--sub); margin-top:12px; max-width:240px; line-height:1.7; }
.footer__col-title { font-family:var(--font-display); font-weight:700; font-size:11px; letter-spacing:.06em; color:var(--white); margin-bottom:14px; text-transform:uppercase; }
.footer__links { list-style:none; display:flex; flex-direction:column; gap:9px; }
.footer__links a { font-size:13px; color:var(--sub); text-decoration:none; transition:color .15s; }
.footer__links a:hover { color:var(--text); }
.footer__bottom { display:flex; align-items:center; justify-content:space-between; padding-top:28px; border-top:1px solid var(--bdr); flex-wrap:wrap; gap:14px; }
.footer__copy   { font-family:var(--font-mono); font-size:12px; color:var(--muted); }
.footer__social { display:flex; gap:12px; }
.social-link { width:30px; height:30px; border-radius:8px; border:1px solid var(--bdr); display:flex; align-items:center; justify-content:center; color:var(--sub); text-decoration:none; font-size:12px; font-weight:600; transition:all .15s; }
.social-link:hover { border-color:var(--bdr-hi); color:var(--text); background:var(--s1); }

/* ─── RESPONSIVE ─────────────────────────────────────────────── */
@media (max-width: 900px) {
  section { padding:72px 24px; }
  .container { padding:0 24px; }
  .hero__inner { grid-template-columns:1fr; }
  .hero__preview { display:none; }
  .hero { min-height:auto; padding:100px 24px 64px; }
  .features__grid,.features__grid--flipped { grid-template-columns:1fr; }
  .fcard__col { display:contents; }
  .how__steps { grid-template-columns:1fr 1fr; gap:24px; }
  .how__steps::after { display:none; }
  .testimonials__grid,.pricing__grid { grid-template-columns:1fr; }
  .faq__grid { grid-template-columns:1fr; }
  .integrations__grid { grid-template-columns:repeat(4,1fr); }
  .footer__top { grid-template-columns:1fr 1fr; }
  .live-counter__stats { grid-template-columns:1fr; gap:24px; }
  .live-counter__divider { display:none; }
  .problem__gate { grid-template-columns:1fr; }
  .problem__gate-line { display:none; }
  .nav__links,.nav__actions { display:none; }
  .nav__burger { display:flex; }
  .nav { padding:0 24px; }
}

@media (max-width: 600px) {
  .footer__top { grid-template-columns:1fr; }
  .comp-table { font-size:12px; }
  .integrations__grid { grid-template-columns:repeat(3,1fr); }
}
</style>
