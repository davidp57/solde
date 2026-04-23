import { onMounted, onUnmounted } from 'vue'

export interface KeyboardShortcutHandlers {
  /** Called when Ctrl+N (or Cmd+N) is pressed outside a text input. Opens a "new" form. */
  onNew?: () => void
  /** Called when Ctrl+S (or Cmd+S) is pressed. Saves the current form. */
  onSave?: () => void
  /** Called when Escape is pressed. Closes the current dialog. */
  onClose?: () => void
}

/**
 * Registers keyboard shortcuts for the calling component:
 * - Ctrl/Cmd+N → onNew (only when focus is not in a text input)
 * - Ctrl/Cmd+S → onSave
 * - Escape     → onClose
 *
 * Listeners are attached on mount and removed on unmount.
 */
export function useKeyboardShortcuts(handlers: KeyboardShortcutHandlers): void {
  function handleKeydown(event: KeyboardEvent): void {
    if (event.defaultPrevented) {
      return
    }

    const target = event.target
    const isEditing =
      target instanceof HTMLElement && (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT' ||
        target.isContentEditable ||
        target.getAttribute('contenteditable') === 'true' ||
        target.getAttribute('contenteditable') === ''
      )

    if (event.key === 'Escape') {
      handlers.onClose?.()
      return
    }

    const hasModifier = event.ctrlKey || event.metaKey

    if (hasModifier && event.key === 's') {
      event.preventDefault()
      handlers.onSave?.()
      return
    }

    if (hasModifier && event.key === 'n' && !isEditing) {
      event.preventDefault()
      handlers.onNew?.()
    }
  }

  onMounted(() => {
    document.addEventListener('keydown', handleKeydown)
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeydown)
  })
}
