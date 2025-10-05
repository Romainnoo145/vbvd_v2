"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { ArrowRight, ArrowLeft, Image as ImageIcon, Ruler, MapPin, ExternalLink, Sparkles, CheckCircle, Award } from "lucide-react";
import { DEMO_ARTWORKS } from "@/lib/demo-data";

export default function DemoArtworksPage() {
  const router = useRouter();
  const [artworks, setArtworks] = useState(DEMO_ARTWORKS.map(a => ({ ...a })));

  const selectedCount = artworks.filter(a => a.selected).length;
  const targetCount = 50;

  const toggleArtwork = (index: number) => {
    const newArtworks = [...artworks];
    newArtworks[index].selected = !newArtworks[index].selected;
    setArtworks(newArtworks);
  };

  const handleComplete = () => {
    if (selectedCount < 1) {
      alert("Please select at least 1 artwork to complete the exhibition");
      return;
    }

    // Store selected artworks
    const selected = artworks.filter(a => a.selected);
    sessionStorage.setItem('demo_selected_artworks', JSON.stringify(selected));

    // In real app, this would generate final exhibition proposal
    alert(`Exhibition complete! ${selectedCount} artworks selected.\n\nIn the full application, this would generate a complete exhibition proposal with quality metrics and export options.`);
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
                      Phase 3
                    </Badge>
                  </div>
                  <CardTitle className="text-3xl text-[var(--brand-ink)]">Artwork Discovery</CardTitle>
                  <CardDescription className="mt-2 text-[var(--brand-muted)]">
                    Select {targetCount} artworks for your exhibition "Dreams & Reality: The Surrealist Revolution"
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
            <CardContent className="pt-6 space-y-3">
              <div className="flex items-start gap-3">
                <Sparkles className="h-5 w-5 text-[var(--brand-primary)] shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-semibold text-[var(--brand-ink)] text-sm mb-1">🎨 Discovered via Europeana-First Architecture</h3>
                  <p className="text-xs text-[var(--brand-muted)]">
                    These artworks were <strong>discovered by searching available artworks</strong> in European collections, ensuring 100% IIIF image quality and proven loan availability.
                    Each artwork includes institution details, rights information, and availability status.
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap gap-2 text-xs ml-8">
                <Badge variant="secondary" className="bg-green-50 text-green-700 border-green-200">
                  ✓ IIIF High-Quality Images
                </Badge>
                <Badge variant="secondary" className="bg-blue-50 text-blue-700 border-blue-200">
                  ✓ Verified Availability
                </Badge>
                <Badge variant="secondary" className="bg-purple-50 text-purple-700 border-purple-200">
                  ✓ Rights Cleared
                </Badge>
              </div>
              <div className="flex items-start gap-3 pl-8 pt-2">
                <p className="text-xs text-[var(--brand-muted)] italic">
                  <em>Note: This demo shows sample artworks. The full system discovers 100+ candidates from Europeana's 65M+ items.</em>
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Artwork Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {artworks.map((artwork, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + index * 0.05 }}
            >
              <Card
                className={`relative overflow-hidden cursor-pointer transition-all border-neutral-200 bg-white hover:shadow-lg ${
                  artwork.selected
                    ? 'ring-2 ring-[var(--brand-primary)] shadow-md'
                    : 'hover:border-[var(--brand-accent)]'
                }`}
                onClick={() => toggleArtwork(index)}
              >
                {artwork.selected && (
                  <div className="pointer-events-none absolute inset-x-0 top-0 h-1 w-full bg-[var(--brand-primary)]/80" />
                )}
                <CardHeader className={artwork.selected ? "pt-6" : ""}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Checkbox
                          checked={artwork.selected}
                          onCheckedChange={() => toggleArtwork(index)}
                          onClick={(e) => e.stopPropagation()}
                          className="data-[state=checked]:bg-[var(--brand-primary)] data-[state=checked]:border-[var(--brand-primary)]"
                        />
                        <CardTitle className="text-lg text-[var(--brand-ink)]">{artwork.title}</CardTitle>
                      </div>
                      <p className="text-sm text-[var(--brand-muted)] mt-1">{artwork.artist_name}</p>
                      <p className="text-xs text-[var(--brand-muted)]">{artwork.date_created}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <Badge variant="outline" className="border-[var(--brand-accent)]/40 text-[var(--brand-ink)]">
                        {Math.round(artwork.relevance_score * 100)}% match
                      </Badge>
                      {(artwork as any).iiif_quality && (
                        <Badge variant="secondary" className="text-xs bg-green-50 text-green-700 border-green-200">
                          {(artwork as any).iiif_quality}% IIIF
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Europeana Discovery & Availability Badges */}
                  {(artwork as any).source === "Europeana" && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      <Badge variant="secondary" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                        🌍 Discovered via Europeana
                      </Badge>
                      {(artwork as any).availability_status === "Available for loan" && (
                        <Badge variant="secondary" className="text-xs bg-emerald-50 text-emerald-700 border-emerald-200">
                          ✓ Loanable
                        </Badge>
                      )}
                      {(artwork as any).availability_status === "Currently on display" && (
                        <Badge variant="secondary" className="text-xs bg-amber-50 text-amber-700 border-amber-200">
                          ⓘ On Display
                        </Badge>
                      )}
                    </div>
                  )}
                </CardHeader>
                <CardContent className="space-y-3">
                  {/* Artwork image */}
                  <div className="bg-neutral-100 rounded-lg h-48 flex items-center justify-center overflow-hidden border border-neutral-200">
                    {artwork.thumbnail_url ? (
                      <img
                        src={artwork.thumbnail_url}
                        alt={artwork.title}
                        className="w-full h-full object-contain"
                        onError={(e) => {
                          // Fallback if image fails to load
                          e.currentTarget.style.display = 'none';
                          e.currentTarget.parentElement!.innerHTML = `
                            <div class="text-center text-muted-foreground">
                              <svg class="h-12 w-12 mx-auto mb-2 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                              <p class="text-xs">Image unavailable</p>
                            </div>
                          `;
                        }}
                      />
                    ) : (
                      <div className="text-center text-[var(--brand-muted)]">
                        <ImageIcon className="h-12 w-12 mx-auto mb-2 opacity-30" />
                        <p className="text-xs">No image available</p>
                      </div>
                    )}
                  </div>

                  {/* Technical details */}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {artwork.medium && (
                      <div>
                        <p className="font-semibold text-[var(--brand-muted)]">Medium</p>
                        <p className="text-[var(--brand-ink)]">{artwork.medium}</p>
                      </div>
                    )}
                    {artwork.height_cm && artwork.width_cm && (
                      <div>
                        <p className="font-semibold text-[var(--brand-muted)] flex items-center gap-1">
                          <Ruler className="h-3 w-3" />
                          Dimensions
                        </p>
                        <p className="text-[var(--brand-ink)]">{artwork.height_cm} × {artwork.width_cm} cm</p>
                      </div>
                    )}
                  </div>

                  {/* Europeana Availability Information */}
                  {(artwork as any).source === "Europeana" && (
                    <div className="bg-gradient-to-br from-[var(--brand-accent)]/5 to-[var(--brand-accent)]/10 rounded-lg p-3 border border-[var(--brand-accent)]/20">
                      <p className="text-xs font-semibold text-[var(--brand-ink)] mb-2 flex items-center gap-1">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Availability & Rights
                      </p>
                      <div className="space-y-1.5 text-xs">
                        <div className="flex justify-between">
                          <span className="text-[var(--brand-muted)]">Status:</span>
                          <span className="font-medium text-[var(--brand-ink)]">{(artwork as any).availability_status || "Available"}</span>
                        </div>
                        {(artwork as any).data_provider && (
                          <div className="flex justify-between">
                            <span className="text-[var(--brand-muted)]">Provider:</span>
                            <span className="font-medium text-[var(--brand-ink)]">{(artwork as any).data_provider}</span>
                          </div>
                        )}
                        {(artwork as any).country && (
                          <div className="flex justify-between">
                            <span className="text-[var(--brand-muted)]">Country:</span>
                            <span className="font-medium text-[var(--brand-ink)]">{(artwork as any).country}</span>
                          </div>
                        )}
                        {(artwork as any).rights_statement && (
                          <div className="flex justify-between">
                            <span className="text-[var(--brand-muted)]">Rights:</span>
                            <span className="font-medium text-[var(--brand-ink)]">{(artwork as any).rights_statement}</span>
                          </div>
                        )}
                        {(artwork as any).loan_conditions && (
                          <div className="mt-2 pt-2 border-t border-[var(--brand-accent)]/20">
                            <p className="text-[var(--brand-muted)]">Loan: <span className="text-[var(--brand-ink)]">{(artwork as any).loan_conditions}</span></p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {artwork.institution_name && (
                    <div className="text-xs">
                      <p className="font-semibold text-[var(--brand-muted)] flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        Collection
                      </p>
                      <p className="text-[var(--brand-ink)]">{artwork.institution_name}</p>
                    </div>
                  )}

                  <div className="pt-2 border-t border-neutral-200 space-y-2">
                    <div>
                      <p className="text-xs font-semibold text-[var(--brand-muted)] mb-1">Relevance to Exhibition</p>
                      <p className="text-xs text-[var(--brand-muted)] italic">
                        {artwork.relevance_reasoning}
                      </p>
                    </div>
                    {artwork.yale_lux_url && (
                      <a
                        href={artwork.yale_lux_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-[var(--brand-primary)] hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <ExternalLink className="h-3 w-3" />
                        View Details
                      </a>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Action Buttons */}
        <Card className="relative overflow-hidden border-neutral-200 bg-white shadow-sm sticky bottom-6">
          <div className="pointer-events-none absolute inset-x-0 top-0 h-[2px] w-full bg-[var(--brand-primary)]/80" />
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
              <Button
                onClick={() => router.push("/demo/artists")}
                variant="outline"
                className="border-[var(--brand-primary)]/30 text-[var(--brand-primary)] hover:bg-[var(--brand-accent)]/10 w-full sm:w-auto"
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Artists
              </Button>
              <div className="text-sm text-[var(--brand-muted)]">
                {selectedCount < targetCount && `Select ${targetCount - selectedCount} more artwork${targetCount - selectedCount === 1 ? '' : 's'}`}
                {selectedCount >= targetCount && (
                  <span className="text-[var(--brand-primary)] font-medium flex items-center gap-1">
                    <Award className="h-4 w-4" />
                    Exhibition ready!
                  </span>
                )}
              </div>
              <Button
                onClick={handleComplete}
                disabled={selectedCount < 1}
                className="bg-[var(--brand-primary)] hover:bg-[var(--brand-primary-600)] text-white w-full sm:w-auto"
              >
                Complete Exhibition
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
