// Основные типы для ReAIboot UI

export interface Post {
  id: string;
  message_id: string;
  channel_title: string;
  text: string;
  views: number;
  reactions: number;
  replies: number;
  forwards: number;
  score: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
}

export interface Scenario {
  id: string;
  post_id: string;
  title: string;
  duration: number;
  hook: {
    text: string;
    visual: string;
    voiceover: string;
  };
  insight: {
    text: string;
    visual: string;
    voiceover: string;
  };
  steps: Array<{
    step: number;
    title: string;
    description: string;
    visual: string;
    voiceover: string;
    duration: number;
  }>;
  cta: {
    text: string;
    visual: string;
    voiceover: string;
  };
  hashtags: string[];
  music_suggestion: string;
  status: 'draft' | 'approved' | 'published';
  created_at: string;
}

export interface PromptTemplate {
  name: string;
  description: string;
  system_prompt: string;
  user_prompt: string;
  variables: Record<string, any>;
  model_settings: {
    model: string;
    temperature: number;
    max_tokens: number;
  };
}

export interface AnalyticsData {
  total_posts: number;
  processed_posts: number;
  generated_scenarios: number;
  avg_processing_time: number;
  success_rate: number;
  cost_today: number;
  cost_month: number;
}

export interface FilterOptions {
  date_range: {
    start: string;
    end: string;
  };
  channels: string[];
  score_range: {
    min: number;
    max: number;
  };
  status: string[];
  sort_by: 'date' | 'score' | 'views' | 'engagement';
  sort_order: 'asc' | 'desc';
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Типы для форм
export interface PostFiltersForm {
  dateFrom: string;
  dateTo: string;
  channels: string[];
  minScore: number;
  maxScore: number;
  status: string[];
}

export interface ScenarioForm {
  title: string;
  duration: number;
  hook_text: string;
  hook_visual: string;
  hook_voiceover: string;
  insight_text: string;
  insight_visual: string;
  insight_voiceover: string;
  steps: Array<{
    title: string;
    description: string;
    visual: string;
    voiceover: string;
    duration: number;
  }>;
  cta_text: string;
  cta_visual: string;
  cta_voiceover: string;
  hashtags: string[];
  music_suggestion: string;
}

export interface PromptForm {
  name: string;
  description: string;
  system_prompt: string;
  user_prompt: string;
  variables: Record<string, any>;
  model_settings: {
    model: string;
    temperature: number;
    max_tokens: number;
  };
}
