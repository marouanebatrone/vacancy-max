import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { useYearOverview } from '@/features/calendar/hooks/useYearOverview';
import { YearCalendar } from '@/features/calendar/components/YearCalendar';
import { BreakCard } from '@/features/optimizer/components/BreakCard';
import { DaysForm } from '@/features/optimizer/components/DaysForm';
import { PlanActions } from '@/features/optimizer/components/PlanActions';
import { PlanHero } from '@/features/optimizer/components/PlanHero';
import { usePlan } from '@/features/optimizer/hooks/usePlan';
import { useShareableDays } from '@/features/optimizer/hooks/useShareableDays';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, retry: 1, refetchOnWindowFocus: false },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Planner />
    </QueryClientProvider>
  );
}

function Planner() {
  const [days, setDays] = useShareableDays();
  const plan = usePlan(days);
  const year = useYearOverview(plan.data?.year);

  return (
    <div className="page">
      <header className="masthead">
        <h1>Vacancy Max</h1>
        <p>Turn your leave days into the longest possible time off.</p>
      </header>

      <DaysForm onSubmit={setDays} busy={plan.isFetching} initialDays={days} />

      {plan.isError && (
        <p className="error">
          Couldn&apos;t build a plan just now. Check the connection and try again.
        </p>
      )}

      {plan.isFetching && !plan.data && <p className="skeleton">Finding your best year…</p>}

      {plan.data && (
        <>
          <div style={{ marginTop: 20 }} />
          <PlanHero plan={plan.data} />

          {plan.data.breaks.length > 0 && <PlanActions plan={plan.data} />}

          {plan.data.breaks.length > 0 && (
            <>
              <div className="section-head">
                <h2>Your breaks</h2>
                <p>{plan.data.breaks.length} stretches, best first to book</p>
              </div>
              <div className="breaks">
                {plan.data.breaks.map((brk) => (
                  <BreakCard key={brk.start} brk={brk} />
                ))}
              </div>

              <div className="section-head">
                <h2>Your {plan.data.year}</h2>
                <p>Every holiday, and the days you&apos;d request</p>
              </div>
              {year.data ? (
                <YearCalendar
                  year={plan.data.year}
                  breaks={[...plan.data.breaks]}
                  holidays={[...year.data.holidays]}
                />
              ) : (
                <p className="skeleton">Loading the calendar…</p>
              )}
            </>
          )}

          <p className="footnote">
            Moroccan public holidays. Weekends are Saturday and Sunday, and a holiday landing on one
            is not given back.
          </p>
        </>
      )}
    </div>
  );
}
