import type { Context } from "@buzz/author";
import type { CSSProperties } from "react";

type Resource = {
  id: string;
  name: string;
  category: string;
  stage: readonly string[];
  area: string;
  description: string;
  url: string | null;
};

const DATA: {
  lastChecked: string;
  categories: readonly string[];
  stages: readonly string[];
  resources: readonly Resource[];
} = {
  "lastChecked": "2026-11-13",
  "categories": [
    "Accelerators & Incubators",
    "Georgia Tech Programs",
    "Funding & Investors",
    "Coworking & Hubs",
    "Events",
    "News & Community"
  ],
  "stages": [
    "Idea",
    "Pre-seed",
    "Seed",
    "Growth",
    "Small business"
  ],
  "resources": [
    {
      "id": "atdc",
      "name": "ATDC",
      "category": "Accelerators & Incubators",
      "stage": ["Idea", "Pre-seed", "Seed"],
      "area": "Midtown / Tech Square",
      "description": "Georgia Tech's statewide startup incubator. Tiered programs (Educate, Accelerate, Signature) plus industry tracks, mentors, funding and corporate pilot connections.",
      "url": "https://atdc.org"
    },
    {
      "id": "engage",
      "name": "Engage",
      "category": "Accelerators & Incubators",
      "stage": ["Seed", "Growth"],
      "area": "Atlanta",
      "description": "Corporate-backed platform (Delta, Coca-Cola, The Home Depot and others) with a 10-week Enterprise Accelerator that runs each spring and fall.",
      "url": "https://engage.vc"
    },
    {
      "id": "cox-cleantech",
      "name": "Cox Cleantech Accelerator",
      "category": "Accelerators & Incubators",
      "stage": ["Pre-seed", "Seed"],
      "area": "Atlanta",
      "description": "12-week cleantech program run with gener8tor and the Georgia Cleantech Innovation Hub; $250K investment per startup. Also runs an equity-free Residency.",
      "url": "https://www.gener8tor.com/cox"
    },
    {
      "id": "founder-institute",
      "name": "Founder Institute Atlanta",
      "category": "Accelerators & Incubators",
      "stage": ["Idea"],
      "area": "Virtual",
      "description": "Idea-stage pre-accelerator chapter for Atlanta founders. Runs fully virtual and charges an entrance fee.",
      "url": "https://fi.co/atlanta"
    },
    {
      "id": "create-x",
      "name": "CREATE-X Startup Launch",
      "category": "Georgia Tech Programs",
      "stage": ["Idea", "Pre-seed"],
      "area": "Georgia Tech",
      "description": "12-week summer program for GT students, faculty, researchers and alumni: $5K seed funding, ~$30K in-kind services, 24/7 coworking and Demo Day.",
      "url": "https://create-x.gatech.edu/launch/startup-launch"
    },
    {
      "id": "quadrant-i",
      "name": "Quadrant-i",
      "category": "Georgia Tech Programs",
      "stage": ["Idea"],
      "area": "Georgia Tech",
      "description": "GT unit that helps faculty, researchers and grad students turn research into startups. Its Startup Launch section includes a $10K commercialization grant.",
      "url": "https://quadrant-i.gatech.edu"
    },
    {
      "id": "venturelab",
      "name": "VentureLab",
      "category": "Georgia Tech Programs",
      "stage": ["Idea"],
      "area": "Georgia Tech",
      "description": "GT's commercialization teaching and training unit for faculty and students. No charge and no equity taken.",
      "url": "https://venturelab.gatech.edu"
    },
    {
      "id": "gra",
      "name": "Georgia Research Alliance",
      "category": "Funding & Investors",
      "stage": ["Idea", "Pre-seed"],
      "area": "Statewide",
      "description": "Innovation & Entrepreneurship grants ($10K–$250K) and startup loans for companies built on Georgia university technology.",
      "url": "https://gra.org"
    },
    {
      "id": "invest-atlanta",
      "name": "Invest Atlanta – Startup Growth Loan",
      "category": "Funding & Investors",
      "stage": ["Seed", "Small business"],
      "area": "City of Atlanta",
      "description": "City economic development agency. Its Atlanta Startup Growth Loan Program offers direct loans up to $150K to tech startups in the city, alongside other small business loans.",
      "url": "https://www.investatlanta.com/businesses/small-businesses/atlanta-startup-growth-program"
    },
    {
      "id": "atlanta-ventures",
      "name": "Atlanta Ventures",
      "category": "Funding & Investors",
      "stage": ["Pre-seed", "Seed"],
      "area": "Atlanta",
      "description": "Venture studio and early-stage fund. Free founder resources include office hours and monthly pitch practice.",
      "url": "https://atlantaventures.com"
    },
    {
      "id": "atv",
      "name": "Atlanta Tech Village",
      "category": "Coworking & Hubs",
      "stage": ["Idea", "Pre-seed", "Seed", "Growth"],
      "area": "Buckhead + 3 other locations",
      "description": "Startup hub at 3423 Piedmont Rd NE. Programs include Women + Tech, It Takes A Village, Startup Summer School and Atlanta Startup Village.",
      "url": "https://atlantatechvillage.com"
    },
    {
      "id": "switchyards",
      "name": "Switchyards",
      "category": "Coworking & Hubs",
      "stage": ["Idea", "Pre-seed", "Seed", "Small business"],
      "area": "12 metro Atlanta clubs",
      "description": "Membership work club. $100/mo on an annual plan or $129/mo month-to-month for access to every club.",
      "url": "https://www.switchyards.com"
    },
    {
      "id": "roam",
      "name": "Roam",
      "category": "Coworking & Hubs",
      "stage": ["Seed", "Growth", "Small business"],
      "area": "Buckhead (Peachtree & Piedmont)",
      "description": "Flexible workspace with professional meeting rooms. Good for investor or client meetings.",
      "url": "https://meetatroam.com"
    },
    {
      "id": "tech-square-atl",
      "name": "Tech Square ATL",
      "category": "Coworking & Hubs",
      "stage": ["Idea", "Pre-seed", "Seed"],
      "area": "Midtown / Tech Square",
      "description": "Flexible coworking plus news and events connecting Tech Square's research and startup community.",
      "url": "https://www.techsquareatl.com"
    },
    {
      "id": "venture-atlanta",
      "name": "Venture Atlanta",
      "category": "Events",
      "stage": ["Seed", "Growth"],
      "area": "Midtown (Woodruff Arts Center)",
      "description": "The Southeast's largest venture conference, held each October. Includes Startup Showcase Live, a pre-seed/seed pitch competition ($475K prize in 2026).",
      "url": "https://www.ventureatlanta.org"
    },
    {
      "id": "atl-tech-week",
      "name": "Atlanta Tech Week",
      "category": "Events",
      "stage": ["Idea", "Pre-seed", "Seed", "Growth"],
      "area": "Citywide",
      "description": "Week of panels, workshops and meetups each August, produced by Render Group.",
      "url": "https://www.atl.tech"
    },
    {
      "id": "hypepotamus",
      "name": "Hypepotamus",
      "category": "News & Community",
      "stage": ["Idea", "Pre-seed", "Seed", "Growth"],
      "area": "Online",
      "description": "News on startups, investors and corporate innovation in Atlanta and the Southeast.",
      "url": "https://www.hypepotamus.com"
    }
  ]
};

