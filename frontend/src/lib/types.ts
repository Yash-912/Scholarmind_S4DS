// TypeScript interfaces for the ScholarMind API

export interface Paper {
  id: number;
  title: string;
  abstract: string | null;
  authors: string[];
  source: string;
  source_id: string;
  doi: string | null;
  published_date: string | null;
  categories: string[];
  citation_count: number;
  novelty_score: number;
  pdf_url: string | null;
  created_at: string;
}

export interface Topic {
  id: number;
  name: string;
  keywords: string[];
  paper_count: number;
  trend_direction: "rising" | "stable" | "declining";
  coherence_score: number;
}

export interface SearchResult {
  paper_id: string;
  title: string;
  snippet: string;
  score: number;
  source: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  count: number;
  reranked: boolean;
  latency_ms: number;
}

export interface SynthesisRequest {
  query: string;
  query_type?: string;
  top_k?: number;
  rerank?: boolean;
  stream?: boolean;
}

export interface SynthesisResponse {
  answer: string;
  query_type: string;
  papers: SearchResult[];
  metrics: SynthesisMetrics;
  hallucination_check: HallucinationResult;
  cached: boolean;
}

export interface SynthesisMetrics {
  latency_ms: number;
  papers_retrieved: number;
  papers_reranked: number;
  model: string;
  cost_usd: number;
}

export interface HallucinationResult {
  score: number;
  verdict: string;
  details: string;
}

export interface FeedPaper extends Paper {
  relevance_score: number;
  paper_id: string;
}

export interface FeedResponse {
  feed: FeedPaper[];
  interests: string[];
  bookmarks: number[];
}

export interface DashboardData {
  metrics: SystemMetrics;
  query_stats: QueryStats;
  ingestion_stats: IngestionStats;
  alerts: Alert[];
}

export interface SystemMetrics {
  system: {
    cpu_percent: number;
    memory_used_mb: number;
    memory_percent: number;
    disk_used_gb: number;
  };
  vector_store: {
    total_vectors: number;
  };
  cache: {
    size: number;
    max_size: number;
    hit_rate: number;
    threshold: number;
  };
  cost: {
    hourly_spend_usd: number;
    hourly_limit_usd: number;
    over_budget: boolean;
    utilization_pct: number;
  };
}

export interface QueryStats {
  total_queries: number;
  avg_latency_ms: number;
  total_cost_usd: number;
  avg_faithfulness: number;
}

export interface IngestionStats {
  total_runs: number;
  total_new_papers: number;
  total_duplicates: number;
  avg_duration_seconds: number;
}

export interface Alert {
  id: number;
  name: string;
  severity: "info" | "warning" | "critical";
  message: string;
  resolved: boolean;
  created_at: string;
}

export interface ModelVersion {
  id: number;
  name: string;
  version: string;
  model_type: string;
  is_active: boolean;
  registered_at: string;
  metrics: Record<string, number>;
}

export interface ScalingAdvice {
  category: string;
  severity: string;
  title: string;
  description: string;
  recommendation: string;
}

export interface Conference {
  name: string;
  field: string;
  conference_date: string;
  surge_starts: string;
  days_until_surge: number;
}
