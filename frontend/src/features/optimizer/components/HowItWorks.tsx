/**
 * The explanation, for anyone who wonders whether to trust the answer.
 *
 * A native <details> rather than a hand-built accordion: it is keyboard
 * operable, announced correctly by screen readers, and it still opens if the
 * JavaScript never loads.
 */
export function HowItWorks() {
  return (
    <details className="card how">
      <summary>
        How does it work? <span className="how-chevron" aria-hidden="true" />
      </summary>

      <div className="how-body">
        <p>
          You tell us how many leave days you get. We find the days where taking{' '}
          <strong>one</strong> buys you <strong>three or four</strong>.
        </p>

        <p>
          Take August 2026: two public holidays, a weekend, two more holidays, then another weekend
          — all scattered, all looking like ordinary days off. Fill the three gaps between them, on
          the 24th, 27th and 28th, and the whole stretch fuses into{' '}
          <strong>11 days away from work for 3 days of leave</strong>.
        </p>

        <p>Doing that for a whole year takes three steps:</p>

        <ol>
          <li>
            <strong>Map the year.</strong> Every day is a working day, a weekend, or a Moroccan
            public holiday — the fixed ones and the Islamic ones.
          </li>
          <li>
            <strong>Price every bridge.</strong> For each holiday: what if you took the day before?
            Two days before? The day after? Each option has a cost in leave and a payoff in days
            off.
          </li>
          <li>
            <strong>Pick the best combination.</strong> Not the best single break — the best set of
            breaks that fits your budget. One long summer holiday can be worth less than the same
            days spread across four bridges.
          </li>
        </ol>

        <p>
          It doesn&apos;t guess. It checks every possibility and returns the mathematically best
          answer: no arrangement of your days beats the one you see. That takes about 8
          milliseconds.
        </p>

        <p className="how-caveat">
          Two things we&apos;re upfront about. A holiday landing on a weekend is simply lost —
          Morocco grants no day in lieu — so we count it as lost rather than pretend otherwise. And
          Islamic holiday dates depend on the moon sighting announced by the Ministry of Habous, so
          any break resting on one is marked <em>date not confirmed</em>. Check it before you book.
        </p>
      </div>
    </details>
  );
}
