import type { components } from "./schema";

export type Schema = components["schemas"];
export type Me = Schema["Me"];
export type Provider = Schema["ProviderProfile"];
export type Skill = Schema["SkillOut"];
export type RequestItem = Schema["RequestOut"];
export type SessionItem = Schema["SessionOut"];
export type NotificationItem = Schema["NotificationOut"];
export type Suggestion = Schema["SuggestionOut"];
export type Page<T> = { items: T[]; limit: number; offset: number };
