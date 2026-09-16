# Domain model

## The one input

The user supplies **a single number**: how many paid leave days their company
grants them. Nothing else is asked. The year, the weekend rule and the holiday
set are the application's own knowledge, not the user's burden.

    POST /api/v1/optimizer/plan/   {"days": 18}

## Vocabulary

| Term | Meaning |
| --- | --- |
| **Workday** | Mon-Fri that is not a public holiday. The only kind of day leave is spent on. |
| **Free day** | A weekend day or a public holiday. Costs nothing. |
| **Break** | A maximal run of consecutive free days that contains at least one leave day. |
| **Cost** | Workdays inside a break -- i.e. leave days consumed. |
| **Value** | Calendar length of the break, end to end. |
| **Efficiency** | `value / cost`. The number that makes the product feel magical. |

## Holidays

Two kinds, and the distinction is load-bearing:

**Fixed Gregorian** -- same date every year, always confirmed:

| Date | Holiday |
| --- | --- |
| Jan 1 | New Year's Day |
| Jan 11 | Proclamation of Independence |
| Jan 14 | Amazigh New Year |
| May 1 | Labour Day |
| Jul 30 | Throne Day |
| Aug 14 | Oued Ed-Dahab Allegiance Day |
| Aug 20 | Revolution of the King and the People |
| Aug 21 | Youth Day |
| Nov 6 | Green March Day |
| Nov 18 | Independence Day |

**Hijri (lunar)** -- shifts ~11 days earlier each Gregorian year and is fixed
officially only by moon sighting: Eid al-Fitr (2 days), Eid al-Adha (2 days),
Fatih Muharram (1 day), Aid Al Mawlid (2 days).

Every stored holiday therefore carries `is_confirmed` and `uncertainty_days`.
A plan that leans on an unconfirmed date must say so in the UI. Guessing
silently is the one thing this product cannot afford to do.

## Rules that are decided

1. **Weekend** is Saturday and Sunday.
2. **No compensation.** A holiday landing on a weekend is simply lost -- that is
   the real Moroccan rule, and the optimizer must model reality, not wishes.
3. **Leave is spent on workdays only.**
4. **Dates are naive.** A public holiday has no timezone; the domain layer uses
   `datetime.date` and never `datetime`.
5. **One calendar year per plan** in V1. Breaks spanning Dec-Jan are a V2 concern.
