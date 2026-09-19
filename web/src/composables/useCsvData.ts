const cache = new Map<string, any[]>()

function parseCSV(text: string): any[] {
  const lines = text.trim().split('\n').filter(l => l.trim())
  if (lines.length < 2) return []
  
  // 清理BOM头
  const headerLine = lines[0].replace(/^\uFEFF/, '')
  const headers = headerLine.split(',').map(h => h.trim().replace(/^"|"$/g, ''))
  
  const result: any[] = []
  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map(v => v.trim().replace(/^"|"$/g, ''))
    const row: any = {}
    headers.forEach((h, idx) => {
      const rawVal = values[idx] ?? ''
      // 尝试转为数字
      const numVal = Number(rawVal)
      // 空字符串列名也保留
      row[h] = rawVal !== '' && !isNaN(numVal) && rawVal.trim() !== '' ? numVal : rawVal
    })
    result.push(row)
  }
  return result
}

export function useCsvData() {
  async function loadCsv(path: string): Promise<any[]> {
    if (cache.has(path)) {
      return cache.get(path)!
    }

    const response = await fetch(path)
    if (!response.ok) {
      throw new Error(`Failed to load CSV: ${path}`)
    }
    const csvText = await response.text()
    const data = parseCSV(csvText)
    cache.set(path, data)
    return data
  }

  function clearCache() {
    cache.clear()
  }

  return { loadCsv, clearCache }
}
