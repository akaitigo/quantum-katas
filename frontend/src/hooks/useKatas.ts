import { fetchKataDetail, fetchKatas } from "@/lib/api";
import type { KataDetail, KataSummary } from "@/types/kata";
import { useQuery } from "@tanstack/react-query";

/** Fetch all katas as summaries. */
export function useKataList(): {
  katas: KataSummary[];
  isLoading: boolean;
  error: Error | null;
} {
  const { data, isLoading, error } = useQuery({
    queryKey: ["katas"],
    queryFn: fetchKatas,
    staleTime: 5 * 60 * 1000,
  });

  return {
    katas: data ?? [],
    isLoading,
    error: error ?? null,
  };
}

/** Fetch a single kata detail by ID. */
export function useKataDetail(kataId: string): {
  kata: KataDetail | null;
  isLoading: boolean;
  error: Error | null;
} {
  const { data, isLoading, error } = useQuery({
    queryKey: ["kata", kataId],
    queryFn: () => fetchKataDetail(kataId),
    staleTime: 5 * 60 * 1000,
    enabled: kataId.length > 0,
  });

  return {
    kata: data ?? null,
    isLoading,
    error: error ?? null,
  };
}
