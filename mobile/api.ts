import * as SecureStore from 'expo-secure-store'

export type Event = { name: string; amount: string; source_date: string; posted_date: string; kind: 'income' | 'bill' }
export type ProjectedDay = { date: string; opening_balance: string; events: Event[]; closing_balance: string }
export type RecurrenceKind = 'ONCE' | 'WEEKLY' | 'BIWEEKLY' | 'SEMI_MONTHLY' | 'MONTHLY'
export type AuthResponse = { access_token: string; token_type: string }
export type OptimizationMove = { bill_name: string; original_date: string; new_date: string }
export type Optimization = { moves: OptimizationMove[]; before_min_balance: string; after_min_balance: string; before_negative_days: number; after_negative_days: number; recommendation: string }
export type Override = { id: number; item_id: number; bill_name: string; occurrence_date: string; new_date: string; created_at: string }
export type SavedItem = { id: number; item_id: number; kind: 'income' | 'bill'; name: string; amount: string; variance_pct: string; enabled: boolean; recurrence: { kind: RecurrenceKind; anchor: string; day_of_month?: number; second_day_of_month?: number }; flexibility?: 'FIXED' | 'WINDOW' | 'FLEXIBLE'; window_start?: number; window_end?: number }
export type Bill = SavedItem & { kind: 'bill' }
export type AccountExport = { account: { id: number; starting_balance: string; as_of: string }; incomes: SavedItem[]; bills: Bill[]; overrides: Override[] }

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000'
const TOKEN_KEY = 'cashflow-access-token'
const ACCOUNT_KEY = 'cashflow-account-id'

async function request(path: string, init: RequestInit = {}, token?: string) {
  const headers = new Headers(init.headers)
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API_URL}${path}`, { ...init, headers })
  if (!response.ok) {
    let message = 'Something went wrong'
    try { const body = await response.json() as { detail?: string }; if (body.detail) message = body.detail } catch { /* Empty error responses are valid. */ }
    throw new Error(message)
  }
  return response
}

export async function signIn(email: string, password: string, mode: 'login' | 'register') {
  const response = await request(`/api/v1/auth/${mode}`, { method: 'POST', body: JSON.stringify({ email, password }) })
  const auth = await response.json() as AuthResponse
  await SecureStore.setItemAsync(TOKEN_KEY, auth.access_token)
}

export async function restoreSession() {
  const token = await SecureStore.getItemAsync(TOKEN_KEY)
  const accountId = await SecureStore.getItemAsync(ACCOUNT_KEY)
  return token ? { token, accountId: accountId ? Number(accountId) : null } : null
}

export async function signOut() {
  await SecureStore.deleteItemAsync(TOKEN_KEY)
  await SecureStore.deleteItemAsync(ACCOUNT_KEY)
}

export async function createAccount(token: string, startingBalance: string, asOf: string) {
  const response = await request('/api/v1/accounts', { method: 'POST', body: JSON.stringify({ starting_balance: startingBalance, as_of: asOf }) }, token)
  const account = await response.json() as { id: number }
  await SecureStore.setItemAsync(ACCOUNT_KEY, String(account.id))
  return account.id
}

export async function getProjection(token: string, accountId: number, horizonDays = 90) {
  const response = await request(`/api/v1/accounts/${accountId}/projection?horizon_days=${horizonDays}`, {}, token)
  return await response.json() as ProjectedDay[]
}

export async function getOptimization(token: string, accountId: number, horizonDays = 90) {
  const response = await request(`/api/v1/accounts/${accountId}/optimization?horizon_days=${horizonDays}`, {}, token)
  return await response.json() as Optimization
}

export async function getOverrides(token: string, accountId: number) {
  const response = await request(`/api/v1/accounts/${accountId}/overrides`, {}, token)
  return await response.json() as Override[]
}

export async function createOverride(token: string, accountId: number, override: { item_id: number; occurrence_date: string; new_date: string }) {
  const response = await request(`/api/v1/accounts/${accountId}/overrides`, { method: 'POST', body: JSON.stringify(override) }, token)
  return await response.json() as { id: number }
}

export async function deleteOverride(token: string, accountId: number, overrideId: number) {
  await request(`/api/v1/accounts/${accountId}/overrides/${overrideId}`, { method: 'DELETE' }, token)
}

export type BillFlexibility = 'FIXED' | 'WINDOW' | 'FLEXIBLE'
type BillFields = { flexibility: BillFlexibility; windowStart?: number; windowEnd?: number }
function billPayload(item: BillFields) { return { flexibility: item.flexibility, ...(item.flexibility === 'WINDOW' ? { window_start: item.windowStart, window_end: item.windowEnd } : {}) } }
export async function addItem(token: string, accountId: number, item: { kind: 'income' | 'bill'; name: string; amount: string; anchor: string; recurrence: RecurrenceKind; flexibility?: BillFlexibility; windowStart?: number; windowEnd?: number }) {
  const payload = { name: item.name, amount: item.amount, recurrence: { kind: item.recurrence, anchor: item.anchor }, ...(item.kind === 'bill' ? billPayload({ flexibility: item.flexibility ?? 'FIXED', windowStart: item.windowStart, windowEnd: item.windowEnd }) : {}) }
  await request(`/api/v1/accounts/${accountId}/${item.kind === 'income' ? 'incomes' : 'bills'}`, { method: 'POST', body: JSON.stringify(payload) }, token)
}

export async function getIncomes(token: string, accountId: number) {
  const response = await request(`/api/v1/accounts/${accountId}/incomes`, {}, token)
  return await response.json() as SavedItem[]
}

export async function getBills(token: string, accountId: number) {
  const response = await request(`/api/v1/accounts/${accountId}/bills`, {}, token)
  return await response.json() as Bill[]
}

export async function updateIncome(token: string, accountId: number, item: SavedItem) {
  await request(`/api/v1/accounts/${accountId}/incomes/${item.item_id}`, { method: 'PUT', body: JSON.stringify({ name: item.name, amount: item.amount, enabled: item.enabled, recurrence: item.recurrence }) }, token)
}

export async function updateBill(token: string, accountId: number, item: Bill) {
  await request(`/api/v1/accounts/${accountId}/bills/${item.item_id}`, { method: 'PUT', body: JSON.stringify({ name: item.name, amount: item.amount, enabled: item.enabled, ...billPayload({ flexibility: item.flexibility ?? 'FIXED', windowStart: item.window_start, windowEnd: item.window_end }), recurrence: item.recurrence }) }, token)
}

export async function setItemEnabled(token: string, accountId: number, item: SavedItem, enabled: boolean) {
  await request(`/api/v1/accounts/${accountId}/${item.kind === 'income' ? 'incomes' : 'bills'}/${item.item_id}/enabled`, { method: 'PATCH', body: JSON.stringify({ enabled }) }, token)
}

export async function deleteItem(token: string, accountId: number, item: SavedItem) {
  await request(`/api/v1/accounts/${accountId}/${item.kind === 'income' ? 'incomes' : 'bills'}/${item.item_id}`, { method: 'DELETE' }, token)
}

export async function exportAccount(token: string, accountId: number) {
  const response = await request(`/api/v1/accounts/${accountId}/export`, {}, token)
  return await response.json() as AccountExport
}

export async function deleteAccount(token: string, accountId: number) {
  await request(`/api/v1/accounts/${accountId}`, { method: 'DELETE' }, token)
  await signOut()
}