import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useKeyboardShortcuts } from '../../composables/useKeyboardShortcuts'

function fireKey(key: string, extra: Partial<KeyboardEventInit> = {}): void {
  document.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, ...extra }))
}

function mountWithShortcuts(handlers: Parameters<typeof useKeyboardShortcuts>[0]) {
  const Wrapper = defineComponent({
    setup() {
      useKeyboardShortcuts(handlers)
      return () => h('div')
    },
  })
  return mount(Wrapper, { attachTo: document.body })
}

describe('useKeyboardShortcuts', () => {
  let calls: Record<string, number>
  let onNew: () => void
  let onSave: () => void
  let onClose: () => void
  let activeWrapper: ReturnType<typeof mountWithShortcuts> | null = null

  beforeEach(() => {
    calls = { onNew: 0, onSave: 0, onClose: 0 }
    onNew = () => { calls['onNew']! += 1 }
    onSave = () => { calls['onSave']! += 1 }
    onClose = () => { calls['onClose']! += 1 }
  })

  afterEach(() => {
    activeWrapper?.unmount()
    activeWrapper = null
  })

  it('calls onNew when Ctrl+N is pressed outside an input', () => {
    activeWrapper = mountWithShortcuts({ onNew, onSave, onClose })
    fireKey('n', { ctrlKey: true })
    expect(calls['onNew']).toBe(1)

  })

  it('does not call onNew when Ctrl+N is pressed inside an input', () => {
    activeWrapper = mountWithShortcuts({ onNew, onSave, onClose })
    const input = document.createElement('input')
    document.body.appendChild(input)
    input.focus()
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'n', ctrlKey: true, bubbles: true }))
    expect(calls['onNew']).toBe(0)
    document.body.removeChild(input)

  })

  it('does not call onNew when Ctrl+N is pressed inside a textarea', () => {
    activeWrapper = mountWithShortcuts({ onNew, onSave, onClose })
    const textarea = document.createElement('textarea')
    document.body.appendChild(textarea)
    textarea.focus()
    textarea.dispatchEvent(new KeyboardEvent('keydown', { key: 'n', ctrlKey: true, bubbles: true }))
    expect(calls['onNew']).toBe(0)
    document.body.removeChild(textarea)

  })

  it('does not call onNew when Ctrl+N is pressed inside a select', () => {
    activeWrapper = mountWithShortcuts({ onNew, onSave, onClose })
    const select = document.createElement('select')
    document.body.appendChild(select)
    select.focus()
    select.dispatchEvent(new KeyboardEvent('keydown', { key: 'n', ctrlKey: true, bubbles: true }))
    expect(calls['onNew']).toBe(0)
    document.body.removeChild(select)

  })

  it('does not call onNew when Ctrl+N is pressed inside a contentEditable element', () => {
    activeWrapper = mountWithShortcuts({ onNew, onSave, onClose })
    const div = document.createElement('div')
    div.setAttribute('contenteditable', 'true')
    document.body.appendChild(div)
    div.focus()
    div.dispatchEvent(new KeyboardEvent('keydown', { key: 'n', ctrlKey: true, bubbles: true }))
    expect(calls['onNew']).toBe(0)
    document.body.removeChild(div)

  })

  it('calls onSave when Ctrl+S is pressed', () => {
    activeWrapper = mountWithShortcuts({ onNew, onSave, onClose })
    fireKey('s', { ctrlKey: true })
    expect(calls['onSave']).toBe(1)

  })

  it('calls onSave when Ctrl+S is pressed inside an input', () => {
    activeWrapper = mountWithShortcuts({ onNew, onSave, onClose })
    const input = document.createElement('input')
    document.body.appendChild(input)
    input.focus()
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 's', ctrlKey: true, bubbles: true }))
    expect(calls['onSave']).toBe(1)
    document.body.removeChild(input)

  })

  it('calls onClose when Escape is pressed', () => {
    activeWrapper = mountWithShortcuts({ onNew, onSave, onClose })
    fireKey('Escape')
    expect(calls['onClose']).toBe(1)

  })

  it('does not call any handler for unrelated keys', () => {
    activeWrapper = mountWithShortcuts({ onNew, onSave, onClose })
    fireKey('a', { ctrlKey: true })
    fireKey('Enter')
    expect(calls['onNew']).toBe(0)
    expect(calls['onSave']).toBe(0)
    expect(calls['onClose']).toBe(0)

  })

  it('removes the listener when the component is unmounted', () => {
    activeWrapper = mountWithShortcuts({ onNew, onSave, onClose })
    activeWrapper.unmount()
    activeWrapper = null
    fireKey('n', { ctrlKey: true })
    fireKey('s', { ctrlKey: true })
    fireKey('Escape')
    expect(calls['onNew']).toBe(0)
    expect(calls['onSave']).toBe(0)
    expect(calls['onClose']).toBe(0)
  })

  it('works with Cmd key (Meta) on macOS', () => {
    activeWrapper = mountWithShortcuts({ onNew, onSave, onClose })
    fireKey('n', { metaKey: true })
    expect(calls['onNew']).toBe(1)
    fireKey('s', { metaKey: true })
    expect(calls['onSave']).toBe(1)

  })

  it('does not throw when handlers are omitted', () => {
    activeWrapper = mountWithShortcuts({})
    expect(() => {
      fireKey('n', { ctrlKey: true })
      fireKey('s', { ctrlKey: true })
      fireKey('Escape')
    }).not.toThrow()

  })

  it('skips all handlers when event.defaultPrevented is true', () => {
    activeWrapper = mountWithShortcuts({ onNew, onSave, onClose })
    const preventedEvent = new KeyboardEvent('keydown', { key: 's', ctrlKey: true, bubbles: true, cancelable: true })
    preventedEvent.preventDefault()
    document.dispatchEvent(preventedEvent)
    expect(calls['onSave']).toBe(0)

  })

  it('prevents default browser behavior for Ctrl/Cmd+S', () => {
    activeWrapper = mountWithShortcuts({ onNew, onSave, onClose })
    const event = new KeyboardEvent('keydown', { key: 's', ctrlKey: true, bubbles: true, cancelable: true })
    const spy = vi.spyOn(event, 'preventDefault')
    document.dispatchEvent(event)
    expect(spy).toHaveBeenCalledOnce()

  })

  it('prevents default browser behavior for Ctrl/Cmd+N', () => {
    activeWrapper = mountWithShortcuts({ onNew, onSave, onClose })
    const event = new KeyboardEvent('keydown', { key: 'n', ctrlKey: true, bubbles: true, cancelable: true })
    const spy = vi.spyOn(event, 'preventDefault')
    document.dispatchEvent(event)
    expect(spy).toHaveBeenCalledOnce()

  })

  it('does not prevent default for Escape', () => {
    activeWrapper = mountWithShortcuts({ onNew, onSave, onClose })
    const event = new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true })
    const spy = vi.spyOn(event, 'preventDefault')
    document.dispatchEvent(event)
    expect(spy).not.toHaveBeenCalled()

  })
})
