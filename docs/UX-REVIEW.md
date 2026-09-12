# UI/UX Review

**Reviewer:** Maya Chen, UI/UX Designer  
**Reviewed:** 2026-08-25  
**Surfaces:** React web client and Expo mobile client

## Release Blockers

1. Web `Accounts` navigation is misleading. It does not have an account view and routes into an unrelated item-library path. Remove it for the one-account v1 or implement a narrowly scoped starting-balance view.
2. Synthetic demo data must be clearly labeled, current-looking, and resettable. Authenticated empty workspaces must not inherit stale sample data.
3. Mobile must expose the full daily balance story, including negative days without events. The current compact event list is not enough for 90-day projection review.
4. Mobile bill editing must preserve and expose `FIXED`, `WINDOW`, and `FLEXIBLE` constraints.
5. Recommendations should show bill, original/proposed dates, constraint, lowest-balance before/after, and negative-day count before/after in both clients.
6. Apply/Undo must correspond to one explicit active scenario. Older unrelated overrides should not make a different recommendation appear undoable.
7. Delete needs confirmation and recovery language because it changes future projections.

## Important Usability Risks

- Web chart needs an accessible data-table equivalent with date, opening balance, events, and closing balance.
- Web modal needs dialog semantics, Escape handling, focus management, and explicit cancel behavior.
- Mobile item actions need contextual error feedback instead of silently failing.
- Web controls need consistent visible focus states and larger touch targets.
- Web and mobile navigation should intentionally represent the same v1 concepts.
- Assumptions disclosure should match across clients.
- Negative rows should identify when an event crosses the balance below zero.
- Demo and staging data must remain isolated and synthetic.

## Approved Direction

Keep the product focused on daily cash position, negative-day detection, and one constrained scheduling change. Do not add categories, spending analysis, net worth, bank sync, or unrelated dashboard tabs.

## Prioritized Work

1. Remove or correctly implement web Accounts navigation.
2. Fix demo labeling, date freshness, and reset behavior.
3. Add full mobile projection discoverability.
4. Bring mobile bill constraint editing to parity.
5. Make recommendation before/after and active Apply/Undo state explicit.
6. Add delete confirmation and action-level errors.
7. Complete web chart/modal accessibility and focus targets.
8. Expand mobile assumptions to match web.
