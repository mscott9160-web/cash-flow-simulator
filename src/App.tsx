import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { addBill, addIncome, createAccount, createOverride, deleteAccount, deleteItem, deleteOverride, exportAccount, getItems, getOptimization, getOverrides, getProjection, login, register, setItemEnabled, updateBill, updateIncome } from './api'
import type { RecurrenceKind } from './api'
import type { Optimization, Override, ProjectedDay, SavedItem } from './api'
import './App.css'

type View = 'Projection' | 'Income' | 'Bills' | 'Assumptions' | 'Settings'
type ItemKind = 'income' | 'bill'

function relativeDate(daysFromToday: number) { const date = new Date(); date.setHours(12, 0, 0, 0); date.setDate(date.getDate() + daysFromToday); return date.toISOString().slice(0, 10) }
const demoDate = relativeDate
const sampleDays: ProjectedDay[] = [
  { date: demoDate(0), opening_balance: '1860', closing_balance: '1860', events: [] },
  { date: demoDate(7), opening_balance: '1860', closing_balance: '2480', events: [{ name: 'Paycheck', amount: '620', source_date: demoDate(7), posted_date: demoDate(7), kind: 'income' }] },
  { date: demoDate(14), opening_balance: '2480', closing_balance: '-96', events: [{ name: 'Rent', amount: '-2576', source_date: demoDate(14), posted_date: demoDate(14), kind: 'bill' }] },
  { date: demoDate(15), opening_balance: '-96', closing_balance: '-172', events: [{ name: 'Internet', amount: '-76', source_date: demoDate(15), posted_date: demoDate(15), kind: 'bill' }] },
  { date: demoDate(21), opening_balance: '-172', closing_balance: '448', events: [{ name: 'Paycheck', amount: '620', source_date: demoDate(21), posted_date: demoDate(21), kind: 'income' }] },
  { date: demoDate(28), opening_balance: '448', closing_balance: '148', events: [{ name: 'Card payment', amount: '-300', source_date: demoDate(28), posted_date: demoDate(28), kind: 'bill' }] },
  { date: demoDate(28), opening_balance: '820', closing_balance: '2140', events: [{ name: 'Rent', amount: '-1500', source_date: demoDate(28), posted_date: demoDate(28), kind: 'bill' }] },
]

function amount(value: string) { return Number(value) }
function money(value: number) { return `${value < 0 ? '-' : ''}$${Math.abs(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}` }
function shortDate(value: string) { return new Date(`${value}T12:00:00`).toLocaleDateString(undefined, { month: 'short', day: '2-digit' }) }
function optimizationMetric(value: string) { return money(amount(value)) }

const chartWidth = 800
const chartHeight = 220
const chartPadding = { top: 12, right: 12, bottom: 12, left: 12 }

function chartBalance(value: number) {
  if (Math.abs(value) >= 1000) return `${value < 0 ? '-' : ''}$${(Math.abs(value) / 1000).toFixed(1).replace('.0', '')}k`
  return money(value)
}

function createChart(days: ProjectedDay[]) {
  const balances = days.map((day) => {
    const value = amount(day.closing_balance)
    return Number.isFinite(value) ? value : 0
  })
  const minimum = Math.min(0, ...balances)
  const maximum = Math.max(0, ...balances)
  const balanceRange = maximum - minimum
  const padding = balanceRange ? balanceRange * 0.1 : Math.max(Math.abs(maximum) * 0.1, 1)
  const lowerBound = minimum - padding
  const upperBound = maximum + padding
  const valueRange = upperBound - lowerBound
  const plotWidth = chartWidth - chartPadding.left - chartPadding.right
  const plotHeight = chartHeight - chartPadding.top - chartPadding.bottom
  const yForBalance = (value: number) => chartPadding.top + ((upperBound - value) / valueRange) * plotHeight
  const points = balances.map((value, index) => ({
    value,
    x: days.length === 1 ? chartWidth / 2 : chartPadding.left + (index / (days.length - 1)) * plotWidth,
    y: yForBalance(value),
  }))
  const linePath = points.map(({ x, y }, index) => `${index ? 'L' : 'M'}${x} ${y}`).join(' ')
  const areaPath = points.length ? `${linePath} L${points[points.length - 1].x} ${yForBalance(0)} L${points[0].x} ${yForBalance(0)}Z` : ''
  const labelCount = Math.min(5, days.length || 1)
  const labelIndexes = Array.from({ length: labelCount }, (_, index) => days.length ? Math.round(index * (days.length - 1) / Math.max(labelCount - 1, 1)) : 0)
  const dateLabels = days.length ? labelIndexes.filter((index, position, indexes) => indexes.indexOf(index) === position && indexes.findIndex((candidate) => days[candidate].date === days[index].date) === position).map((index) => ({ date: days[index].date, x: points[index].x })) : []
  const yLabels = Array.from({ length: 5 }, (_, index) => upperBound - (index / 4) * valueRange)

  return { points, linePath, areaPath, zeroY: yForBalance(0), dateLabels, yLabels }
}

