"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useExhibitionGeneration } from "@/hooks/useExhibitionGeneration";
import { CuratorBrief } from "@/types/curator";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle2, XCircle, Sparkles, Users, Palette } from "lucide-react";
import { IIIFViewer } from "@/components/iiif-viewer";

export default function GeneratePage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [curatorBrief, setCuratorBrief] = useState<CuratorBrief | null>(null);

  // Load curator brief from session storage
  useEffect(() => {
    const storedBrief = sessionStorage.getItem(`curator_brief_${sessionId}`);

    if (storedBrief) {
      setCuratorBrief(JSON.parse(storedBrief));
    } else {
      // If no brief found, redirect back to home
      router.push("/");
    }
  }, [sessionId, router]);

  const { state, connect, isConnected } = useExhibitionGeneration({
    sessionId,
    curatorBrief: curatorBrief!,
    automaticMode: false, // Always human-in-the-loop
    autoStart: !!curatorBrief,
  });

  // Handle page visibility change - reconnect if user returns to tab
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible" && curatorBrief && state.status === "generating" && !isConnected) {
        console.log("Page became visible, attempting to reconnect...");
        connect();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [curatorBrief, state.status, isConnected, connect]);

  // Redirect to proposal page when completed
  useEffect(() => {
    if (state.status === "completed" && state.proposalUrl) {
      router.push(`/proposal/${sessionId}`);
    }
  }, [state.status, state.proposalUrl, sessionId, router]);

  if (!curatorBrief) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  const getStageIcon = (stage: string) => {
    switch (stage) {
      case "theme_refinement":
        return <Sparkles className="h-5 w-5" />;
      case "artist_discovery":
        return <Users className="h-5 w-5" />;
      case "artwork_discovery":
        return <Palette className="h-5 w-5" />;
      default:
        return <Loader2 className="h-5 w-5 animate-spin" />;
    }
  };

  const getStageLabel = (stage: string) => {
    switch (stage) {
      case "theme_refinement":
        return "Refining Exhibition Theme";
      case "artist_discovery":
        return "Discovering Artists";
      case "artwork_discovery":
        return "Discovering Artworks";
      default:
        return "Preparing...";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Header */}
          <div className="text-center space-y-4">
            <h1 className="text-4xl font-bold tracking-tight">
              Generating Exhibition Proposal
            </h1>
            <p className="text-lg text-muted-foreground">
              {curatorBrief.theme_title}
            </p>
          </div>

          {/* Error State */}
          {state.status === "error" && (
            <Card className="border-destructive">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <XCircle className="h-5 w-5 text-destructive" />
                  <CardTitle className="text-destructive">Generation Failed</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm mb-4">{state.error}</p>
                <div className="flex gap-2">
                  <Button onClick={connect} variant="outline">
                    Try Again
                  </Button>
                  <Button onClick={() => router.push("/")} variant="ghost">
                    Back to Form
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Idle state with existing progress - allow reconnect */}
          {state.status === "idle" && (state.theme || state.artists || state.artworks) && (
            <Card className="border-yellow-500/50">
              <CardHeader>
                <CardTitle>Session Recovery</CardTitle>
                <CardDescription>
                  We found existing progress for this session. You can continue or start fresh.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>Last Progress</span>
                    <span>{Math.round(state.progress)}%</span>
                  </div>
                  <Progress value={state.progress} className="h-2" />
                </div>
                <div className="flex gap-2">
                  <Button onClick={connect}>
                    Continue Generation
                  </Button>
                  <Button onClick={() => router.push("/")} variant="outline">
                    Start New
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Progress Card */}
          {(state.status === "connecting" || state.status === "generating") && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {state.currentStage && getStageIcon(state.currentStage)}
                    <CardTitle>
                      {state.currentStage ? getStageLabel(state.currentStage) : "Connecting..."}
                    </CardTitle>
                  </div>
                  <Badge variant={isConnected ? "default" : "secondary"}>
                    {isConnected ? "Connected" : "Connecting..."}
                  </Badge>
                </div>
                <CardDescription>
                  This may take 15-25 minutes. The backend is doing real curatorial research with AI, Wikipedia, and museum databases. Results will appear when each stage completes. Safe to close this tab - progress is saved.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>Progress</span>
                    <span>{Math.round(state.progress)}%</span>
                  </div>
                  <Progress value={state.progress} className="h-2" />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Theme Refinement Result */}
          {state.theme && (
            <Card className="border-green-500/50">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  <CardTitle>Exhibition Theme</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h3 className="text-2xl font-bold mb-1">{state.theme.exhibition_title}</h3>
                  {state.theme.subtitle && (
                    <p className="text-lg text-muted-foreground">{state.theme.subtitle}</p>
                  )}
                </div>

                <div className="flex gap-2">
                  <Badge variant="secondary">{state.theme.target_audience_refined}</Badge>
                  <Badge variant="secondary">{state.theme.complexity_level}</Badge>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Curatorial Statement</h4>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {state.theme.curatorial_statement}
                  </p>
                </div>

                {state.theme.key_themes && state.theme.key_themes.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2">Key Themes</h4>
                    <div className="flex flex-wrap gap-2">
                      {state.theme.key_themes.map((theme, index) => (
                        <Badge key={index} variant="outline">
                          {theme}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Artist Discovery Result */}
          {state.artists && (
            <Card className="border-green-500/50">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  <CardTitle>Discovered Artists</CardTitle>
                </div>
                <CardDescription>
                  {state.artists.artists.length} artists selected from {state.artists.total_candidates} candidates
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {state.artists.artists.map((artist, index) => (
                    <div key={artist.wikidata_id} className="border-l-2 border-primary pl-4">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h4 className="font-semibold">{artist.name}</h4>
                          <p className="text-sm text-muted-foreground">
                            {artist.birth_year} - {artist.death_year || "present"}
                            {artist.nationality && ` · ${artist.nationality}`}
                          </p>
                        </div>
                        <Badge variant="secondary">
                          {(artist.relevance_score * 100).toFixed(0)}% match
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">
                        {artist.relevance_reasoning}
                      </p>
                      {artist.movement && (
                        <Badge variant="outline" className="text-xs">
                          {artist.movement}
                        </Badge>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Artwork Discovery Result */}
          {state.artworks && (
            <Card className="border-green-500/50">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  <CardTitle>Discovered Artworks</CardTitle>
                </div>
                <CardDescription>
                  {state.artworks.artworks.length} artworks selected ·{" "}
                  {state.artworks.coverage_summary.with_iiif} with IIIF viewer (
                  {state.artworks.coverage_summary.iiif_percentage.toFixed(0)}%)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {state.artworks.artworks.slice(0, 6).map((artwork) => (
                    <div key={artwork.identifier} className="border rounded-lg p-4 space-y-2">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold text-sm">{artwork.title}</h4>
                          <p className="text-xs text-muted-foreground">{artwork.artist_name}</p>
                        </div>
                        {artwork.iiif_manifest && (
                          <Badge variant="secondary" className="text-xs ml-2">
                            IIIF
                          </Badge>
                        )}
                      </div>
                      {artwork.image_url && (
                        <div className="relative aspect-video w-full bg-muted rounded overflow-hidden group">
                          <img
                            src={artwork.image_url}
                            alt={artwork.title}
                            className="object-cover w-full h-full"
                          />
                          {artwork.iiif_manifest && (
                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                              <IIIFViewer
                                manifestUrl={artwork.iiif_manifest}
                                artworkTitle={artwork.title}
                                artistName={artwork.artist_name}
                              />
                            </div>
                          )}
                        </div>
                      )}
                      <p className="text-xs text-muted-foreground">
                        {artwork.date_created} · {artwork.institution_name}
                      </p>
                      <Badge variant="outline" className="text-xs">
                        {(artwork.relevance_score * 100).toFixed(0)}% match
                      </Badge>
                    </div>
                  ))}
                </div>
                {state.artworks.artworks.length > 6 && (
                  <p className="text-center text-sm text-muted-foreground mt-4">
                    +{state.artworks.artworks.length - 6} more artworks in full proposal
                  </p>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
