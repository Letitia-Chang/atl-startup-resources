// src/index.tsx
var e = {
	lastChecked: "2026-11-13",
	categories: [
		"Accelerators & Incubators",
		"Georgia Tech Programs",
		"Funding & Investors",
		"Coworking & Hubs",
		"Events",
		"News & Community"
	],
	stages: [
		"Idea",
		"Pre-seed",
		"Seed",
		"Growth",
		"Small business"
	],
	resources: [
		{
			id: "atdc",
			name: "ATDC",
			category: "Accelerators & Incubators",
			stage: [
				"Idea",
				"Pre-seed",
				"Seed"
			],
			area: "Midtown / Tech Square",
			description: "Georgia Tech's statewide startup incubator. Tiered programs (Educate, Accelerate, Signature) plus industry tracks, mentors, funding and corporate pilot connections.",
			url: "https://atdc.org"
		},
		{
			id: "engage",
			name: "Engage",
			category: "Accelerators & Incubators",
			stage: ["Seed", "Growth"],
			area: "Atlanta",
			description: "Corporate-backed platform (Delta, Coca-Cola, The Home Depot and others) with a 10-week Enterprise Accelerator that runs each spring and fall.",
			url: "https://engage.vc"
		},
		{
			id: "cox-cleantech",
			name: "Cox Cleantech Accelerator",
			category: "Accelerators & Incubators",
			stage: ["Pre-seed", "Seed"],
			area: "Atlanta",
			description: "12-week cleantech program run with gener8tor and the Georgia Cleantech Innovation Hub; $250K investment per startup. Also runs an equity-free Residency.",
			url: "https://www.gener8tor.com/cox"
		},
		{
			id: "founder-institute",
			name: "Founder Institute Atlanta",
			category: "Accelerators & Incubators",
			stage: ["Idea"],
			area: "Virtual",
			description: "Idea-stage pre-accelerator chapter for Atlanta founders. Runs fully virtual and charges an entrance fee.",
			url: "https://fi.co/atlanta"
		},
		{
			id: "create-x",
			name: "CREATE-X Startup Launch",
			category: "Georgia Tech Programs",
			stage: ["Idea", "Pre-seed"],
			area: "Georgia Tech",
			description: "12-week summer program for GT students, faculty, researchers and alumni: $5K seed funding, ~$30K in-kind services, 24/7 coworking and Demo Day.",
			url: "https://create-x.gatech.edu/launch/startup-launch"
		},
		{
			id: "quadrant-i",
			name: "Quadrant-i",
			category: "Georgia Tech Programs",
			stage: ["Idea"],
			area: "Georgia Tech",
			description: "GT unit that helps faculty, researchers and grad students turn research into startups. Its Startup Launch section includes a $10K commercialization grant.",
			url: "https://quadrant-i.gatech.edu"
		},
		{
			id: "venturelab",
			name: "VentureLab",
			category: "Georgia Tech Programs",
			stage: ["Idea"],
			area: "Georgia Tech",
			description: "GT's commercialization teaching and training unit for faculty and students. No charge and no equity taken.",
			url: "https://venturelab.gatech.edu"
		},
		{
			id: "gra",
			name: "Georgia Research Alliance",
			category: "Funding & Investors",
			stage: ["Idea", "Pre-seed"],
			area: "Statewide",
			description: "Innovation & Entrepreneurship grants ($10K–$250K) and startup loans for companies built on Georgia university technology.",
			url: "https://gra.org"
		},
		{
			id: "invest-atlanta",
			name: "Invest Atlanta – Startup Growth Loan",
			category: "Funding & Investors",
			stage: ["Seed", "Small business"],
			area: "City of Atlanta",
			description: "City economic development agency. Its Atlanta Startup Growth Loan Program offers direct loans up to $150K to tech startups in the city, alongside other small business loans.",
			url: "https://www.investatlanta.com/businesses/small-businesses/atlanta-startup-growth-program"
		},
		{
			id: "atlanta-ventures",
			name: "Atlanta Ventures",
			category: "Funding & Investors",
			stage: ["Pre-seed", "Seed"],
			area: "Atlanta",
			description: "Venture studio and early-stage fund. Free founder resources include office hours and monthly pitch practice.",
			url: "https://atlantaventures.com"
		},
		{
			id: "atv",
			name: "Atlanta Tech Village",
			category: "Coworking & Hubs",
			stage: [
				"Idea",
				"Pre-seed",
				"Seed",
				"Growth"
			],
			area: "Buckhead + 3 other locations",
			description: "Startup hub at 3423 Piedmont Rd NE. Programs include Women + Tech, It Takes A Village, Startup Summer School and Atlanta Startup Village.",
			url: "https://atlantatechvillage.com"
		},
		{
			id: "switchyards",
			name: "Switchyards",
			category: "Coworking & Hubs",
			stage: [
				"Idea",
				"Pre-seed",
				"Seed",
				"Small business"
			],
			area: "12 metro Atlanta clubs",
			description: "Membership work club. $100/mo on an annual plan or $129/mo month-to-month for access to every club.",
			url: "https://www.switchyards.com"
		},
		{
			id: "roam",
			name: "Roam",
			category: "Coworking & Hubs",
			stage: [
				"Seed",
				"Growth",
				"Small business"
			],
			area: "Buckhead (Peachtree & Piedmont)",
			description: "Flexible workspace with professional meeting rooms. Good for investor or client meetings.",
			url: "https://meetatroam.com"
		},
		{
			id: "tech-square-atl",
			name: "Tech Square ATL",
			category: "Coworking & Hubs",
			stage: [
				"Idea",
				"Pre-seed",
				"Seed"
			],
			area: "Midtown / Tech Square",
			description: "Flexible coworking plus news and events connecting Tech Square's research and startup community.",
			url: "https://www.techsquareatl.com"
		},
		{
			id: "venture-atlanta",
			name: "Venture Atlanta",
			category: "Events",
			stage: ["Seed", "Growth"],
			area: "Midtown (Woodruff Arts Center)",
			description: "The Southeast's largest venture conference, held each October. Includes Startup Showcase Live, a pre-seed/seed pitch competition ($475K prize in 2026).",
			url: "https://www.ventureatlanta.org"
		},
		{
			id: "atl-tech-week",
			name: "Atlanta Tech Week",
			category: "Events",
			stage: [
				"Idea",
				"Pre-seed",
				"Seed",
				"Growth"
			],
			area: "Citywide",
			description: "Week of panels, workshops and meetups each August, produced by Render Group.",
			url: "https://www.atl.tech"
		},
		{
			id: "hypepotamus",
			name: "Hypepotamus",
			category: "News & Community",
			stage: [
				"Idea",
				"Pre-seed",
				"Seed",
				"Growth"
			],
			area: "Online",
			description: "News on startups, investors and corporate innovation in Atlanta and the Southeast.",
			url: "https://www.hypepotamus.com"
		}
	]
}, t = {
	"Accelerators & Incubators": "#2a6fdb",
	"Georgia Tech Programs": "#b3862b",
	"Funding & Investors": "#1f8a5b",
	"Coworking & Hubs": "#7a4fd1",
	Events: "#d1495b",
	"News & Community": "#4a5568"
}, n = {
	page: {
		fontFamily: "var(--font-sans, Inter, system-ui, -apple-system, \"Segoe UI\", sans-serif)",
		color: "var(--text-standard, #1a1d23)",
		background: "var(--surface-base, #f6f7f9)",
		maxWidth: "1120px",
		minHeight: "100%",
		boxSizing: "border-box",
		margin: "0 auto",
		padding: "28px clamp(16px, 4vw, 24px) 48px"
	},
	header: {
		display: "flex",
		alignItems: "flex-end",
		justifyContent: "space-between",
		gap: "16px",
		flexWrap: "wrap",
		marginBottom: "20px"
	},
	title: {
		fontSize: "24px",
		fontWeight: 700,
		margin: 0,
		letterSpacing: "-0.01em"
	},
	subtitle: {
		fontSize: "14px",
		color: "var(--text-subtle, #5b6270)",
		margin: "6px 0 0"
	},
	meta: {
		fontSize: "12px",
		color: "var(--text-metadata, #7a8190)"
	},
	toolbar: {
		background: "var(--surface-panel, #fff)",
		border: "1px solid var(--border-standard, #e3e6eb)",
		borderRadius: "12px",
		padding: "14px",
		display: "flex",
		flexDirection: "column",
		gap: "12px",
		marginBottom: "18px"
	},
	search: {
		width: "100%",
		boxSizing: "border-box",
		padding: "10px 12px",
		fontFamily: "inherit",
		fontSize: "14px",
		color: "var(--text-standard, #1a1d23)",
		background: "var(--surface-panel, #fff)",
		border: "1px solid var(--border-prominent, #d5d9e0)",
		borderRadius: "8px"
	},
	chipRow: {
		display: "flex",
		flexWrap: "wrap",
		gap: "6px",
		alignItems: "center"
	},
	rowLabel: {
		fontSize: "12px",
		fontWeight: 600,
		color: "var(--text-subtle, #5b6270)",
		width: "64px"
	},
	chip: {
		fontFamily: "inherit",
		fontSize: "13px",
		padding: "5px 11px",
		borderRadius: "999px",
		border: "1px solid var(--border-prominent, #d5d9e0)",
		background: "var(--surface-panel, #fff)",
		color: "var(--text-standard, #333a45)",
		cursor: "pointer"
	},
	chipOn: {
		background: "var(--affordance-prominent, #1a1d23)",
		color: "var(--text-on-prominent, #fff)",
		borderColor: "var(--affordance-prominent, #1a1d23)"
	},
	count: {
		fontSize: "13px",
		color: "var(--text-subtle, #5b6270)",
		margin: "0 0 10px"
	},
	grid: {
		display: "grid",
		gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 300px), 1fr))",
		gap: "14px"
	},
	card: {
		background: "var(--surface-panel, #fff)",
		border: "1px solid var(--border-standard, #e3e6eb)",
		borderRadius: "12px",
		padding: "16px",
		display: "flex",
		flexDirection: "column",
		gap: "10px",
		borderLeftWidth: "4px"
	},
	badge: {
		display: "inline-flex",
		alignItems: "center",
		gap: "6px",
		fontSize: "12px",
		fontWeight: 600,
		color: "var(--text-subtle, #4a5160)"
	},
	dot: {
		width: "8px",
		height: "8px",
		borderRadius: "50%",
		flexShrink: 0
	},
	name: {
		fontSize: "16px",
		fontWeight: 650,
		margin: 0
	},
	area: {
		fontSize: "12px",
		color: "var(--text-metadata, #7a8190)"
	},
	desc: {
		fontSize: "14px",
		lineHeight: 1.5,
		color: "var(--text-subtle, #333a45)",
		margin: 0,
		flexGrow: 1
	},
	pills: {
		display: "flex",
		flexWrap: "wrap",
		gap: "4px"
	},
	pill: {
		fontSize: "11px",
		padding: "2px 8px",
		borderRadius: "999px",
		background: "var(--surface-inset, #eef1f5)",
		color: "var(--text-subtle, #4a5160)"
	},
	link: {
		fontSize: "13px",
		fontWeight: 600,
		color: "var(--text-link, #2a6fdb)",
		textDecoration: "none",
		alignSelf: "flex-start"
	},
	empty: {
		textAlign: "center",
		padding: "48px 16px",
		color: "var(--text-subtle, #5b6270)",
		background: "var(--surface-panel, #fff)",
		border: "1px dashed var(--border-prominent, #d5d9e0)",
		borderRadius: "12px"
	},
	clear: {
		fontFamily: "inherit",
		fontSize: "13px",
		color: "var(--text-link, #2a6fdb)",
		background: "none",
		border: "none",
		cursor: "pointer",
		padding: 0,
		textDecoration: "underline"
	}
}, r = ["react", "pages"];
function i(r) {
	let i = r.react;
	function a({ label: e, options: t, value: r, onChange: a }) {
		return /* @__PURE__ */ i.createElement("div", {
			style: n.chipRow,
			role: "group",
			"aria-label": e
		}, /* @__PURE__ */ i.createElement("span", { style: n.rowLabel }, e), ["All", ...t].map((t) => {
			let o = t === "All" ? null : t, s = r === o;
			return /* @__PURE__ */ i.createElement("button", {
				key: t,
				type: "button",
				style: s ? {
					...n.chip,
					...n.chipOn
				} : n.chip,
				"aria-label": t === "All" ? `All ${e.toLowerCase()}` : t,
				"aria-pressed": s,
				onClick: () => a(o)
			}, t);
		}));
	}
	function o({ resource: e }) {
		let r = t[e.category] || "#4a5568";
		return /* @__PURE__ */ i.createElement("article", { style: {
			...n.card,
			borderLeftColor: r
		} }, /* @__PURE__ */ i.createElement("div", { style: n.badge }, /* @__PURE__ */ i.createElement("span", {
			style: {
				...n.dot,
				background: r
			},
			"aria-hidden": "true"
		}), e.category), /* @__PURE__ */ i.createElement("div", null, /* @__PURE__ */ i.createElement("h2", { style: n.name }, e.name), /* @__PURE__ */ i.createElement("div", { style: n.area }, e.area)), /* @__PURE__ */ i.createElement("p", { style: n.desc }, e.description), /* @__PURE__ */ i.createElement("div", { style: n.pills }, e.stage.map((e) => /* @__PURE__ */ i.createElement("span", {
			key: e,
			style: n.pill
		}, e))), e.url ? /* @__PURE__ */ i.createElement("a", {
			style: n.link,
			href: e.url,
			target: "_blank",
			rel: "noopener noreferrer"
		}, "Visit site ↗") : null);
	}
	function s() {
		let [t, r] = i.useState(""), [s, c] = i.useState(null), [l, u] = i.useState(null), d = t.trim().toLowerCase(), f = e.resources.filter((e) => (!s || e.category === s) && (!l || e.stage.includes(l)) && (!d || [
			e.name,
			e.description,
			e.area
		].join(" ").toLowerCase().includes(d)));
		function p() {
			r(""), c(null), u(null);
		}
		return /* @__PURE__ */ i.createElement("main", {
			style: n.page,
			"aria-label": "ATL Startup Resources"
		}, /* @__PURE__ */ i.createElement("header", { style: n.header }, /* @__PURE__ */ i.createElement("div", null, /* @__PURE__ */ i.createElement("h1", { style: n.title }, "ATL Startup Resources"), /* @__PURE__ */ i.createElement("p", { style: n.subtitle }, "Programs, funding, workspaces and events for founders building in Atlanta.")), /* @__PURE__ */ i.createElement("span", { style: n.meta }, e.resources.length, " resources · last checked ", e.lastChecked)), /* @__PURE__ */ i.createElement("section", {
			style: n.toolbar,
			"aria-label": "Filter resources"
		}, /* @__PURE__ */ i.createElement("input", {
			style: n.search,
			id: "atl-resource-search",
			type: "search",
			"aria-label": "Search resources",
			placeholder: "Search by name, focus or neighborhood…",
			value: t,
			onChange: (e) => r(e.target.value)
		}), /* @__PURE__ */ i.createElement(a, {
			label: "Category",
			options: e.categories,
			value: s,
			onChange: c
		}), /* @__PURE__ */ i.createElement(a, {
			label: "Stage",
			options: e.stages,
			value: l,
			onChange: u
		})), /* @__PURE__ */ i.createElement("p", {
			style: n.count,
			role: "status"
		}, "Showing ", f.length, " of ", e.resources.length), f.length ? /* @__PURE__ */ i.createElement("div", { style: n.grid }, f.map((e) => /* @__PURE__ */ i.createElement(o, {
			key: e.id,
			resource: e
		}))) : /* @__PURE__ */ i.createElement("div", { style: n.empty }, /* @__PURE__ */ i.createElement("p", { style: { margin: "0 0 8px" } }, "No resources match those filters."), /* @__PURE__ */ i.createElement("button", {
			type: "button",
			style: n.clear,
			onClick: p
		}, "Clear filters")));
	}
	r.pages.register({
		id: "atl-startup-resources",
		title: "ATL Startup Resources",
		primary: !0,
		component: s
	});
}
export { i as apply, r as inject };
