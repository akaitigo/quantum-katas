/** Base URL for all API requests. */
export const API_BASE_URL = "/api";

/** Category display labels. */
export const CATEGORY_LABELS: Record<string, string> = {
  basics: "Basics",
  entanglement: "Entanglement",
  algorithms: "Algorithms",
};

/** Category display order. */
export const CATEGORY_ORDER: readonly string[] = [
  "basics",
  "entanglement",
  "algorithms",
];

/** Total number of katas in the curriculum. */
export const TOTAL_KATAS = 10;

/** Key used for localStorage progress storage. */
export const PROGRESS_STORAGE_KEY = "quantum-katas-progress";
