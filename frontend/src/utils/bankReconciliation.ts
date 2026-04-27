function normalizeReconciliationText(value: string | null | undefined): string {
  return (value ?? '')
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function scoreTextPresence(bankText: string, candidateText: string | null | undefined): number {
  const normalizedCandidate = normalizeReconciliationText(candidateText)
  if (!normalizedCandidate) {
    return 0
  }
  if (bankText.includes(normalizedCandidate)) {
    return normalizedCandidate.length >= 6 ? 80 : 30
  }

  const candidateTokens = normalizedCandidate.split(' ').filter((token) => token.length >= 4)
  return candidateTokens.reduce((score, token) => {
    return score + (bankText.includes(token) ? 18 : 0)
  }, 0)
}

function scoreDateProximity(
  transactionDate: string,
  candidateDate: string | null | undefined,
): number {
  if (!candidateDate) {
    return 0
  }

  const txDate = new Date(transactionDate)
  const otherDate = new Date(candidateDate)
  const dayDelta = Math.abs(otherDate.getTime() - txDate.getTime()) / (1000 * 60 * 60 * 24)

  if (dayDelta <= 3) {
    return 18
  }
  if (dayDelta <= 10) {
    return 12
  }
  if (dayDelta <= 30) {
    return 6
  }
  return 0
}

export interface InvoiceSuggestionInput {
  transactionAmount: number
  transactionDate: string
  transactionDescription: string
  transactionReference?: string | null
  candidateNumber: string
  candidateReference?: string | null
  candidateContactName?: string | null
  candidateDate: string
  candidateRemainingAmount: number
}

export interface PaymentSuggestionInput {
  transactionAmount: number
  transactionDate: string
  transactionDescription: string
  transactionReference?: string | null
  candidateInvoiceNumber?: string | null
  candidateReference?: string | null
  candidateContactName?: string | null
  candidateDate: string
  candidateAmount: number
}

export function scoreInvoiceSuggestion(input: InvoiceSuggestionInput): number {
  const bankText = normalizeReconciliationText(
    `${input.transactionDescription} ${input.transactionReference ?? ''}`,
  )
  const amountDelta = Math.abs(input.candidateRemainingAmount - input.transactionAmount)

  let score = Math.max(0, 120 - Math.round(amountDelta * 100))
  score += scoreTextPresence(bankText, input.candidateNumber)
  score += scoreTextPresence(bankText, input.candidateReference)
  score += scoreTextPresence(bankText, input.candidateContactName)
  score += scoreDateProximity(input.transactionDate, input.candidateDate)
  return score
}

export function scorePaymentSuggestion(input: PaymentSuggestionInput): number {
  const bankText = normalizeReconciliationText(
    `${input.transactionDescription} ${input.transactionReference ?? ''}`,
  )
  const amountDelta = Math.abs(input.candidateAmount - input.transactionAmount)

  let score = Math.max(0, 140 - Math.round(amountDelta * 200))
  score += scoreTextPresence(bankText, input.candidateInvoiceNumber)
  score += scoreTextPresence(bankText, input.candidateReference)
  score += scoreTextPresence(bankText, input.candidateContactName)
  score += scoreDateProximity(input.transactionDate, input.candidateDate)
  return score
}

export { normalizeReconciliationText }
