export interface CuratorBrief {
  theme_title: string;
  theme_description: string;
  theme_concepts: string[];
  reference_artists: string[];
  target_audience: string;
  duration_weeks: number;
}

export type TargetAudience =
  | "general"
  | "academic"
  | "youth"
  | "family"
  | "specialists";

export const TARGET_AUDIENCES: { value: TargetAudience; label: string }[] = [
  { value: "general", label: "General Public" },
  { value: "academic", label: "Academic & Scholars" },
  { value: "youth", label: "Youth & Students" },
  { value: "family", label: "Families" },
  { value: "specialists", label: "Specialists" },
];
