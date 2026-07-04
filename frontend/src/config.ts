// Central API base. Empty string = same-origin (the Vite dev proxy forwards /api).
export const API_BASE: string = (import.meta as any).env?.VITE_API_URL || "";
