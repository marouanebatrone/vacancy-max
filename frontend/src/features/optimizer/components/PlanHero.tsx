import type { Plan } from '../api/optimizerApi';

type Props = { plan: Plan };

/**
 * The moment the product exists for: you gained days, here is how many.
 *
 * Exactly one hero figure on the page. The stat tiles beneath it are secondary
 * and deliberately smaller.
 */
export function PlanHero({ plan }: Props) {
  const { summary, budget, year } = plan;
  const gained = summary.total_days_off - summary.leave_used;

  if (summary.break_count === 0) {
    return (
      <section className="card hero">
        <p className="congrats">Nothing to plan yet</p>
        <p className="lede">
          With {budget} leave {budget === 1 ? 'day' : 'days'} there&apos;s no holiday to build
          around in {year}. Try a few more days.
        </p>
      </section>
    );
  }

  return (
    <section className="card hero">
      <p className="congrats">Congratulations! 🎉</p>

      <p className="figure">
        {summary.total_days_off}
        <span>days away from the office</span>
      </p>

      <p className="lede">
        in {year}, from just <strong>{summary.leave_used}</strong> days of leave. That&apos;s{' '}
        <strong>{gained} extra days</strong> you never had to ask for.
      </p>

      {summary.has_estimated_holidays && (
        <p className="caveat">
          Some breaks fall on Islamic holidays whose dates Morocco confirms by moon sighting.
          They&apos;re marked <em>date not confirmed</em> below — worth a second look before you
          book anything.
        </p>
      )}

      <dl className="stats">
        <div className="stat">
          <dt>Days you request</dt>
          <dd>{summary.leave_used}</dd>
        </div>
        <div className="stat">
          <dt>Extra days gained</dt>
          <dd>{gained}</dd>
        </div>
        <div className="stat">
          <dt>Longest break</dt>
          <dd>{summary.longest_break} days</dd>
        </div>
        <div className="stat">
          <dt>Each day gives you</dt>
          <dd>{summary.efficiency.toFixed(1)} days</dd>
        </div>
      </dl>
    </section>
  );
}
