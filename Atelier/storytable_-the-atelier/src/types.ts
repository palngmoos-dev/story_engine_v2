export type Mode = 'beginner' | 'expert';

export type CardType =
  | 'character' | 'relationship' | 'space' | 'timeline'
  | 'element' | 'cinematic' | 'mood' | 'sense'
  | 'audio' | 'prop' | 'concept' | 'guide';

export type CharacterRole = 'Lead' | 'Support';

export interface NarrativeStats {
  suspicion: number;
  pressure: number;
  echo: number;
}

// ── 인물 & 관계 ──
export interface CharacterCard {
  type: 'character';
  id: string;
  name: string;
  age: string;
  job: string;
  personality: string;
  weakness: string;
  skill: string;
  role: CharacterRole;
  level: number;
  mbti: string;
  bloodType: string;
  upbringing: string;
  relationshipDesc: string;
  hobbies: string;
  car: string;
  gender: 'male' | 'female';
  flaw: string;
  secret: string;
  speechStyle: string;
  background: string;
  baseImpact: NarrativeStats;
}

export interface RelationshipCard {
  type: 'relationship';
  id: string;
  name: string;
  description: string;
  baseImpact: NarrativeStats;
}

// ── 세계관 & 환경 ──
export interface SpaceCard {
  type: 'space';
  id: string;
  name: string;
  description: string;
  modifiers: string;
  baseImpact: NarrativeStats;
}

export interface TimelineCard {
  type: 'timeline';
  id: string;
  era: string;
  vibe: string;
  chronosMode: 'PAST' | 'PRESENT' | 'FUTURE';
  chronosColor: string;
  chronosAesthetic: string;
  baseImpact: NarrativeStats;
}

export interface ElementCard {
  type: 'element';
  id: string;
  name: string;
  theme: string;
  baseImpact: NarrativeStats;
}

// ── 연출 & 감각 ──
export interface CinematicCard {
  type: 'cinematic';
  id: string;
  name: string;
  description: string;
  baseImpact: NarrativeStats;
}

export interface MoodCard {
  type: 'mood';
  id: string;
  name: string;
  baseImpact: NarrativeStats;
}

export interface SenseCard {
  type: 'sense';
  id: string;
  name: string;
  focus: string;
  baseImpact: NarrativeStats;
}

export interface AudioCard {
  type: 'audio';
  id: string;
  name: string;
  description: string;
  category: 'music' | 'ambient';
  baseImpact: NarrativeStats;
}

// ── 서사 & 철학 ──
export interface PropCard {
  type: 'prop';
  id: string;
  name: string;
  description: string;
  baseImpact: NarrativeStats;
}

export interface ConceptCard {
  type: 'concept';
  id: string;
  name: string;
  theme: string;
  baseImpact: NarrativeStats;
}

export interface GuideCard {
  type: 'guide';
  id: string;
  advice: string;
  twist: string;
  baseImpact: NarrativeStats;
}

export type CardData =
  | CharacterCard | RelationshipCard | SpaceCard | TimelineCard
  | ElementCard | CinematicCard | MoodCard | SenseCard
  | AudioCard | PropCard | ConceptCard | GuideCard;

export interface ContiShot {
  shot: string;
  visual: string;
  soundMood: string;
}

export interface DirectorReview {
  stars: number;
  critique: string;
  diagnosis: string;
}

export interface GeneratedStory {
  id?: string;
  title: string;
  logline: string;
  synopsis: string;
  scenes: { title: string; description: string }[];
  videoConti: ContiShot[];
  bgmRecommendation: string;
  directorReview: DirectorReview;
  nextSteps: string;
  createdAt?: any;
  mode?: Mode;
  aggregateStats?: NarrativeStats;
}
