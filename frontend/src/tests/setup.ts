/**
 * Global test setup for Vitest.
 * Provides a localStorage mock compatible with jsdom and the auth store.
 */

// Minimal localStorage implementation for test environments
const localStorageData: Record<string, string> = {}

const localStorageMock: Storage = {
  getItem(key: string): string | null {
    return Object.prototype.hasOwnProperty.call(localStorageData, key)
      ? (localStorageData[key] ?? null)
      : null
  },
  setItem(key: string, value: string): void {
    localStorageData[key] = String(value)
  },
  removeItem(key: string): void {
    delete localStorageData[key]
  },
  clear(): void {
    Object.keys(localStorageData).forEach((k) => delete localStorageData[k])
  },
  get length(): number {
    return Object.keys(localStorageData).length
  },
  key(index: number): string | null {
    return Object.keys(localStorageData)[index] ?? null
  },
}

Object.defineProperty(globalThis, 'localStorage', {
  value: localStorageMock,
  writable: true,
  configurable: true,
})
