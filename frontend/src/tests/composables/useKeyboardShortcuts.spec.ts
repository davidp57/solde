import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { beforeEach, describe, expect, it } from 'vitest'

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

  beforeEach(() => {
    calls = { onNew: 0, onSave: 0, onClose: 0 }
    onNew = () => { calls['onNew']! += 1 }
    onSave = () => { calls['onSave']! += 1 }
    onClose = () => { calls['onClose']! += 1 }
  })

  it('calls onNew when Ctrl+N is pressed outside an input', () => {
    const wrapper = mountWithShortcuts({ onNew, onSave, onClose })
    fireKey('n', { ctrlKey: true })
    expect(calls['onNew']).toBe(1)
    wrapper.unmount()
  })

  it('does not call onNew when Ctrl+N is pressed inside an input', () => {
    const wrapper = mountWithShortcuts({ onNew, onSave, onClose })
    const input = document.createElement('input')
    document.body.appendChild(input)
    input.focus()
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'n', ctrlKey: true, bubbles: true }))
    expect(calls['onNew']).toBe(0)
    document.body.removeChild(input)
    wrapper.unmount()
  })

  it('calls onSave when Ctrl+S is pressed', () => {
    const wrapper = mountWithShortcuts({ onNew, onSave, onClose })
    fireKey('s', { ctrlKey: true })
    expect(calls['onSave']).toBe(1)
    wrapper.unmount()
  })

  it('calls onSave when Ctrl+S is pressed inside an input', () => {
    const wrapper = mountWithShortcuts({ onNew, onSave, onClose })
    const input = document.createElement('input')
    document.body.appendChild(input)
    input.focus()
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 's', ctrlKey: true, bubbles: true }))
    expect(calls['onSave']).toBe(1)
    document.body.removeChild(input)
    wrapper.unmount()
  })

  it('calls onClose when Escape is pressed', () => {
    const wrapper = mountWithShortcuts({ onNew, onSave, onClose })
    fireKey('Escape')
    expect(calls['onClose']).toBe(1)
    wrapper.unmount()
  })

  it('does not call any handler for unrelated keys', () => {
    const wrapper = mountWithShortcuts({ onNew, onSave, onClose })
    fireKey('a', { ctrlKey: true })
    fireKey('Enter')
    expect(calls['onNew']).toBe(0)
    expect(calls['onSave']).toBe(0)
    expect(calls['onClose']).toBe(0)
    wrapper.unmount()
  })

  it('removes the listener when the component is unmounted', () => {
    const wrapper = mountWithShortcuts({ onNew, onSave, onClose })
    wrapper.unmount()
    fireKey('n', { ctrlKey: true })
    fireKey('s', { ctrlKey: true })
    fireKey('Escape')
    expect(calls['onNew']).toBe(0)
    expect(calls['onSave']).toBe(0)
    expect(calls['onClose']).toBe(0)
  })

  it('works with Cmd key (Meta) on macOS', () => {
    const wrapper = mountWithShortcuts({ onNew, onSave, onClose })
    fireKey('n', { metaKey: true })
    expect(calls['onNew']).toBe(1)
    fireKey('s', { metaKey: true })
    expect(calls['onSave']).toBe(1)
    wrapper.unmount()
  })

  it('does not throw when handlers are omitted', () => {
    const wrapper = mountWithShortcuts({})
    expect(() => {
      fireKey('n', { ctrlKey: true })
      fireKey('s', { ctrlKey: true })
      fireKey('Escape')
    }).not.toThrow()
    wrapper.unmount()
  })
})