// Category accents intentionally preserve the supplied mockup's palette.
const CAT_COLOR: Record<string, string> = {
  "Accelerators & Incubators": "#2a6fdb",
  "Georgia Tech Programs": "#b3862b",
  "Funding & Investors": "#1f8a5b",
  "Coworking & Hubs": "#7a4fd1",
  "Events": "#d1495b",
  "News & Community": "#4a5568",
};

const S = {
  page: {
    fontFamily: 'var(--font-sans, Inter, system-ui, -apple-system, "Segoe UI", sans-serif)',
    color: "var(--text-standard, #1a1d23)",
    background: "var(--surface-base, #f6f7f9)",
    maxWidth: "1120px",
    minHeight: "100%",
    boxSizing: "border-box",
    margin: "0 auto",
    padding: "28px clamp(16px, 4vw, 24px) 48px",
  },
  header: {
    display: "flex",
    alignItems: "flex-end",
    justifyContent: "space-between",
    gap: "16px",
    flexWrap: "wrap",
    marginBottom: "20px",
  },
  title: { fontSize: "24px", fontWeight: 700, margin: 0, letterSpacing: "-0.01em" },
  subtitle: { fontSize: "14px", color: "var(--text-subtle, #5b6270)", margin: "6px 0 0" },
  meta: { fontSize: "12px", color: "var(--text-metadata, #7a8190)" },
  toolbar: {
    background: "var(--surface-panel, #fff)",
    border: "1px solid var(--border-standard, #e3e6eb)",
    borderRadius: "12px",
    padding: "14px",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    marginBottom: "18px",
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
    borderRadius: "8px",
  },
  chipRow: { display: "flex", flexWrap: "wrap", gap: "6px", alignItems: "center" },
  rowLabel: { fontSize: "12px", fontWeight: 600, color: "var(--text-subtle, #5b6270)", width: "64px" },
  chip: {
    fontFamily: "inherit",
    fontSize: "13px",
    padding: "5px 11px",
    borderRadius: "999px",
    border: "1px solid var(--border-prominent, #d5d9e0)",
    background: "var(--surface-panel, #fff)",
    color: "var(--text-standard, #333a45)",
    cursor: "pointer",
  },
  chipOn: {
    background: "var(--affordance-prominent, #1a1d23)",
    color: "var(--text-on-prominent, #fff)",
    borderColor: "var(--affordance-prominent, #1a1d23)",
  },
  count: { fontSize: "13px", color: "var(--text-subtle, #5b6270)", margin: "0 0 10px" },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 300px), 1fr))",
    gap: "14px",
  },
  card: {
    background: "var(--surface-panel, #fff)",
    border: "1px solid var(--border-standard, #e3e6eb)",
    borderRadius: "12px",
    padding: "16px",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    borderLeftWidth: "4px",
  },
  badge: {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    fontSize: "12px",
    fontWeight: 600,
    color: "var(--text-subtle, #4a5160)",
  },
  dot: { width: "8px", height: "8px", borderRadius: "50%", flexShrink: 0 },
  name: { fontSize: "16px", fontWeight: 650, margin: 0 },
  area: { fontSize: "12px", color: "var(--text-metadata, #7a8190)" },
  desc: {
    fontSize: "14px",
    lineHeight: 1.5,
    color: "var(--text-subtle, #333a45)",
    margin: 0,
    flexGrow: 1,
  },
  pills: { display: "flex", flexWrap: "wrap", gap: "4px" },
  pill: {
    fontSize: "11px",
    padding: "2px 8px",
    borderRadius: "999px",
    background: "var(--surface-inset, #eef1f5)",
    color: "var(--text-subtle, #4a5160)",
  },
  link: {
    fontSize: "13px",
    fontWeight: 600,
    color: "var(--text-link, #2a6fdb)",
    textDecoration: "none",
    alignSelf: "flex-start",
  },
  empty: {
    textAlign: "center",
    padding: "48px 16px",
    color: "var(--text-subtle, #5b6270)",
    background: "var(--surface-panel, #fff)",
    border: "1px dashed var(--border-prominent, #d5d9e0)",
    borderRadius: "12px",
  },
  clear: {
    fontFamily: "inherit",
    fontSize: "13px",
    color: "var(--text-link, #2a6fdb)",
    background: "none",
    border: "none",
    cursor: "pointer",
    padding: 0,
    textDecoration: "underline",
  },
} satisfies Record<string, CSSProperties>;