function AuthScreen({ onAuthenticated }: { onAuthenticated: (token: string, accountId?: number) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    const normalizedEmail = email.trim()
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) {
      setError('Enter a valid email address.')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setLoading(true)
    try {
      const result = mode === 'login' ? await login(normalizedEmail, password) : await register(normalizedEmail, password)
      localStorage.setItem('cashflow-access-token', result.access_token)
      if (result.account_id) localStorage.setItem('cashflow-account-id', String(result.account_id))
      onAuthenticated(result.access_token, result.account_id)
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : 'Could not authenticate.')
    } finally {
      setLoading(false)
    }
  }

  return <main className="auth-shell">
    <section className="auth-intro">
      <div className="brand"><span className="brand-mark">cf</span><span>cashflow</span></div>
      <div className="auth-story"><p className="eyebrow">See the month ahead</p><h1>Make room for what matters.</h1><p>Cashflow turns the timing of your income and bills into a clear daily picture, so shortfalls never arrive as a surprise.</p><div className="auth-stats"><span><strong>90</strong> days in view</span><span><strong>1</strong> clear next move</span></div></div>
    </section>
    <section className="auth-panel" aria-labelledby="auth-title">
      <div className="auth-panel-heading"><p className="eyebrow">Your private workspace</p><h2 id="auth-title">{mode === 'login' ? 'Welcome back' : 'Start planning clearly'}</h2><p>{mode === 'login' ? 'Sign in to pick up your projection.' : 'Create an account to save your projection.'}</p></div>
      <div className="auth-tabs" role="tablist"><button type="button" role="tab" aria-selected={mode === 'login'} className={mode === 'login' ? 'selected' : ''} onClick={() => { setMode('login'); setError('') }}>Sign in</button><button type="button" role="tab" aria-selected={mode === 'register'} className={mode === 'register' ? 'selected' : ''} onClick={() => { setMode('register'); setError('') }}>Create account</button></div>
      <form className="auth-form" onSubmit={handleSubmit}>
        <label>Email address<input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" required /></label>
        <label>Password<input type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="8 characters minimum" minLength={8} required /></label>
        {error && <p className="auth-error" role="alert">{error}</p>}
        <button className="auth-submit" type="submit" disabled={loading}>{loading ? 'Connecting…' : mode === 'login' ? 'Sign in to cashflow →' : 'Create my workspace →'}</button>
      </form>
      <p className="auth-footnote">Your projection stays tied to your account and is never sent anonymously.</p>
      <button className="demo-button" type="button" onClick={() => onAuthenticated('demo-local')}>Explore demo projection</button>
      <p className="demo-note">Synthetic demo data only. It never creates an account or uses your data.</p>
    </section>
  </main>
}

function AssumptionsPanel() {
  return <section className="assumptions-panel panel" aria-labelledby="assumptions-title">
    <div className="assumptions-intro">
      <p className="eyebrow">Locked v1 contract</p>
      <h2 id="assumptions-title">The rules behind your projection</h2>
      <p>These are the calendar, money, and advisory boundaries the simulator uses today.</p>
    </div>
    <div className="assumptions-grid">
      <article><span className="assumption-index">01</span><h3>Money and horizon</h3><p>Projections use US dollars and cents, with a 90-day default horizon.</p></article>
      <article><span className="assumption-index">02</span><h3>Business days</h3><p>US federal holidays and Saturday/Sunday are treated as non-business days.</p></article>
      <article><span className="assumption-index">03</span><h3>Income posting</h3><p>Income scheduled on a non-business day shifts to the prior business day.</p></article>
      <article><span className="assumption-index">04</span><h3>Bill posting</h3><p>Bills post on their scheduled date. Flexible and window bills provide allowed scheduling dates for recommendations.</p></article>
      <article><span className="assumption-index">05</span><h3>Variable bills</h3><p>Variable bills use the high end of their variance as a deterministic stress amount.</p></article>
      <article><span className="assumption-index">06</span><h3>Advisory only</h3><p>Projections are estimates, not financial advice. Recommendations are hypothetical and never execute payments.</p></article>
    </div>
  </section>
}

