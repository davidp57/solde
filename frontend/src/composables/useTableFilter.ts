import { computed, ref, type Ref } from 'vue'

/** Apply a text query to a plain array (used when sharing filterText across multiple tables). */
export function applyFilter<T>(items: T[], query: string): T[] {
  const q = query.trim().toLowerCase()
  if (!q) return items
  return items.filter(
    (item) =>
      item !== null &&
      item !== undefined &&
      Object.values(item as Record<string, unknown>).some(
        (v) => v !== null && v !== undefined && String(v).toLowerCase().includes(q),
      ),
  )
}

/**
 * Generic client-side fuzzy filter for a single reactive table.
 * Returns `filterText` (bound to InputText) and `filtered` (bound to DataTable :value).
 */
export function useTableFilter<T>(items: Ref<T[]>) {
  const filterText = ref('')

  const filtered = computed<T[]>(() => applyFilter(items.value, filterText.value))

  return { filterText, filtered }
}