export const inject = ["react", "pages"];

export function apply(ctx: Context) {
  const React = ctx.react;

  function FilterChips({
    label,
    options,
    value,
    onChange,
  }: {
    label: string;
    options: readonly string[];
    value: string | null;
    onChange: (value: string | null) => void;
  }) {
    return (
      <div style={S.chipRow} role="group" aria-label={label}>
        <span style={S.rowLabel}>{label}</span>
        {["All", ...options].map((option) => {
          const optionValue = option === "All" ? null : option;
          const selected = value === optionValue;
          return (
            <button
              key={option}
              type="button"
              style={selected ? { ...S.chip, ...S.chipOn } : S.chip}
              aria-label={option === "All" ? `All ${label.toLowerCase()}` : option}
              aria-pressed={selected}
              onClick={() => onChange(optionValue)}
            >
              {option}
            </button>
          );
        })}
      </div>
    );
  }

  function ResourceCard({ resource }: { resource: Resource }) {
    const color = CAT_COLOR[resource.category] || "#4a5568";
    return (
      <article style={{ ...S.card, borderLeftColor: color }}>
        <div style={S.badge}>
          <span style={{ ...S.dot, background: color }} aria-hidden="true" />
          {resource.category}
        </div>
        <div>
          <h2 style={S.name}>{resource.name}</h2>
          <div style={S.area}>{resource.area}</div>
        </div>
        <p style={S.desc}>{resource.description}</p>
        <div style={S.pills}>
          {resource.stage.map((stage) => (
            <span key={stage} style={S.pill}>{stage}</span>
          ))}
        </div>
        {resource.url ? (
          <a style={S.link} href={resource.url} target="_blank" rel="noopener noreferrer">
            Visit site ↗
          </a>
        ) : null}
      </article>
    );
  }

  function AtlStartupResources() {
    const [query, setQuery] = React.useState("");
    const [category, setCategory] = React.useState<string | null>(null);
    const [stage, setStage] = React.useState<string | null>(null);
    const normalizedQuery = query.trim().toLowerCase();
    const results = DATA.resources.filter((resource) =>
      (!category || resource.category === category) &&
      (!stage || resource.stage.includes(stage)) &&
      (!normalizedQuery || [resource.name, resource.description, resource.area]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery))
    );

    function clearFilters() {
      setQuery("");
      setCategory(null);
      setStage(null);
    }

    return (
      <main style={S.page} aria-label="ATL Startup Resources">
        <header style={S.header}>
          <div>
            <h1 style={S.title}>ATL Startup Resources</h1>
            <p style={S.subtitle}>
              Programs, funding, workspaces and events for founders building in Atlanta.
            </p>
          </div>
          <span style={S.meta}>
            {DATA.resources.length} resources · last checked {DATA.lastChecked}
          </span>
        </header>
        <section style={S.toolbar} aria-label="Filter resources">
          <input
            style={S.search}
            id="atl-resource-search"
            type="search"
            aria-label="Search resources"
            placeholder="Search by name, focus or neighborhood…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <FilterChips label="Category" options={DATA.categories} value={category} onChange={setCategory} />
          <FilterChips label="Stage" options={DATA.stages} value={stage} onChange={setStage} />
        </section>
        <p style={S.count} role="status">Showing {results.length} of {DATA.resources.length}</p>
        {results.length ? (
          <div style={S.grid}>
            {results.map((resource) => <ResourceCard key={resource.id} resource={resource} />)}
          </div>
        ) : (
          <div style={S.empty}>
            <p style={{ margin: "0 0 8px" }}>No resources match those filters.</p>
            <button type="button" style={S.clear} onClick={clearFilters}>Clear filters</button>
          </div>
        )}
      </main>
    );
  }

  ctx.pages.register({
    id: "atl-startup-resources",
    title: "ATL Startup Resources",
    primary: true,
    component: AtlStartupResources,
  });
}
