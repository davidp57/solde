export interface FilterLabelOption<T> {
  label: string
  value: T
}

export function findSelectedFilterLabel<T>(
  options: ReadonlyArray<FilterLabelOption<T>>,
  value: T | null | undefined,
): string | undefined {
  if (value === null || value === undefined) {
    return undefined
  }

  const selectedOption = options.find((option) => option.value === value)
  return selectedOption ? selectedOption.label : String(value)
}

export function collectActiveFilterLabels(
  ...labels: Array<string | null | undefined | false>
): string[] {
  return labels.filter((label): label is string => typeof label === 'string' && label.length > 0)
}
