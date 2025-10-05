"use client";

import { CuratorForm } from "@/components/curator-form";
import { motion } from "framer-motion";
import { Sparkles, Palette, Users, Frame } from "lucide-react";

export default function Home() {
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

      <div className="container mx-auto px-4 py-12">
        <div className="flex flex-col items-center justify-center space-y-12">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center space-y-6 max-w-3xl w-full"
          >
            <div className="flex justify-center mb-4">
              <div className="inline-flex items-center gap-2 rounded-full border border-[var(--brand-primary)]/20 bg-white px-4 py-2 shadow-sm">
                <Sparkles className="h-4 w-4 text-[var(--brand-primary)]" />
                <span className="text-sm font-medium text-[var(--brand-ink)]">AI-Powered Curator</span>
              </div>
            </div>

            <h1 className="text-4xl font-extrabold tracking-tight text-[var(--brand-ink)] sm:text-5xl lg:text-6xl">
              Museum van Bommel van Dam
            </h1>

            <p className="text-xl text-[var(--brand-muted)] leading-relaxed">
              Transform your exhibition concept into a comprehensive proposal with AI-powered
              theme refinement, artist and artwork discovery
            </p>

            <div className="flex flex-wrap justify-center gap-6 pt-4">
              <div className="flex items-center gap-2">
                <div className="rounded-full bg-[var(--brand-accent)]/20 p-2">
                  <Palette className="h-5 w-5 text-[var(--brand-primary)]" />
                </div>
                <span className="text-sm text-[var(--brand-muted)]">Theme Refinement</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="rounded-full bg-[var(--brand-accent)]/20 p-2">
                  <Users className="h-5 w-5 text-[var(--brand-primary)]" />
                </div>
                <span className="text-sm text-[var(--brand-muted)]">Artist Discovery</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="rounded-full bg-[var(--brand-accent)]/20 p-2">
                  <Frame className="h-5 w-5 text-[var(--brand-primary)]" />
                </div>
                <span className="text-sm text-[var(--brand-muted)]">Artwork Discovery</span>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="w-full flex justify-center"
          >
            <CuratorForm />
          </motion.div>
        </div>
      </div>
    </div>
  );
}
