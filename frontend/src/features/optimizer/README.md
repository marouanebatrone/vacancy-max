# feature: optimizer

The product in one screen. The user types **one number** -- how many leave days
their company grants -- and gets back a plan.

    api/         useOptimizePlan() -> POST /api/v1/optimizer/plan/  {"days": 18}
    components/  DaysInput, PlanSummary, BreakCard
    hooks/
    types/       re-exports from the generated schema, never hand-written

Everything else (year, weekends, Moroccan holidays) is the backend's job. This
feature must never ask the user for it.
