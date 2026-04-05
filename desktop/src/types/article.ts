export type Segment = {
  id: string;
  sourceText: string;
  translatedText: string | null;
  startMs: number;
  endMs: number;
};

export type Article = {
  id: string;
  title: string;
  status: "imported" | "processing" | "ready" | "failed";
  createdAt: string;
  audioPath: string | null;
  lastPlayedMs: number;
  segments: Segment[];
};
