'use client';
import React, { useMemo, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  BookOpenText,
  Brain,
  CircleCheck,
  HelpCircle,
  Layers,
  Lightbulb,
  ListChecks,
  Sparkles,
  Tag,
  TrendingUp,
  Users,
  ArrowRight,
  ArrowLeft,
} from "lucide-react";
import { DEMO_THEME } from "@/lib/demo-data";

function ExhibitRow({ title, desc, estimate, artists }: { title: string; desc: string; estimate: number; artists: string[] }) {
  return (
    <motion.div whileHover={{ y: -2 }} className="group relative overflow-hidden rounded-2xl border bg-white p-4 transition-shadow hover:shadow-sm">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-1 rounded-t-2xl bg-[var(--brand-primary)]/80" />
      <div className="flex flex-col gap-2 pt-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-base font-semibold text-[var(--brand-ink)]">{title}</div>
          <p className="text-sm text-[var(--brand-muted)]">{desc}</p>
        </div>
        <div className="mt-2 flex items-center gap-2 sm:mt-0">
          <Badge variant="outline" className="border-[var(--brand-primary)]/30 text-[var(--brand-ink)]">
            Estimated artworks: {estimate}
          </Badge>
        </div>
      </div>
      {artists.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {artists.map((a) => (
            <Badge key={a} variant="secondary" className="rounded-full bg-neutral-100 text-[var(--brand-ink)]">
              {a}
            </Badge>
          ))}
        </div>
      )}
    </motion.div>
  );
}

function Sidebar({ active, iterationCount }: { active: string; iterationCount: number }) {
  const items = useMemo(
    () => [
      { id: "central-argument", label: "Central Argument", icon: Brain },
      { id: "opening-text", label: "Opening Wall Text", icon: BookOpenText },
      { id: "exhibition-sections", label: "Exhibition Sections", icon: Layers },
      { id: "key-questions", label: "Key Questions", icon: HelpCircle },
      { id: "contemporary-relevance", label: "Contemporary Relevance", icon: TrendingUp },
      { id: "visitor-takeaway", label: "Visitor Takeaway", icon: Users },
      { id: "validated-concepts", label: "Validated Concepts", icon: Tag },
      { id: "educational-angles", label: "Educational Angles", icon: ListChecks },
    ],
    []
  );

  return (
    <aside className="sticky top-6 hidden h-fit w-64 shrink-0 lg:block">
      <Card className="border-neutral-200 bg-white shadow-sm">
        <CardContent className="p-4">
          <div className="mb-3 text-xs uppercase tracking-wider text-[var(--brand-muted)]">Phase 1 • Iteration {iterationCount}</div>
          <div className="mb-4 flex flex-col gap-2">
            <Badge className="rounded-full bg-[var(--brand-accent)]/20 text-[var(--brand-ink)] hover:bg-[var(--brand-accent)]/30" variant="secondary">
              <Sparkles className="mr-2 h-4 w-4" /> DEMO MODE
            </Badge>
            <Badge className="rounded-full border-[var(--brand-primary)]/30" variant="outline">
              Complete
            </Badge>
          </div>
          <Separator className="my-3 bg-[var(--brand-accent)]/20" />
          <nav className="space-y-1">
            {items.map(({ id, label, icon: Icon }) => (
              <a
                key={id}
                href={`#${id}`}
                className={`flex items-center gap-2 rounded-xl px-2 py-2 text-sm transition-all hover:translate-x-0.5 ${
                  active === id
                    ? "bg-[var(--brand-accent)]/15 text-[var(--brand-primary)]"
                    : "hover:bg-neutral-100 text-[var(--brand-ink)]"
                }`}
              >
                <Icon className={`h-4 w-4 ${active === id ? "text-[var(--brand-primary)]" : "text-[var(--brand-muted)]"}`} />
                <span>{label}</span>
              </a>
            ))}
          </nav>
        </CardContent>
      </Card>
    </aside>
  );
}

function SectionCard({ id, icon: Icon, title, children }: any) {
  return (
    <motion.section
      id={id}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <Card className="relative overflow-hidden border-neutral-200 bg-white">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-[2px] w-full bg-[var(--brand-primary)]/80" />
        <CardContent className="p-6">
          <div className="mb-3 flex items-center gap-2">
            <Icon className="h-5 w-5 text-[var(--brand-muted)]" />
            <h2 className="text-lg font-semibold text-[var(--brand-ink)]">{title}</h2>
          </div>
          <div className="max-w-none text-[15px] leading-7 text-[var(--brand-ink)]">
            {children}
          </div>
        </CardContent>
      </Card>
    </motion.section>
  );
}