function SettingsPanel({ onExport, onDelete, onLogout, loading }: { onExport: () => void; onDelete: () => void; onLogout: () => void; loading: boolean }) {
  return <section className="settings-panel panel" aria-labelledby="settings-title"><div className="settings-intro"><p className="eyebrow">Account management</p><h2 id="settings-title">Keep your account in your hands</h2><p>Export a copy of your saved cash-flow data, or manage your session and account.</p></div><div className="settings-actions"><button className="outline-button" onClick={onExport} disabled={loading}>{loading ? 'Preparing export...' : <>Export data <span>↓</span></>}</button><button className="text-button" onClick={onLogout} disabled={loading}>Sign out <span>↗</span></button></div><div className="danger-section"><p className="eyebrow">Destructive action</p><h2>Delete account</h2><p>This permanently removes your account and all saved cash-flow data. This cannot be undone.</p><button className="danger-action" onClick={onDelete} disabled={loading}>Delete account</button></div></section>
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('cashflow-access-token') ?? '')
  const [activeView, setActiveView] = useState<View>('Projection')
  const [days, setDays] = useState(sampleDays)
  const [items, setItems] = useState<SavedItem[]>([])
  const [optimization, setOptimization] = useState<Optimization | null>(null)
  const [overrides, setOverrides] = useState<Override[]>([])
  const [accountId, setAccountId] = useState<number | null>(() => token ? Number(localStorage.getItem('cashflow-account-id')) || null : null)
  const [showAllDays, setShowAllDays] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [editingItem, setEditingItem] = useState<SavedItem | null>(null)
  const [itemKind, setItemKind] = useState<ItemKind>('bill')
  const [form, setForm] = useState({ name: '', amount: '', date: '2025-06-15', balance: '', recurrence: 'MONTHLY' as RecurrenceKind, flexibility: 'FLEXIBLE' as 'FIXED' | 'WINDOW' | 'FLEXIBLE', windowStart: '15', windowEnd: '22', enabled: true })
  const [loading, setLoading] = useState(false)
  const [notice, setNotice] = useState('Sample projection')
  const [error, setError] = useState('')
  const [selectedNegative, setSelectedNegative] = useState<ProjectedDay | null>(null)
  const [deletingItem, setDeletingItem] = useState<SavedItem | null>(null)

  function handleLogout() {
    localStorage.removeItem('cashflow-access-token')
    localStorage.removeItem('cashflow-account-id')
    setToken('')
    setAccountId(null)
    setActiveView('Projection')
  }

  const refreshAccount = useCallback(async (id: number) => {
    setLoading(true)
    try {
      const [projection, incomes, bills, savedOptimization, savedOverrides] = await Promise.all([getProjection(id), getItems(id, 'income'), getItems(id, 'bill'), getOptimization(id), getOverrides(id)])
      setDays(projection); setItems([...incomes, ...bills]); setOptimization(savedOptimization); setOverrides(savedOverrides)
    } finally { setLoading(false) }
  }, [])

  useEffect(() => {
    if (!accountId) return
    // The refresh owns loading state and synchronizes the account snapshot.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refreshAccount(accountId).then(() => {
      setNotice('Synced from your account')
      setError('')
    }).catch(() => setError('The saved projection could not be loaded.'))
  }, [accountId, refreshAccount])

  const lowest = days.reduce((current, day) => Math.min(current, amount(day.closing_balance)), Infinity)
  const negativeDays = days.filter((day) => amount(day.closing_balance) < 0)
  const currentBalance = amount(days[0]?.opening_balance ?? '0')
  const incomeTotal = days.flatMap((day) => day.events).filter((event) => event.kind === 'income').reduce((total, event) => total + amount(event.amount), 0)
  const billTotal = Math.abs(days.flatMap((day) => day.events).filter((event) => event.kind === 'bill').reduce((total, event) => total + amount(event.amount), 0))
  const visibleDays = showAllDays ? days : days.slice(0, 7)
  const chart = createChart(days)
  const activeItems = items.filter((item) => activeView === 'Income' ? item.kind === 'income' : item.kind === 'bill')
  const recommendation = optimization?.moves[0]
  const recommendedBill = recommendation ? items.find((item) => item.kind === 'bill' && item.name === recommendation.bill_name) : undefined
  const appliedOverride = overrides.find((override) => items.some((item) => item.kind === 'bill' && item.item_id === override.item_id))
  const currentRecommendationApplied = recommendation && recommendedBill ? overrides.some((override) => override.item_id === recommendedBill.item_id && override.occurrence_date === recommendation.original_date && override.new_date === recommendation.new_date) : false

  async function handleApplyRecommendation() {
    if (!accountId || !recommendation || !recommendedBill) return
    setLoading(true)
    setError('')
    try {
      await createOverride(accountId, recommendedBill.item_id, recommendation.original_date, recommendation.new_date)
      await refreshAccount(accountId)
      setNotice('Hypothetical schedule change applied')
    } catch (applyError) {
      setError(applyError instanceof Error ? applyError.message : 'Could not apply recommendation.')
    } finally { setLoading(false) }
  }

  async function handleUndoRecommendation() {
    if (!accountId || !appliedOverride) return
    setLoading(true)
    setError('')
    try {
      await deleteOverride(accountId, appliedOverride.id)
      await refreshAccount(accountId)
      setNotice('Hypothetical schedule change undone')
    } catch (undoError) {
      setError(undoError instanceof Error ? undoError.message : 'Could not undo change.')
    } finally { setLoading(false) }
  }

  async function handleToggleItem(item: SavedItem) {
    if (!accountId) return
    const enabled = !item.enabled
    setLoading(true)
    setError('')
    try {
      await setItemEnabled(accountId, item, enabled)
      await refreshAccount(accountId)
      setNotice(`${item.name} ${enabled ? 'resumed' : 'paused'}`)
    } catch (toggleError) {
      setError(toggleError instanceof Error ? toggleError.message : 'Could not update item.')
    } finally { setLoading(false) }
  }

  async function handleDeleteItem() {
    if (!accountId || !deletingItem) return
    setLoading(true)
    setError('')
    try {
      await deleteItem(accountId, deletingItem)
      await refreshAccount(accountId)
      setDeletingItem(null)
      setNotice(`${deletingItem.name} deleted`)
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : `Could not delete ${deletingItem.name}.`)
    } finally { setLoading(false) }
  }

  async function handleExport() {
    if (!accountId) return
    setLoading(true); setError(''); setNotice('Preparing account export...')
    try {
      const data = await exportAccount(accountId)
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url; link.download = `cashflow-account-${accountId}.json`; link.click()
      URL.revokeObjectURL(url)
      setNotice('Account export downloaded')
    } catch (exportError) { setError(exportError instanceof Error ? exportError.message : 'Could not export your account.')
    } finally { setLoading(false) }
  }

  async function handleDeleteAccount() {
    if (!accountId || !window.confirm('Delete your account and all saved cash-flow data? This cannot be undone.')) return
    setLoading(true); setError(''); setNotice('Deleting your account...')
    try {
      await deleteAccount(accountId)
      localStorage.removeItem('cashflow-access-token'); localStorage.removeItem('cashflow-account-id')
      setToken(''); setAccountId(null); setDays([]); setItems([]); setOptimization(null); setOverrides([]); setNotice('')
    } catch (deleteError) { setError(deleteError instanceof Error ? deleteError.message : 'Could not delete your account.')
    } finally { setLoading(false) }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      let id = accountId
      if (!id) {
        const created = await createAccount(form.balance || '0', form.date)
        id = created.id
        setAccountId(id)
        localStorage.setItem('cashflow-account-id', String(id))
      }
      if (editingItem) {
        if (editingItem.kind === 'income') await updateIncome(id, editingItem.item_id, form.name, form.amount, form.date, form.recurrence, form.enabled)
        else await updateBill(id, editingItem.item_id, form.name, form.amount, form.date, form.recurrence, form.flexibility, Number(form.windowStart), Number(form.windowEnd), form.enabled)
      } else if (itemKind === 'income') await addIncome(id, form.name, form.amount, form.date, form.recurrence)
      else await addBill(id, form.name, form.amount, form.date, form.recurrence, form.flexibility, Number(form.windowStart), Number(form.windowEnd))
      setShowForm(false)
      setEditingItem(null)
      setForm({ name: '', amount: '', date: '2025-06-15', balance: '', recurrence: 'MONTHLY', flexibility: 'FLEXIBLE', windowStart: '15', windowEnd: '22', enabled: true })
      setNotice(editingItem ? 'Changes saved to your account' : 'Saved to your account')
      await refreshAccount(id)
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Could not save this item.')
    } finally { setLoading(false) }
  }

  if (!token) return <AuthScreen onAuthenticated={(newToken, newAccountId) => { setToken(newToken); setAccountId(newAccountId ?? null); setNotice(newToken === 'demo-local' ? 'Demo data' : 'Sample projection') }} />

  return <main className="app-shell">
    <header className="topbar">
      <div className="brand"><span className="brand-mark">cf</span><span>cashflow</span></div>
      <nav aria-label="Main navigation">{(['Projection', 'Income', 'Bills', 'Assumptions', 'Settings'] as View[]).map((item) => <button className={activeView === item ? 'nav-item active' : 'nav-item'} key={item} onClick={() => setActiveView(item)}>{item}</button>)}</nav>
      {accountId && <button className="profile" onClick={handleLogout} aria-label="Sign out">Sign out <span>↗</span></button>}
    </header>
    <section className="content">
      <div className="heading-row"><div><p className="eyebrow">{activeView === 'Projection' ? 'Cash health' : activeView === 'Assumptions' ? 'Product boundaries' : 'Setup'}</p><h1>{activeView}</h1><p className="subheading">{activeView === 'Assumptions' ? 'A clear reference for how the simulator treats timing, money, and recommendations.' : accountId ? 'Your daily balance, projected through September 5.' : 'Start with a balance, then add what you make and owe.'}</p></div>{activeView !== 'Assumptions' && <div className="heading-actions">{recommendation && recommendedBill && (currentRecommendationApplied ? <button className="outline-button" onClick={handleUndoRecommendation} disabled={loading}>Undo change <span>↶</span></button> : <button className="primary-button" onClick={handleApplyRecommendation} disabled={loading}>Apply recommendation <span>→</span></button>)}{appliedOverride && !recommendation && <button className="outline-button" onClick={handleUndoRecommendation} disabled={loading}>Undo change <span>↶</span></button>}<button className="primary-button" onClick={() => { setEditingItem(null); setShowForm(true) }}><span>+</span> Add item</button></div>}</div>
      {error && <div className="notice error-notice">{error}<button className="retry-button" onClick={() => accountId && refreshAccount(accountId)} disabled={loading}>{loading ? 'Retrying...' : 'Retry loading account data'}</button></div>}
      {token === 'demo-local' && <div className="notice">Demo data: synthetic dates and transactions, stored only in this browser. <button className="text-button" onClick={() => { setToken(''); setAccountId(null); setDays([]); setItems([]); setOptimization(null); setNotice('') }}>Reset demo</button></div>}
      {appliedOverride && <div className="notice recommendation-applied">Applied as a hypothetical schedule change for {appliedOverride.bill_name}. This does not make or schedule a real payment.</div>}
      {recommendation && !recommendedBill && <div className="notice error-notice">This advisory move could not be matched to a saved bill, so it cannot be applied.</div>}
      {activeView === 'Settings' ? <SettingsPanel onExport={handleExport} onDelete={handleDeleteAccount} onLogout={handleLogout} loading={loading} /> : activeView === 'Assumptions' ? <AssumptionsPanel /> : <>
      <div className="summary-grid"><article className="balance-card"><div className="card-label">Current balance <span className="tiny-dot"></span></div><strong>{money(currentBalance)}</strong><p className="positive">{notice}</p><div className="balance-spark"><span></span><span></span><span></span><span></span><span></span><span></span><span></span></div></article><article className="metric-card"><div className="card-label">Lowest projected</div><strong className={lowest < 0 ? 'negative' : ''}>{money(lowest)}</strong><p>{negativeDays.length ? `${negativeDays.length} negative day${negativeDays.length === 1 ? '' : 's'}` : 'No negative days'}</p><div className="metric-rule negative-rule"></div></article><article className="metric-card"><div className="card-label">Income in view</div><strong>{money(incomeTotal)}</strong><p>{days.flatMap((day) => day.events).filter((event) => event.kind === 'income').length} deposits expected</p><div className="metric-rule income-rule"></div></article><article className="metric-card"><div className="card-label">Bills in view</div><strong>{money(billTotal)}</strong><p>{days.flatMap((day) => day.events).filter((event) => event.kind === 'bill').length} payments expected</p><div className="metric-rule bill-rule"></div></article></div>
      {activeView !== 'Projection' && <section className="item-library panel"><div className="panel-heading"><div><h2>{activeView} sources</h2><p>Saved items used by the projection engine</p></div><button className="text-button" onClick={() => { setItemKind(activeView === 'Income' ? 'income' : 'bill'); setEditingItem(null); setShowForm(true) }}>Add {activeView === 'Income' ? 'income' : 'bill'} <span>+</span></button></div>{!accountId && <p className="empty-state">Create your first account from the Projection tab to start saving items.</p>}{accountId && !activeItems.length && <p className="empty-state">No {activeView.toLowerCase()} sources yet.</p>}<div className="saved-items">{activeItems.map((item) => <div className={item.enabled ? 'saved-item' : 'saved-item disabled'} key={`${item.kind}-${item.item_id}`}><div><strong>{item.name}</strong><span>{item.recurrence.kind.toLowerCase().replace('_', ' ')} · {shortDate(item.recurrence.anchor)}{item.kind === 'bill' ? ` · ${item.flexibility?.toLowerCase()}` : ''}</span><span className="item-status" aria-label={`${item.name} is ${item.enabled ? 'active' : 'paused'}`}>{item.enabled ? 'Active' : 'Paused'}</span></div><strong>{money(amount(item.amount))}</strong><button className="toggle-button" onClick={() => { setEditingItem(item); setItemKind(item.kind); setForm({ name: item.name, amount: item.amount, date: item.recurrence.anchor, balance: '', recurrence: item.recurrence.kind, flexibility: item.flexibility ?? 'FLEXIBLE', windowStart: String(item.window_start ?? 15), windowEnd: String(item.window_end ?? 22), enabled: item.enabled }); setShowForm(true) }} disabled={loading} aria-label={`Edit ${item.name}`}>Edit</button><button className="toggle-button" onClick={() => handleToggleItem(item)} disabled={loading} aria-label={`${item.enabled ? 'Pause' : 'Resume'} ${item.name}`}>{item.enabled ? 'Pause' : 'Resume'}</button><button className="delete-button" onClick={() => setDeletingItem(item)} aria-label={`Delete ${item.name}`}>×</button></div>)}</div></section>}
      <div className="main-grid"><section className="projection-panel panel"><div className="panel-heading"><div><h2>90-day projection</h2><p>{days.length ? `${shortDate(days[0].date)} — ${shortDate(days[days.length - 1].date)}` : 'No projection yet'}</p></div><div className="legend"><span><i className="legend-line"></i> Balance</span><span><i className="legend-red"></i> Below zero</span></div></div><div className="chart"><div className="chart-y"><span>$3k</span><span>$2k</span><span>$1k</span><span>$0</span></div><div className="chart-area"><div className="gridline top"></div><div className="gridline mid-high"></div><div className="gridline mid"></div><div className="gridline zero"></div><div className="negative-zone"></div><svg viewBox="0 0 800 220" preserveAspectRatio="none" aria-label="Projected balance line chart"><path className="area-fill" d="M0 82 L80 65 L160 70 L240 224 L320 126 L400 92 L480 104 L560 64 L640 70 L720 35 L800 50 L800 220 L0 220Z"></path><path className="line-fill" d="M0 82 L80 65 L160 70 L240 224 L320 126 L400 92 L480 104 L560 64 L640 70 L720 35 L800 50"></path></svg><div className="chart-labels"><span>{days[0] ? shortDate(days[0].date) : 'Start'}</span><span>{days[2] ? shortDate(days[Math.min(2, days.length - 1)].date) : ''}</span><span>{days[4] ? shortDate(days[Math.min(4, days.length - 1)].date) : ''}</span><span>{days[6] ? shortDate(days[Math.min(6, days.length - 1)].date) : ''}</span><span>{days.length ? shortDate(days[Math.floor(days.length / 2)].date) : ''}</span><span>{days.length ? shortDate(days[days.length - 1].date) : ''}</span></div></div></div></section><aside className="recommendation panel"><div className="recommendation-icon">↗</div><p className="eyebrow">Advisory recommendation</p><h2>{accountId && optimization ? (optimization.moves.length ? 'Consider this scheduling move' : 'No schedule change needed') : negativeDays.length ? 'Review your first negative day' : 'Your projection is clear'}</h2><p>{accountId && optimization ? optimization.recommendation : negativeDays.length ? `Open ${shortDate(negativeDays[0].date)} to see which event pushes the balance below zero.` : 'This is sample projection data. Add your recurring income and bills to load a real advisory recommendation.'}</p>{optimization ? <div className="recommendation-metrics">{optimization.moves.length ? <span>{optimization.moves[0].bill_name}: {shortDate(optimization.moves[0].original_date)} → {shortDate(optimization.moves[0].new_date)}</span> : <span>No scheduling move proposed.</span>}<span>{optimizationMetric(optimization.before_min_balance)} → {optimizationMetric(optimization.after_min_balance)} minimum</span><span>{optimization.before_negative_days} → {optimization.after_negative_days} negative days</span></div> : null}<p className="fine-print">{loading ? 'Updating projection and advisory…' : accountId ? 'Advisory only. No changes have been applied.' : 'Sample projection fallback'}</p></aside></div>
        <div className="main-grid"><section className="projection-panel panel"><div className="panel-heading"><div><h2>90-day projection</h2><p>{days.length ? `${shortDate(days[0].date)} — ${shortDate(days[days.length - 1].date)}` : 'No projection yet'}</p></div><div className="legend"><span><i className="legend-line"></i> Balance</span><span><i className="legend-red"></i> Below zero</span></div></div><div className="chart"><div className="chart-y">{chart.yLabels.map((value) => <span key={value}>{chartBalance(value)}</span>)}</div><div className="chart-area">{chart.yLabels.map((value, index) => <div className={Math.abs(value) < 0.0001 ? 'gridline zero' : 'gridline'} key={value} style={{ top: `${(index / 4) * 100}%` }}></div>)}{chart.points.some((point) => point.value < 0) && <div className="negative-zone" style={{ top: `${(chart.zeroY / chartHeight) * 100}%` }}></div>}<svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} preserveAspectRatio="none" aria-label="Projected balance line chart"><path className="area-fill" d={chart.areaPath}></path><path className="line-fill" d={chart.linePath}></path>{chart.points.map((point) => <circle className={point.value < 0 ? 'danger-point' : 'good-point'} cx={point.x} cy={point.y} r="4" key={`${point.x}-${point.value}`}></circle>)}</svg><div className="chart-labels">{chart.dateLabels.map((label, index) => <span key={`${label.date}-${index}`} style={{ left: `${(label.x / chartWidth) * 100}%` }}>{label.date ? shortDate(label.date) : ''}</span>)}</div></div></div></section><aside className="recommendation panel"><div className="recommendation-icon">↗</div><p className="eyebrow">Advisory recommendation</p><h2>{accountId && optimization ? (optimization.moves.length ? 'Consider this scheduling move' : 'No schedule change needed') : negativeDays.length ? 'Review your first negative day' : 'Your projection is clear'}</h2><p>{accountId && optimization ? optimization.recommendation : negativeDays.length ? `Open ${shortDate(negativeDays[0].date)} to see which event pushes the balance below zero.` : 'This is sample projection data. Add your recurring income and bills to load a real advisory recommendation.'}</p>{optimization?.moves.length ? <div className="recommendation-metrics"><span><strong>Move:</strong> {optimization.moves[0].bill_name}, {shortDate(optimization.moves[0].original_date)} → {shortDate(optimization.moves[0].new_date)}</span><span><strong>Minimum balance:</strong> {optimizationMetric(optimization.before_min_balance)} → {optimizationMetric(optimization.after_min_balance)}</span><span><strong>Negative days:</strong> {optimization.before_negative_days} → {optimization.after_negative_days}</span><span>This is a hypothetical, advisory change. It does not execute a payment.</span></div> : null}<p className="fine-print">{loading ? 'Updating projection and advisory…' : accountId ? 'Advisory only. No changes have been applied.' : 'Sample projection fallback'}</p></aside></div>
      <section className="activity panel"><div className="panel-heading"><div><h2>Upcoming days</h2><p>{negativeDays.length ? `First shortfall: ${shortDate(negativeDays[0].date)} · lowest ${money(lowest)} · ${negativeDays.length} negative day${negativeDays.length === 1 ? '' : 's'}` : 'No shortfalls in this projection'}</p></div><button className="text-button" onClick={() => setShowAllDays(!showAllDays)}>{showAllDays ? 'Show less' : 'View all days'} <span>→</span></button></div><div className="day-list">{visibleDays.map((day, index) => <button className={amount(day.closing_balance) < 0 ? 'day-row danger day-button' : 'day-row day-button'} key={`${day.date}-${index}`} onClick={() => amount(day.closing_balance) < 0 && setSelectedNegative(day)}><div className="date-block"><strong>{new Date(`${day.date}T12:00:00`).getDate().toString().padStart(2, '0')}</strong><span>{new Date(`${day.date}T12:00:00`).toLocaleDateString(undefined, { month: 'short' })}</span></div><div className="events">{day.events.length ? day.events.map((event, index) => <span className={event.kind === 'income' ? 'event income' : 'event bill'} key={`${event.name}-${index}`}><i></i>{event.name} <em>{amount(event.amount) > 0 ? '+' : ''}{money(amount(event.amount))}</em></span>) : <span className="quiet">No scheduled events</span>}</div><strong className={amount(day.closing_balance) < 0 ? 'day-balance negative' : 'day-balance'}>{money(amount(day.closing_balance))}</strong></button>)}</div></section>
      </>}
    </section>
    {deletingItem && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setDeletingItem(null)}><section className="detail-panel delete-dialog" role="dialog" aria-modal="true" aria-labelledby="delete-title"><p className="eyebrow">Delete saved item</p><h2 id="delete-title">Delete {deletingItem.name}?</h2><p>This will remove future occurrences from the projection.</p><div className="dialog-actions"><button className="outline-button" onClick={() => setDeletingItem(null)} disabled={loading}>Cancel</button><button className="primary-button" onClick={handleDeleteItem} disabled={loading}>{loading ? 'Deleting...' : 'Delete item'}</button></div></section></div>}
    <footer><span>cashflow</span><span>{loading || (Boolean(accountId) && !optimization && !error) ? 'Syncing…' : notice}</span><span>90 day horizon · USD</span></footer>
    {selectedNegative && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setSelectedNegative(null)}><section className="detail-panel" role="dialog" aria-modal="true" aria-labelledby="shortfall-title"><button className="close-button" onClick={() => setSelectedNegative(null)} aria-label="Close">×</button><p className="eyebrow">Shortfall investigation</p><h2 id="shortfall-title">{shortDate(selectedNegative.date)}</h2><p>Opening balance: <strong>{money(amount(selectedNegative.opening_balance))}</strong></p>{selectedNegative.events.map((event, index) => <p key={`${event.name}-${index}`}>{event.name}: {money(amount(event.amount))}</p>)}<p>Closing balance: <strong className="negative">{money(amount(selectedNegative.closing_balance))}</strong></p><p className="fine-print">Crossing event: the listed bills reduce the opening balance below zero; the closing balance reflects every event posted that day.</p></section></div>}
    {showForm && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setShowForm(false)}><form className="item-form" onSubmit={handleSubmit}><div className="panel-heading"><div><p className="eyebrow">{editingItem ? 'Edit saved item' : 'Add to projection'}</p><h2>{editingItem ? 'Edit item' : accountId ? 'New item' : 'Start your account'}</h2></div><button type="button" className="close-button" onClick={() => { setShowForm(false); setEditingItem(null) }} aria-label="Close">×</button></div>{!accountId && <label>Starting balance<input required type="number" step="0.01" value={form.balance} onChange={(event) => setForm({ ...form, balance: event.target.value })} placeholder="1000.00" /></label>}<div className="segmented"><button type="button" className={itemKind === 'bill' ? 'selected' : ''} onClick={() => setItemKind('bill')}>Bill</button><button type="button" className={itemKind === 'income' ? 'selected' : ''} onClick={() => setItemKind('income')}>Income</button></div><label>Name<input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder={itemKind === 'bill' ? 'Rent' : 'Paycheck'} /></label><label>Amount<input required type="number" min="0.01" step="0.01" value={form.amount} onChange={(event) => setForm({ ...form, amount: event.target.value })} placeholder="500.00" /></label><label>Recurrence<select value={form.recurrence} onChange={(event) => setForm({ ...form, recurrence: event.target.value as RecurrenceKind })}><option value="ONCE">One time</option><option value="WEEKLY">Weekly</option><option value="BIWEEKLY">Every two weeks</option><option value="SEMI_MONTHLY">Twice a month</option><option value="MONTHLY">Monthly</option></select></label><label>First date<input required type="date" value={form.date} onChange={(event) => setForm({ ...form, date: event.target.value })} /></label>{itemKind === 'bill' && <><label>Flexibility<select value={form.flexibility} onChange={(event) => setForm({ ...form, flexibility: event.target.value as 'FIXED' | 'WINDOW' | 'FLEXIBLE' })}><option value="FIXED">Fixed date</option><option value="WINDOW">Within a window</option><option value="FLEXIBLE">Flexible this month</option></select></label>{form.flexibility === 'WINDOW' && <div className="window-fields"><label>Window starts<input type="number" min="1" max="31" value={form.windowStart} onChange={(event) => setForm({ ...form, windowStart: event.target.value })} /></label><label>Window ends<input type="number" min="1" max="31" value={form.windowEnd} onChange={(event) => setForm({ ...form, windowEnd: event.target.value })} /></label></div>}</>}<p className="form-note">Dates and flexibility are saved with this recurring item and used by the projection engine.</p><button className="primary-button form-submit" disabled={loading}>{loading ? 'Saving…' : editingItem ? 'Save changes' : 'Save and project'}</button></form></div>}
  </main>
}

export default App
