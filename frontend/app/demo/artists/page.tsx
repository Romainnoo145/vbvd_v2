"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { ArrowRight, ArrowLeft, Calendar, ExternalLink, Sparkles, CheckCircle, User } from "lucide-react";
import { DEMO_ARTISTS } from "@/lib/demo-data";

export default function DemoArtistsPage() {
  const router = useRouter();
  const [artists, setArtists] = useState(DEMO_ARTISTS.map(a => ({ ...a })));
  const [currentPage, setCurrentPage] = useState(1);
  const artistsPerPage = 20;

  const selectedCount = artists.filter(a => a.selected).length;
  const targetCount = 15;

  // Pagination logic
  const totalPages = Math.ceil(artists.length / artistsPerPage);
  const startIndex = (currentPage - 1) * artistsPerPage;
  const endIndex = startIndex + artistsPerPage;
  const currentArtists = artists.slice(startIndex, endIndex);

  const toggleArtist = (index: number) => {
    const newArtists = [...artists];
    newArtists[index].selected = !newArtists[index].selected;
    setArtists(newArtists);
  };

  const handleContinue = () => {
    if (selectedCount < 1) {
      alert("Please select at least 1 artist to continue");
      return;
    }

    // Store selected artists
    const selected = artists.filter(a => a.selected);
    sessionStorage.setItem('demo_selected_artists', JSON.stringify(selected));

    router.push("/demo/artworks");
  };

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

      <div className="container mx-auto p-6 max-w-7xl space-y-6">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Card className="relative overflow-hidden border-neutral-200 bg-white shadow-lg">
            <div className="pointer-events-none absolute inset-x-0 top-0 h-[3px] w-full bg-[var(--brand-primary)]/80" />
            <CardHeader className="pt-8">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="secondary" className="bg-[var(--brand-accent)]/20 text-[var(--brand-ink)]">
                      DEMO MODE
                    </Badge>
                    <Badge variant="outline" className="border-[var(--brand-primary)]/30">
                      Phase 2
                    </Badge>
                  </div>
                  <CardTitle className="text-3xl text-[var(--brand-ink)]">Artist Discovery</CardTitle>
                  <CardDescription className="mt-2 text-[var(--brand-muted)]">
                    Select {targetCount} artists for your exhibition "Dreams & Reality: The Surrealist Revolution"
                  </CardDescription>
                </div>
                <Badge
                  variant={selectedCount >= targetCount ? "default" : "secondary"}
                  className={`text-lg px-4 py-2 shrink-0 ${
                    selectedCount >= targetCount
                      ? "bg-[var(--brand-primary)] text-white"
                      : "bg-[var(--brand-accent)]/20 text-[var(--brand-ink)]"
                  }`}
                >
                  {selectedCount >= targetCount && <CheckCircle className="mr-2 h-5 w-5" />}
                  {selectedCount} / {targetCount} selected
                </Badge>
              </div>
            </CardHeader>
          </Card>
        </motion.div>

        {/* Europeana-First Discovery Banner */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card className="border-[var(--brand-primary)]/30 bg-gradient-to-r from-[var(--brand-primary)]/5 to-[var(--brand-accent)]/5">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="shrink-0 rounded-full bg-[var(--brand-primary)]/10 p-2">
                  <svg className="h-5 w-5 text-[var(--brand-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.586-3.414A2 2 0 0015.172 6H8.828a2 2 0 00-1.414.586l-4 4a2 2 0 000 2.828l4 4a2 2 0 001.414.586h6.344a2 2 0 001.414-.586l4-4a2 2 0 000-2.828l-4-4z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-[var(--brand-ink)] mb-1">🎨 Discovered via Europeana-First Architecture</h3>
                  <p className="text-sm text-[var(--brand-muted)]">
                    These artists were discovered by searching <strong className="text-[var(--brand-ink)]">available artworks</strong> in European collections,
                    then ranking by quality metrics (works count, IIIF availability, institution diversity).
                    This ensures every artist has <strong className="text-[var(--brand-ink)]">loanable works</strong> ready for exhibition.
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs">
                    <span className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 px-2 py-1 rounded border border-blue-200">
                      <span>📚</span> Wikipedia Biography = Established artist
                    </span>
                    <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-700 px-2 py-1 rounded border border-amber-200">
                      <span>🎨</span> Europeana Metadata = Emerging/Regional artist
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Selection Guide */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
          <Card className="border-neutral-200 bg-white">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <Sparkles className="h-5 w-5 text-[var(--brand-primary)] shrink-0 mt-0.5" />
                <p className="text-sm text-[var(--brand-muted)]">
                  <strong className="text-[var(--brand-ink)]">Selection Tips:</strong> Artists are ranked by Quality Score (0-100) based on availability.
                  Choose artists that best represent your exhibition theme.
                  Consider mix of established (Wikipedia) and emerging (Europeana) artists.
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Pagination Info */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Card className="border-neutral-200 bg-white">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between text-sm text-[var(--brand-muted)]">
                <span>
                  Showing {startIndex + 1}-{Math.min(endIndex, artists.length)} of {artists.length} artists
                </span>
                <span>
                  Page {currentPage} of {totalPages}
                </span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Artist Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {currentArtists.map((artist, displayIndex) => {
            const actualIndex = startIndex + displayIndex;
            return (
            <motion.div
              key={actualIndex}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + displayIndex * 0.05 }}
            >
              <Card
                className={`relative overflow-hidden cursor-pointer transition-all border-neutral-200 bg-white hover:shadow-lg ${
                  artist.selected
                    ? 'ring-2 ring-[var(--brand-primary)] shadow-md'
                    : 'hover:border-[var(--brand-accent)]'
                }`}
                onClick={() => toggleArtist(actualIndex)}
              >
                {artist.selected && (
                  <div className="pointer-events-none absolute inset-x-0 top-0 h-1 w-full bg-[var(--brand-primary)]/80" />
                )}
                <CardHeader className={artist.selected ? "pt-6" : ""}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Checkbox
                          checked={artist.selected}
                          onCheckedChange={() => toggleArtist(actualIndex)}
                          onClick={(e) => e.stopPropagation()}
                          className="data-[state=checked]:bg-[var(--brand-primary)] data-[state=checked]:border-[var(--brand-primary)]"
                        />
                        <CardTitle className="text-xl text-[var(--brand-ink)]">{artist.name}</CardTitle>
                      </div>
                      <div className="flex items-center gap-2 mt-2 text-sm text-[var(--brand-muted)]">
                        <Calendar className="h-4 w-4" />
                        <span>
                          {artist.enrichment?.estimatedActivePeriod ||
                           `${artist.birth_year}–${artist.death_year || "present"}`}
                        </span>
                        <span>•</span>
                        <span>{artist.nationality}</span>
                      </div>
                      {/* Europeana-First: Enrichment Source Badge */}
                      <div className="mt-2">
                        {artist.enrichment?.source === 'wikipedia' ? (
                          <Badge variant="secondary" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                            📚 Wikipedia Biography
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="text-xs bg-amber-50 text-amber-700 border-amber-200">
                            🎨 Discovered via Europeana
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-col gap-2 items-end">
                      {/* Quality Score */}
                      {artist.qualityScore && (
                        <Badge
                          variant="outline"
                          className="border-[var(--brand-primary)]/40 text-[var(--brand-ink)] font-bold"
                        >
                          Score: {artist.qualityScore.total}
                        </Badge>
                      )}
                      <Badge variant="outline" className="border-[var(--brand-accent)]/40 text-[var(--brand-ink)]">
                        {Math.round(artist.relevance_score * 100)}% match
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {/* Artist portrait */}
                  <div className="bg-neutral-100 rounded-lg h-64 flex items-center justify-center overflow-hidden border border-neutral-200">
                    {artist.portrait_url ? (
                      <img
                        src={artist.portrait_url}
                        alt={artist.name}
                        className="w-full h-full object-contain"
                        onError={(e) => {
                          // Fallback if image fails to load
                          e.currentTarget.style.display = 'none';
                          e.currentTarget.parentElement!.innerHTML = `
                            <div class="text-center text-muted-foreground">
                              <svg class="h-12 w-12 mx-auto mb-2 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                              </svg>
                              <p class="text-xs">Portrait unavailable</p>
                            </div>
                          `;
                        }}
                      />
                    ) : (
                      <div className="text-center text-[var(--brand-muted)]">
                        <User className="h-12 w-12 mx-auto mb-2 opacity-30" />
                        <p className="text-xs">No portrait available</p>
                      </div>
                    )}
                  </div>

                  <p className="text-sm text-[var(--brand-ink)]">{artist.biography_short}</p>

                  {/* Europeana-First: Availability Metrics */}
                  {artist.availability && (
                    <div className="bg-gradient-to-br from-[var(--brand-accent)]/5 to-[var(--brand-accent)]/10 rounded-lg p-3 border border-[var(--brand-accent)]/20">
                      <p className="text-xs font-semibold text-[var(--brand-ink)] mb-2 flex items-center gap-1">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Availability Proof
                      </p>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-[var(--brand-muted)]">Available Works:</span>
                          <span className="ml-1 font-bold text-[var(--brand-primary)]">{artist.availability.totalWorks}</span>
                        </div>
                        <div>
                          <span className="text-[var(--brand-muted)]">IIIF Images:</span>
                          <span className="ml-1 font-bold text-[var(--brand-primary)]">{artist.availability.iiifAvailability}%</span>
                        </div>
                      </div>
                      <div className="mt-2">
                        <p className="text-xs text-[var(--brand-muted)] mb-1">Institutions ({artist.availability.institutions.length}):</p>
                        <div className="flex flex-wrap gap-1">
                          {artist.availability.institutions.slice(0, 3).map((inst, i) => (
                            <span key={i} className="text-xs bg-white px-2 py-0.5 rounded border border-[var(--brand-accent)]/30 text-[var(--brand-ink)]">
                              {inst}
                            </span>
                          ))}
                          {artist.availability.institutions.length > 3 && (
                            <span className="text-xs text-[var(--brand-muted)]">+{artist.availability.institutions.length - 3} more</span>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {artist.movements.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-[var(--brand-muted)] mb-1">Movements:</p>
                      <div className="flex flex-wrap gap-1">
                        {artist.movements.map((movement, i) => (
                          <Badge
                            key={i}
                            variant="secondary"
                            className="text-xs bg-[var(--brand-accent)]/15 text-[var(--brand-ink)]"
                          >
                            {movement}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {artist.major_works.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-[var(--brand-muted)] mb-1">Major Works:</p>
                      <p className="text-xs text-[var(--brand-muted)]">
                        {artist.major_works.slice(0, 3).join(", ")}
                      </p>
                    </div>
                  )}

                  <div className="pt-2 border-t border-neutral-200 space-y-2">
                    <div>
                      <p className="text-xs font-semibold text-[var(--brand-muted)] mb-1">Why this artist?</p>
                      <p className="text-xs text-[var(--brand-muted)] italic">
                        {artist.relevance_reasoning}
                      </p>
                    </div>
                    {artist.wikipedia_url && (
                      <a
                        href={artist.wikipedia_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-[var(--brand-primary)] hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <ExternalLink className="h-3 w-3" />
                        View on Wikipedia
                      </a>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
          })}
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <Card className="border-neutral-200 bg-white">
            <CardContent className="pt-4">
              <div className="flex items-center justify-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(1)}
                  disabled={currentPage === 1}
                  className="border-[var(--brand-primary)]/30"
                >
                  First
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="border-[var(--brand-primary)]/30"
                >
                  <ArrowLeft className="h-4 w-4" />
                </Button>

                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }

                    return (
                      <Button
                        key={pageNum}
                        variant={currentPage === pageNum ? "default" : "outline"}
                        size="sm"
                        onClick={() => setCurrentPage(pageNum)}
                        className={currentPage === pageNum ? "bg-[var(--brand-primary)] text-white" : "border-[var(--brand-primary)]/30"}
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="border-[var(--brand-primary)]/30"
                >
                  <ArrowRight className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(totalPages)}
                  disabled={currentPage === totalPages}
                  className="border-[var(--brand-primary)]/30"
                >
                  Last
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        <Card className="relative overflow-hidden border-neutral-200 bg-white shadow-sm sticky bottom-6">
          <div className="pointer-events-none absolute inset-x-0 top-0 h-[2px] w-full bg-[var(--brand-primary)]/80" />
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
              <Button
                onClick={() => router.push("/demo/theme")}
                variant="outline"
                className="border-[var(--brand-primary)]/30 text-[var(--brand-primary)] hover:bg-[var(--brand-accent)]/10 w-full sm:w-auto"
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Theme
              </Button>
              <div className="text-sm text-[var(--brand-muted)]">
                {selectedCount < targetCount && `Select ${targetCount - selectedCount} more artist${targetCount - selectedCount === 1 ? '' : 's'}`}
                {selectedCount >= targetCount && <span className="text-[var(--brand-primary)] font-medium">✓ Ready to continue!</span>}
              </div>
              <Button
                onClick={handleContinue}
                disabled={selectedCount < 1}
                className="bg-[var(--brand-primary)] hover:bg-[var(--brand-primary-600)] text-white w-full sm:w-auto"
              >
                Continue to Artworks
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
