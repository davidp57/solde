import { ref, watch } from 'vue'

const STORAGE_KEY = 'solde-dark-mode'
const isDark = ref(localStorage.getItem(STORAGE_KEY) === 'true')

// Apply immediately (also done by inline script in index.html to prevent FOUC)
if (isDark.value) {
  document.documentElement.classList.add('dark-mode')
}

// Module-level watcher — runs once, not tied to any component lifecycle
watch(
  isDark,
  (val) => {
    if (val) {
      document.documentElement.classList.add('dark-mode')
    } else {
      document.documentElement.classList.remove('dark-mode')
    }
    localStorage.setItem(STORAGE_KEY, String(val))
  },
  { immediate: false },
)

export function useDarkMode() {
  function toggle() {
    isDark.value = !isDark.value
  }

  return { isDark, toggle }
}
