"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ArrowLeft, Download, Share2, ExternalLink, FileJson } from "lucide-react";
import type { GenerationState } from "@/types/exhibition";
import { IIIFViewer } from "@/components/iiif-viewer";

export default function ProposalPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [proposalData, setProposalData] = useState<GenerationState | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Try to load from sessionStorage first
    const storedState = sessionStorage.getItem(`exhibition_state_${sessionId}`);
    if (storedState) {
      const state: GenerationState = JSON.parse(storedState);
      setProposalData(state);
      setLoading(false);
    } else {
      // TODO: Fetch from API if not in session storage
      // For now, redirect back to home
      router.push("/");
    }
  }, [sessionId, router]);

  const handlePrint = () => {
    window.print();
  };

  const handleShare = async () => {
    const url = window.location.href;
    if (navigator.share) {
      try {
        await navigator.share({
          title: proposalData?.theme?.exhibition_title || "Exhibition Proposal",
          url: url,
        });
      } catch (err) {
        // User cancelled or error occurred
      }
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(url);
      alert("Link copied to clipboard!");
    }
  };

  const handleExportJSON = () => {
    if (!proposalData) return;

    const exportData = {
      session_id: sessionId,
      exported_at: new Date().toISOString(),
      theme: proposalData.theme,
      artists: proposalData.artists,
      artworks: proposalData.artworks,
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `exhibition-proposal-${sessionId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading || !proposalData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">Loading proposal...</p>
      </div>
    );
  }

  const { theme, artists, artworks } = proposalData;

  if (!theme || !artists || !artworks) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-muted-foreground">Incomplete proposal data</p>
          <Button onClick={() => router.push("/")}>Return Home</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Action Bar - Hidden in print */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b print-hidden">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Button variant="ghost" onClick={() => router.push("/")}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              New Proposal
            </Button>
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleShare}>
                <Share2 className="mr-2 h-4 w-4" />
                Share
              </Button>
              <Button variant="outline" onClick={handleExportJSON}>
                <FileJson className="mr-2 h-4 w-4" />
                Export JSON
              </Button>
              <Button onClick={handlePrint}>
                <Download className="mr-2 h-4 w-4" />
                Export PDF
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Proposal Content */}
      <div className="container mx-auto px-4 py-12 max-w-5xl">
        <div className="space-y-12">
          {/* Exhibition Header */}
          <div className="space-y-6 text-center">
            <div className="space-y-2">
              <h1 className="text-5xl font-bold tracking-tight">{theme.exhibition_title}</h1>
              {theme.subtitle && (
                <p className="text-2xl text-muted-foreground font-light">{theme.subtitle}</p>
              )}
            </div>
            <div className="flex justify-center gap-3">
              <Badge variant="secondary" className="text-sm">
                {theme.target_audience_refined}
              </Badge>
              <Badge variant="secondary" className="text-sm">
                {theme.complexity_level}
              </Badge>
            </div>
          </div>

          <Separator />

          {/* Curatorial Statement */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold">Curatorial Statement</h2>
            <p className="text-lg leading-relaxed text-muted-foreground">
              {theme.curatorial_statement}
            </p>
          </section>

          {/* Scholarly Rationale */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold">Scholarly Rationale</h2>
            <p className="text-lg leading-relaxed text-muted-foreground">
              {theme.scholarly_rationale}
            </p>
          </section>

          {/* Key Themes */}
          {theme.key_themes && theme.key_themes.length > 0 && (
            <section className="space-y-4">
              <h2 className="text-3xl font-bold">Key Themes</h2>
              <div className="flex flex-wrap gap-2">
                {theme.key_themes.map((themeItem, index) => (
                  <Badge key={index} variant="outline" className="text-base py-2 px-4">
                    {themeItem}
                  </Badge>
                ))}
              </div>
            </section>
          )}

          {/* Historical Context */}
          {theme.historical_context && (
            <section className="space-y-4">
              <h2 className="text-3xl font-bold">Historical Context</h2>
              <p className="text-lg leading-relaxed text-muted-foreground">
                {theme.historical_context}
              </p>
            </section>
          )}

          <Separator />

          {/* Featured Artists */}
          <section className="space-y-6">
            <div>
              <h2 className="text-3xl font-bold mb-2">Featured Artists</h2>
              <p className="text-muted-foreground">
                {artists.artists.length} artists selected from {artists.total_candidates} candidates
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {artists.artists.map((artist) => (
                <Card key={artist.wikidata_id} className="overflow-hidden">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-xl">{artist.name}</CardTitle>
                        <CardDescription>
                          {artist.birth_year} - {artist.death_year || "present"}
                          {artist.nationality && ` · ${artist.nationality}`}
                        </CardDescription>
                      </div>
                      <Badge variant="secondary">
                        {(artist.relevance_score * 100).toFixed(0)}%
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-sm text-muted-foreground">{artist.biography}</p>
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Why this artist?</p>
                      <p className="text-sm text-muted-foreground">{artist.relevance_reasoning}</p>
                    </div>
                    {artist.movement && (
                      <Badge variant="outline" className="mt-2">
                        {artist.movement}
                      </Badge>
                    )}
                    <Button variant="link" className="p-0 h-auto text-xs" asChild>
                      <a
                        href={`https://www.wikidata.org/wiki/${artist.wikidata_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        View on Wikidata <ExternalLink className="ml-1 h-3 w-3" />
                      </a>
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <Separator />

          {/* Artwork Selection */}
          <section className="space-y-6">
            <div>
              <h2 className="text-3xl font-bold mb-2">Artwork Selection</h2>
              <p className="text-muted-foreground">
                {artworks.artworks.length} artworks ·{" "}
                {artworks.coverage_summary.with_iiif} with high-resolution IIIF viewer (
                {artworks.coverage_summary.iiif_percentage.toFixed(0)}%)
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {artworks.artworks.map((artwork) => (
                <Card key={artwork.identifier} className="overflow-hidden">
                  {artwork.image_url && (
                    <div className="relative aspect-[3/4] bg-muted overflow-hidden group">
                      <img
                        src={artwork.image_url}
                        alt={artwork.title}
                        className="object-cover w-full h-full hover:scale-105 transition-transform duration-300"
                      />
                      {artwork.iiif_manifest && (
                        <>
                          <Badge className="absolute top-2 right-2" variant="secondary">
                            IIIF
                          </Badge>
                          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                            <IIIFViewer
                              manifestUrl={artwork.iiif_manifest}
                              artworkTitle={artwork.title}
                              artistName={artwork.artist_name}
                            />
                          </div>
                        </>
                      )}
                    </div>
                  )}
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base line-clamp-2">{artwork.title}</CardTitle>
                    <CardDescription className="text-xs">
                      {artwork.artist_name}
                      {artwork.date_created && ` · ${artwork.date_created}`}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {artwork.medium && (
                      <p className="text-xs text-muted-foreground">{artwork.medium}</p>
                    )}
                    {artwork.height_cm && artwork.width_cm && (
                      <p className="text-xs text-muted-foreground">
                        {artwork.height_cm} × {artwork.width_cm} cm
                      </p>
                    )}
                    {artwork.institution_name && (
                      <p className="text-xs font-medium">{artwork.institution_name}</p>
                    )}
                    <p className="text-xs text-muted-foreground italic">
                      {artwork.curatorial_note}
                    </p>
                    <Badge variant="outline" className="text-xs">
                      {(artwork.relevance_score * 100).toFixed(0)}% match
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          {/* Footer */}
          <div className="text-center text-sm text-muted-foreground pt-12 print-hidden">
            <p>Generated by AI Curator Assistant</p>
            <p className="mt-1">Session ID: {sessionId}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
