// Exhibition data types based on backend WebSocket API

export interface ThemeRefinement {
  exhibition_title: string;
  subtitle: string | null;
  curatorial_statement: string;
  scholarly_rationale: string;
  target_audience_refined: string;
  complexity_level: string;
  key_themes: string[];
  historical_context: string;
}

export interface Artist {
  wikidata_id: string;
  name: string;
  birth_year: number | null;
  death_year: number | null;
  nationality: string | null;
  movement: string | null;
  biography: string;
  relevance_score: number;
  relevance_reasoning: string;
  artworks_count?: number;
}

export interface Artwork {
  identifier: string;
  title: string;
  artist_name: string;
  artist_wikidata_id: string;
  date_created: string | null;
  medium: string | null;
  institution_name: string | null;
  institution_id: string | null;
  image_url: string | null;
  iiif_manifest: string | null;
  height_cm: number | null;
  width_cm: number | null;
  relevance_score: number;
  curatorial_note: string;
}

export interface ArtistDiscoveryData {
  artists: Artist[];
  total_candidates: number;
  selection_criteria: string;
}

export interface ArtworkDiscoveryData {
  artworks: Artwork[];
  total_candidates: number;
  coverage_summary: {
    total_artworks: number;
    with_iiif: number;
    iiif_percentage: number;
  };
}

// WebSocket message types
export type WebSocketMessageType =
  | "connected"
  | "progress"
  | "stage_complete"
  | "completed"
  | "error";

export type Stage =
  | "theme_refinement"
  | "artist_discovery"
  | "artwork_discovery";

export interface WebSocketMessage {
  type: WebSocketMessageType;
  message?: string;
  progress?: number;
  stage?: string;
  completed_stage?: Stage;
  data?: ThemeRefinement | ArtistDiscoveryData | ArtworkDiscoveryData;
  proposal_url?: string;
  error?: string;
}

// Generation state
export interface GenerationState {
  status: "idle" | "connecting" | "generating" | "completed" | "error";
  progress: number;
  currentStage: Stage | null;
  theme: ThemeRefinement | null;
  artists: ArtistDiscoveryData | null;
  artworks: ArtworkDiscoveryData | null;
  error: string | null;
  proposalUrl: string | null;
}
