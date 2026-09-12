export type Event = { name: string; amount: string; source_date: string; posted_date: string; kind: 'income' | 'bill' }
export type ProjectedDay = { date: string; opening_balance: string; events: Event[]; closing_balance: string }
export type OptimizationMove = { bill_name: string; original_date: string; new_date: string }
export type Optimization = { moves: OptimizationMove[]; before_min_balance: string; after_min_balance: string; before_negative_days: number; after_negative_days: number; recommendation: string }
export type Override = { id: number; item_id: number; bill_name: string; occurrence_date: string; new_date: string; created_at: string }
export type RecurrenceKind = 'ONCE' | 'WEEKLY' | 'BIWEEKLY' | 'SEMI_MONTHLY' | 'MONTHLY'
export type SavedItem = { item_id: number; kind: 'income' | 'bill'; name: string; amount: string; variance_pct: string; enabled: boolean; recurrence: { kind: RecurrenceKind; anchor: string }; flexibility?: 'FIXED' | 'WINDOW' | 'FLEXIBLE'; window_start?: number; window_end?: number }

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export type AuthResponse = { access_token: string; token_type: string; account_id?: number }
export type AccountExport = { account: { id: number; starting_balance: string; as_of: string }; incomes: SavedItem[]; bills: SavedItem[]; overrides: Override[] }

async function request(path: string, init: RequestInit = {}) {
  const token = localStorage.getItem('cashflow-access-token')
  const headers = new Headers(init.headers)
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API_URL}${path}`, { ...init, headers })
  if (!response.ok) {
    let message = 'Request failed'
    try {
      const body = await response.json() as { detail?: string }
      if (body.detail) message = body.detail
    } catch { message = 'Request failed' }
    throw new Error(message)
  }
  return response
}

export async function register(email: string, password: string) {
  const response = await request('/api/v1/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) })
  return (await response.json()) as AuthResponse
}

export async function login(email: string, password: string) {
  const response = await request('/api/v1/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) })
  return (await response.json()) as AuthResponse
}

export async function createAccount(startingBalance: string, asOf: string) {
  const response = await request('/api/v1/accounts', { method: 'POST', body: JSON.stringify({ starting_balance: startingBalance, as_of: asOf }) })
  return (await response.json()) as { id: number }
}

export async function getProjection(accountId: number, horizonDays = 90) {
  const response = await request(`/api/v1/accounts/${accountId}/projection?horizon_days=${horizonDays}`)
  return (await response.json()) as ProjectedDay[]
}

export async function getOptimization(accountId: number, horizonDays = 90) {
  const response = await request(`/api/v1/accounts/${accountId}/optimization?horizon_days=${horizonDays}`)
  return (await response.json()) as Optimization
}

export async function getItems(accountId: number, kind: 'income' | 'bill') {
  const response = await request(`/api/v1/accounts/${accountId}/${kind === 'income' ? 'incomes' : 'bills'}`)
  return (await response.json()) as SavedItem[]
}

export async function getOverrides(accountId: number) {
  const response = await request(`/api/v1/accounts/${accountId}/overrides`)
  return (await response.json()) as Override[]
}

export async function exportAccount(accountId: number) {
  const response = await request(`/api/v1/accounts/${accountId}/export`)
  return await response.json() as AccountExport
}

export async function deleteAccount(accountId: number) {
  await request(`/api/v1/accounts/${accountId}`, { method: 'DELETE' })
}

export async function createOverride(accountId: number, itemId: number, occurrenceDate: string, newDate: string) {
  const response = await request(`/api/v1/accounts/${accountId}/overrides`, {
    method: 'POST',
    body: JSON.stringify({ item_id: itemId, occurrence_date: occurrenceDate, new_date: newDate }),
  })
  return (await response.json()) as { id: number }
}

export async function deleteOverride(accountId: number, overrideId: number) {
  await request(`/api/v1/accounts/${accountId}/overrides/${overrideId}`, { method: 'DELETE' })
}

export async function deleteItem(accountId: number, item: SavedItem) {
  await request(`/api/v1/accounts/${accountId}/${item.kind === 'income' ? 'incomes' : 'bills'}/${item.item_id}`, { method: 'DELETE' })
}

export async function setItemEnabled(accountId: number, item: SavedItem, enabled: boolean) {
  await request(`/api/v1/accounts/${accountId}/${item.kind === 'income' ? 'incomes' : 'bills'}/${item.item_id}/enabled`, {
    method: 'PATCH',
    body: JSON.stringify({ enabled }),
  })
}

export async function addIncome(accountId: number, name: string, amount: string, anchor: string, recurrence: RecurrenceKind) {
  await request(`/api/v1/accounts/${accountId}/incomes`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, amount, recurrence: { kind: recurrence, anchor } }),
  })
}

export async function updateIncome(accountId: number, itemId: number, name: string, amount: string, anchor: string, recurrence: RecurrenceKind, enabled: boolean) {
  await request(`/api/v1/accounts/${accountId}/incomes/${itemId}`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, amount, enabled, recurrence: { kind: recurrence, anchor } }),
  })
}

export async function addBill(accountId: number, name: string, amount: string, anchor: string, recurrence: RecurrenceKind, flexibility: 'FIXED' | 'WINDOW' | 'FLEXIBLE', windowStart?: number, windowEnd?: number) {
  await request(`/api/v1/accounts/${accountId}/bills`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, amount, flexibility, window_start: windowStart, window_end: windowEnd, recurrence: { kind: recurrence, anchor } }),
  })
}

export async function updateBill(accountId: number, itemId: number, name: string, amount: string, anchor: string, recurrence: RecurrenceKind, flexibility: 'FIXED' | 'WINDOW' | 'FLEXIBLE', windowStart: number | undefined, windowEnd: number | undefined, enabled: boolean) {
  await request(`/api/v1/accounts/${accountId}/bills/${itemId}`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, amount, enabled, flexibility, window_start: windowStart, window_end: windowEnd, recurrence: { kind: recurrence, anchor } }),
  })
}
