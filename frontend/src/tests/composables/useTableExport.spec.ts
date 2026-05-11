import { describe, expect, it, vi, beforeEach } from 'vitest'
import { useTableExport } from '../../composables/useTableExport'

vi.mock('xlsx', () => ({
  utils: {
    aoa_to_sheet: vi.fn((data: unknown[][]) => ({ data })),
    book_new: () => ({ sheets: {} as Record<string, unknown> }),
    book_append_sheet: (wb: { sheets: Record<string, unknown> }, ws: unknown, name: string) => {
      wb.sheets[name] = ws
    },
  },
  writeFile: vi.fn(),
}))

describe('useTableExport', () => {
  let mockAoaToSheet: ReturnType<typeof vi.fn>
  let mockWriteFile: ReturnType<typeof vi.fn>

  beforeEach(async () => {
    const XLSX = await import('xlsx')
    mockAoaToSheet = vi.mocked(XLSX.utils.aoa_to_sheet)
    mockWriteFile = vi.mocked(XLSX.writeFile)
    mockAoaToSheet.mockClear()
    mockWriteFile.mockClear()
  })
  it('calls writeFile with .xlsx extension', () => {
    const { exportToExcel } = useTableExport()
    const rows = [{ name: 'Alice', amount: 100 }]
    const cols = [
      { field: 'name', header: 'Nom' },
      { field: 'amount', header: 'Montant' },
    ]

    exportToExcel(rows, cols, 'test-export')

    expect(mockWriteFile).toHaveBeenCalledWith(expect.anything(), 'test-export.xlsx')
  })

  it('keeps .xlsx suffix when already provided', () => {
    const { exportToExcel } = useTableExport()

    exportToExcel([], [], 'my-file.xlsx')

    expect(mockWriteFile).toHaveBeenCalledWith(expect.anything(), 'my-file.xlsx')
  })

  it('maps row fields to column headers order', () => {
    const { exportToExcel } = useTableExport()
    const rows = [{ b: 2, a: 1 }]
    const cols = [
      { field: 'a', header: 'Col A' },
      { field: 'b', header: 'Col B' },
    ]

    exportToExcel(rows, cols, 'order-test')

    expect(mockAoaToSheet).toHaveBeenCalledWith([['Col A', 'Col B'], [1, 2]])
  })

  it('replaces missing fields with empty string', () => {
    const { exportToExcel } = useTableExport()
    const rows = [{ a: 'hello' }]
    const cols = [
      { field: 'a', header: 'A' },
      { field: 'missing', header: 'B' },
    ]

    exportToExcel(rows, cols, 'missing-test')

    expect(mockAoaToSheet).toHaveBeenCalledWith([['A', 'B'], ['hello', '']])
  })
})
