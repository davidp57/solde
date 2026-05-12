import * as XLSX from 'xlsx'

export interface ExportColumn {
  field: string
  header: string
}

export function useTableExport() {
  function exportToExcel(rows: object[], columns: ExportColumn[], filename: string): void {
    const headers = columns.map((c) => c.header)
    const data = rows.map((row) => columns.map((c) => (row as Record<string, unknown>)[c.field] ?? ''))

    const worksheet = XLSX.utils.aoa_to_sheet([headers, ...data])
    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Export')

    const safeFilename = filename.endsWith('.xlsx') ? filename : `${filename}.xlsx`
    XLSX.writeFile(workbook, safeFilename)
  }

  return { exportToExcel }
}
