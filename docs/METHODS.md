# Methods

Each method is kept simple so a quality professional can read it and check it.

## Recurring deviations (`deviations.py`)
1. Group reports by (area, category).
2. Inside a group, link two reports when the word sets of their descriptions overlap enough. The overlap measure is Jaccard similarity (shared words divided by all words), after removing very common words. Default threshold: 0.4.
3. Reports linked directly or through others form a cluster. A cluster is reported only if it has at least 5 events (default) and the linked reports fall within 365 days of each other.
4. For each cluster, count the earlier reports whose CAPA had been closed before a later report in the same cluster. This is a sign a CAPA may not have worked. It needs human review.

Known limits: word overlap does not understand meaning. Two reports about the same root cause written in different words can be missed, and two unrelated reports that share common words can be linked.

## Environmental-monitoring flags (`monitoring.py`)
Counts of colony-forming units (CFU) per week are small whole numbers, so the checks use plain counting rules and a Poisson model, not a normal-curve control chart. For each location:
- **Alert / action weeks:** the number of weeks with a count at or above the alert or action limit (defaults 1 and 3).
- **Run flag:** three or more consecutive weeks with a count above zero.
- **Rate-rise flag:** the mean of the last 12 weeks is higher than the earlier mean by more than 3 Poisson standard errors.
Limits must be set to match the site's own EM program. The defaults are for the demonstration only.

## Risk ranking (`risk.py`)
score = severity weight x (1 + ln(events)) x (1 + 0.5 x CAPAs followed by recurrence). The default severity weights are 1 (minor), 3 (major) and 10 (critical). They are a judgment, not a standard. Change them to match your own risk procedure. The score tells staff where to look first. It is not a risk assessment under any regulation.

## Cost worksheet (`cost.py`)
Annual cost = (events per year) x (investigation hours x hourly rate + probability of batch loss x batch value + delay days x delay cost per day). Low and high cases scale the loss and delay terms. All inputs come from the user.

## Synthetic data (`synthetic.py`)
Random reports are drawn from short description templates. Three recurring problems and one rising EM trend are planted with fixed wording and spacing. Because the planted problems have distinctive wording, they are easier to find than real ones would be.