export default function DemoThemePage() {
  const router = useRouter();
  const [active, setActive] = useState("central-argument");

  // Active section detection on scroll
  useEffect(() => {
    const handleScroll = () => {
      const sections = document.querySelectorAll("section[id]");
      const scrollPosition = window.scrollY + 200; // Offset for better detection

      let currentSection = "central-argument"; // Default to first section

      sections.forEach((section) => {
        const sectionTop = (section as HTMLElement).offsetTop;
        const sectionHeight = (section as HTMLElement).offsetHeight;

        if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
          currentSection = section.id;
        }
      });

      setActive(currentSection);
    };

    // Initial check
    handleScroll();

    // Add scroll listener
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="relative min-h-screen" style={{
      ["--brand-bg" as any]: "#F7F6F3",
      ["--brand-ink" as any]: "#1C1C1C",
      ["--brand-muted" as any]: "#6B6F76",
      ["--brand-primary" as any]: "#7A1E20",
      ["--brand-primary-600" as any]: "#611618",
      ["--brand-accent" as any]: "#C0A46B",
      backgroundColor: "var(--brand-bg)",
      color: "var(--brand-ink)",
    }}>
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(60%_40%_at_80%_0%,rgba(192,164,107,0.12),transparent_60%)]" />

      <div className="mx-auto max-w-7xl px-4 py-8 lg:px-8">
        <motion.header initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <div className="text-xs text-[var(--brand-muted)]">Phase 1 • Iteration {DEMO_THEME.iteration_count}</div>
              <h1 className="text-3xl font-extrabold tracking-tight text-[var(--brand-ink)] sm:text-4xl">
                {DEMO_THEME.exhibition_title}
              </h1>
            </div>
          </div>
        </motion.header>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[16rem_1fr] lg:items-start">
          <Sidebar active={active} iterationCount={DEMO_THEME.iteration_count} />

          <div className="space-y-6">
            <SectionCard id="central-argument" icon={Brain} title="Central Argument">
              <p>{DEMO_THEME.central_argument}</p>
            </SectionCard>

            <SectionCard id="opening-text" icon={BookOpenText} title="Opening Wall Text">
              <p className="whitespace-pre-line">{DEMO_THEME.opening_wall_text}</p>
            </SectionCard>

            <SectionCard id="exhibition-sections" icon={Layers} title="Exhibition Sections">
              <div className="space-y-4">
                {DEMO_THEME.exhibition_sections.map((section, index) => (
                  <ExhibitRow
                    key={index}
                    title={section.title}
                    desc={section.focus}
                    estimate={section.estimated_artwork_count}
                    artists={section.artist_emphasis}
                  />
                ))}
              </div>
            </SectionCard>

            <SectionCard id="key-questions" icon={HelpCircle} title="Key Questions">
              <ul className="grid gap-3 sm:grid-cols-2">
                {DEMO_THEME.key_questions.map((q, index) => (
                  <li
                    key={index}
                    className="group relative flex items-start gap-3 overflow-hidden rounded-xl border bg-white p-3 transition-all hover:shadow-sm"
                  >
                    <span className="pointer-events-none absolute inset-x-0 top-0 h-px bg-[var(--brand-accent)]/40" />
                    <Lightbulb className="mt-0.5 h-5 w-5" aria-hidden />
                    <span>{q}</span>
                  </li>
                ))}
              </ul>
            </SectionCard>

            <SectionCard id="contemporary-relevance" icon={TrendingUp} title="Contemporary Relevance">
              <p>{DEMO_THEME.contemporary_relevance}</p>
            </SectionCard>

            <SectionCard id="visitor-takeaway" icon={Users} title="Visitor Takeaway">
              <p>{DEMO_THEME.visitor_takeaway}</p>
            </SectionCard>

            <SectionCard id="validated-concepts" icon={Tag} title="Validated Art Historical Concepts">
              <div className="flex flex-wrap gap-2">
                {DEMO_THEME.validated_concepts.map((concept, index) => (
                  <Badge key={index} variant="secondary" className="rounded-full bg-neutral-100 px-3 py-1 text-sm">
                    {concept.original_concept} ({Math.round(concept.confidence_score * 100)}%)
                  </Badge>
                ))}
              </div>
            </SectionCard>

            <SectionCard id="educational-angles" icon={ListChecks} title="Educational Angles">
              <ul className="space-y-2">
                {DEMO_THEME.educational_angles.map((item, index) => (
                  <li key={index} className="flex items-start gap-3">
                    <CircleCheck className="mt-0.5 h-5 w-5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </SectionCard>

            {/* Navigation Section */}
            <Card className="relative overflow-hidden border-neutral-200 bg-white">
              <div className="pointer-events-none absolute inset-x-0 top-0 h-[2px] w-full bg-[var(--brand-primary)]/80" />
              <CardContent className="p-6">
                <div className="mb-3">
                  <h2 className="text-lg font-semibold text-[var(--brand-ink)]">Next Steps</h2>
                  <p className="text-sm text-[var(--brand-muted)]">Proceed to artist discovery to select artists for your exhibition</p>
                </div>
                <div className="flex gap-4">
                  <Button
                    onClick={() => router.push("/")}
                    variant="outline"
                    className="flex-1 border-[var(--brand-primary)]/30 text-[var(--brand-primary)] hover:bg-neutral-100"
                  >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back to Home
                  </Button>
                  <Button
                    onClick={() => router.push("/demo/artists")}
                    className="flex-1 bg-[var(--brand-primary)] text-white hover:bg-[var(--brand-primary-600)]"
                  >
                    Continue to Artist Discovery
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
