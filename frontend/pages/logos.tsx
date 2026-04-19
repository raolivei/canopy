import Image from "next/image";
import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { Card, CardContent } from "@/components/ui";

interface Concept {
  id: string;
  title: string;
  tagline: string;
  rationale: string;
  src: string;
  kind: "png" | "svg";
}

const CONCEPTS: Concept[] = [
  {
    id: "wallet-leaf",
    title: "Wallet-leaf",
    tagline: "Billfold meets canopy",
    rationale:
      "A wallet whose flap is a rounded canopy leaf, with a subtle upward chart hiding inside the pocket. Ties finance and growth in one glyph.",
    src: "/brand/concepts/logo-1-wallet-leaf.png",
    kind: "png",
  },
  {
    id: "tree-coin",
    title: "Tree-coin",
    tagline: "Canadian dollar, Canadian growth",
    rationale:
      "A CAD coin with a canopy tree growing through it — the crown folds over the rim. Reads instantly as \u201CCanadian investments compounding.\u201D",
    src: "/brand/concepts/logo-2-tree-coin.png",
    kind: "png",
  },
  {
    id: "maple-shield",
    title: "Maple-shield",
    tagline: "Self-hosted, Canadian, compounding",
    rationale:
      "Rounded shield (self-hosted cue) cradling an 11-point maple. One vein escapes and turns into a net-worth line. Most literal of the three.",
    src: "/brand/concepts/logo-3-maple-shield.png",
    kind: "png",
  },
  {
    id: "leaf-chart",
    title: "Leaf-chart",
    tagline: "Veins that resolve into growth",
    rationale:
      "Monoline SVG, re-themes with the app. The leaf veins dissolve into a rising line chart; the stem tucks into a wallet pocket at the base.",
    src: "/brand/concepts/logo-4-leaf-chart.svg",
    kind: "svg",
  },
  {
    id: "monogram",
    title: "Canopy monogram",
    tagline: "A 'C' made of branch",
    rationale:
      "Monoline SVG, re-themes with the app. A bent branch shaped like a \u2018C\u2019 with three leaves; the negative space reads as ascending bars.",
    src: "/brand/concepts/logo-5-monogram.svg",
    kind: "svg",
  },
];

function Swatch({
  concept,
  variant,
}: {
  concept: Concept;
  variant: "light" | "dark";
}) {
  const bg =
    variant === "light"
      ? "bg-white"
      : "bg-slate-950";
  const fg =
    variant === "light"
      ? "text-emerald-600"
      : "text-emerald-400";
  const label =
    variant === "light" ? "Light" : "Dark";
  const labelTone =
    variant === "light"
      ? "text-slate-500"
      : "text-slate-400";

  return (
    <div
      className={`relative flex aspect-square w-full items-center justify-center overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 ${bg}`}
    >
      <span
        className={`absolute left-2 top-2 text-[10px] uppercase tracking-wider ${labelTone}`}
      >
        {label}
      </span>
      {concept.kind === "svg" ? (
        <div className={`h-24 w-24 ${fg}`}>
          <object
            data={concept.src}
            type="image/svg+xml"
            aria-label={`${concept.title} on ${label.toLowerCase()} background`}
            className="h-full w-full"
          />
        </div>
      ) : (
        <div className="relative h-28 w-28">
          <Image
            src={concept.src}
            alt={`${concept.title} on ${label.toLowerCase()} background`}
            fill
            sizes="112px"
            className="object-contain"
            unoptimized
          />
        </div>
      )}
    </div>
  );
}

export default function LogosPage() {
  return (
    <PageLayout
      title="Brand explorations"
      description="Five directions for the Canopy mark. The active logo is unchanged."
    >
      <PageHeader
        title="Brand explorations"
        description="Five directions for the Canopy mark. The active logo is unchanged — pick a favourite in the PR comments."
      />

      <Card className="mb-6">
        <CardContent className="p-5 text-sm text-slate-600 dark:text-slate-300">
          <p>
            Canopy is a self-hosted, CAD-only tracker for Canadian investments
            (see the{" "}
            <a
              href="https://github.com/raolivei/canopy#readme"
              target="_blank"
              rel="noreferrer"
              className="text-emerald-600 underline-offset-2 hover:underline dark:text-emerald-400"
            >
              README
            </a>
            ). Each concept below tries to express that in one glyph: wallet /
            tree / natural, Canadian, compounding.
          </p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {CONCEPTS.map((concept, idx) => (
          <Card key={concept.id}>
            <CardContent className="p-5">
              <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold tracking-tight text-slate-900 dark:text-white">
                    {idx + 1}. {concept.title}
                  </h2>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {concept.tagline}
                  </p>
                </div>
                <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] uppercase tracking-wider text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
                  {concept.kind === "svg" ? "SVG \u00B7 themed" : "PNG \u00B7 1024"}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Swatch concept={concept} variant="light" />
                <Swatch concept={concept} variant="dark" />
              </div>

              <p className="mt-4 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
                {concept.rationale}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <p className="mt-8 text-center text-xs text-slate-500 dark:text-slate-500">
        Assets live in{" "}
        <code className="rounded bg-slate-100 px-1 py-0.5 dark:bg-slate-800">
          frontend/public/brand/concepts/
        </code>
        .
      </p>
    </PageLayout>
  );
}
