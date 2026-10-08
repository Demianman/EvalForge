import type { components } from "./api-schema";

// Public aliases are generated from FastAPI's canonical OpenAPI contract.
// Run `npm run contracts:generate` after backend schema changes.
export type Project = components["schemas"]["ProjectOut"];
export type Dataset = components["schemas"]["DatasetOut"];
export type TestCase = components["schemas"]["TestCaseOut"];
export type Run = components["schemas"]["RunOut"];
export type Result = components["schemas"]["ResultOut"];
export type Dashboard = components["schemas"]["DashboardOut"];
export type RunDetail = components["schemas"]["RunDetail"];
export type Compare = components["schemas"]["CompareOut"];
export type Review = components["schemas"]["ReviewOut"];
export type ReviewInput = components["schemas"]["ReviewIn"];
export type Page<T> = { items:T[]; total:number; page:number; page_size:number };
export type ApiError = { error?:{message?:string} };
