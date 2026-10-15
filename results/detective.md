# The detective: Kulottunga III's accession

Candidate start dates: every day 1 Jan 1174 – 31 Dec 1182 (uniform prior). Frame: lahiri-1.69.

## 1. Votes (interval intersection that tolerates errors)

The best start dates explain **18 of 24** inscriptions with no error: **6 Jul 1178 – 8 Jul 1178** (one unbroken run). Kielhorn (EI VIII, 1906): about 6–8 July 1178.

![votes](votes.png)

## 2. Bayesian model

- Most likely accession: **6 Jul 1178**
- 50% credible interval: **6 Jul 1178 – 8 Jul 1178**
- 95% credible interval: **16 Jun 1178 – 24 Jul 1178**
- Estimated error rate per carved clue: **0.090** (about 1 in 11)

![accession](accession.png)

![inscriptions](inscriptions.png)

### Per inscription

| id     |   year | kielhorn_date   | kielhorn_verdict   | kielhorn_error        |   P(miscarved) | most_likely_date   |   P(date) | wrong_clues_if_so      | alternatives                                                                                       |
|:-------|-------:|:----------------|:-------------------|:----------------------|---------------:|:-------------------|----------:|:-----------------------|:---------------------------------------------------------------------------------------------------|
| K3-16  |     19 | 1197-11-21      | error              | solar_day;regnal_year |           1    | 1197-11-21         |      0.49 | solar_day, regnal_year | 1196-10-11 (0.05, wrong: solar_month, nakshatra); 1195-11-10 (0.04, wrong: nakshatra, regnal_year) |
| K3-17  |     19 | 1196-11-12      | correct            | -                     |           0.02 | 1196-11-12         |      0.98 | -                      | 1196-11-11 (0.02, wrong: weekday)                                                                  |
| K3-18  |     34 | 1211-09-19      | correct            | -                     |           0.02 | 1211-09-19         |      0.98 | -                      | 1211-09-18 (0.02, wrong: weekday)                                                                  |
| K3-19  |     12 | 1189-12-04      | correct            | -                     |           0.05 | 1189-12-04         |      0.95 | -                      | 1190-01-01 (0.03, wrong: solar_month); 1189-12-03 (0.02, wrong: weekday)                           |
| K3-23  |      8 | 1185-07-08      | correct            | -                     |           0.25 | 1185-07-08         |      0.87 | -                      | 1186-06-28 (0.09, wrong: weekday); 1185-07-09 (0.02, wrong: weekday)                               |
| K3-24  |     16 | 1194-06-04      | error              | tithi                 |           1    | 1194-06-04         |      0.97 | tithi                  | 1194-06-05 (0.02, wrong: tithi, weekday)                                                           |
| K3-29  |     29 | 1207-03-07      | correct            | -                     |           0.04 | 1207-03-07         |      0.96 | -                      | 1207-03-08 (0.02, wrong: weekday); 1207-03-06 (0.02, wrong: weekday)                               |
| K3-30  |     37 | 1215-06-07      | correct            | -                     |           0.02 | 1215-06-07         |      0.98 | -                      | 1215-06-06 (0.02, wrong: weekday)                                                                  |
| K3-31  |     20 | -               | unresolved         | -                     |           1    | 1198-06-15         |      0.25 | solar_month, weekday   | 1198-06-16 (0.25, wrong: solar_month, weekday); 1198-05-18 (0.18, wrong: nakshatra, weekday)       |
| K3-44  |     27 | 1205-05-05      | correct            | -                     |           0.02 | 1205-05-05         |      0.98 | -                      | 1205-05-04 (0.02, wrong: weekday)                                                                  |
| K3-60  |     14 | 1192-01-02      | error              | paksha                |           1    | 1192-01-02         |      0.91 | paksha                 | 1192-01-16 (0.06, wrong: nakshatra); 1192-01-01 (0.02, wrong: paksha, weekday)                     |
| K3-90  |     10 | 1188-01-05      | error              | paksha                |           1    | 1188-01-05         |      0.92 | paksha                 | 1188-01-19 (0.06, wrong: nakshatra)                                                                |
| K3-91  |     35 | 1213-06-02      | correct            | -                     |           0.02 | 1213-06-02         |      0.98 | -                      | 1213-06-03 (0.02, wrong: weekday)                                                                  |
| K3-92  |     36 | 1214-04-14      | correct            | -                     |           0.02 | 1214-04-14         |      0.98 | -                      | 1214-04-13 (0.02, wrong: weekday)                                                                  |
| K3-93  |     37 | 1214-11-17      | correct            | -                     |           0.02 | 1214-11-17         |      0.98 | -                      | 1214-11-18 (0.02, wrong: weekday)                                                                  |
| K3-94  |     39 | 1217-01-25      | correct            | -                     |           0.02 | 1217-01-25         |      0.98 | -                      | 1217-01-24 (0.02, wrong: weekday)                                                                  |
| K3-107 |      4 | 1182-03-11      | correct            | -                     |           0.05 | 1182-03-11         |      0.95 | -                      | 1182-04-08 (0.03, wrong: solar_month); 1182-03-10 (0.02, wrong: weekday)                           |
| K3-108 |      6 | 1184-07-05      | error              | tithi                 |           0.06 | 1184-07-05         |      0.95 | -                      | 1184-06-07 (0.05, wrong: solar_month)                                                              |
| K3-109 |      6 | 1184-07-05      | error              | tithi                 |           0.06 | 1184-07-05         |      0.95 | -                      | 1184-06-07 (0.05, wrong: solar_month)                                                              |
| K3-110 |     16 | 1194-01-17      | correct            | -                     |           0    | 1194-01-17         |      1    | -                      |                                                                                                    |
| K3-111 |     20 | 1198-05-03      | error              | nakshatra             |           1    | 1198-05-03         |      0.95 | nakshatra              | 1198-03-04 (0.03, wrong: solar_month, weekday); 1198-05-02 (0.02, wrong: nakshatra, weekday)       |
| K3-112 |     23 | 1200-11-06      | correct            | -                     |           0    | 1200-11-06         |      1    | -                      |                                                                                                    |
| K3-113 |     25 | 1202-07-24      | error              | tithi                 |           0.05 | 1202-07-24         |      0.98 | -                      | 1203-07-14 (0.02, wrong: weekday)                                                                  |
| K3-114 |     32 | 1209-12-21      | error              | tithi                 |           0.02 | 1209-12-21         |      0.98 | -                      | 1209-12-22 (0.02, wrong: weekday)                                                                  |

## 3. Robustness

| assumption                                                           | most likely   | 50% interval              | 95% interval              |   eps (mean) |   log10 Bayes factor vs main | flagged (P>0.5)                                                   |
|:---------------------------------------------------------------------|:--------------|:--------------------------|:--------------------------|-------------:|-----------------------------:|:------------------------------------------------------------------|
| Main: during-day tithi/nakshatra, structured errors, year error 5%   | 6 Jul 1178    | 6 Jul 1178 – 8 Jul 1178   | 16 Jun 1178 – 24 Jul 1178 |        0.09  |                          0   | 16, 24, 31, 60, 90, 111                                           |
| Kielhorn's practice: tithi at sunrise, nakshatra any time in the day | 17 Jun 1178   | 11 Jun 1178 – 26 Jun 1178 | 8 Jun 1178 – 8 Jul 1178   |        0.139 |                         -6.4 | 16, 24, 31, 60, 90, 93, 108, 109, 111, 113, 114                   |
| Sunrise-only tithi and nakshatra                                     | 7 Jul 1178    | 17 Jun 1178 – 8 Jul 1178  | 8 Jun 1178 – 11 Sep 1178  |        0.221 |                        -16.4 | 16, 23, 24, 31, 60, 90, 91, 93, 108, 109, 110, 111, 112, 113, 114 |
| Every wrong value equally likely (no error structure)                | 6 Jul 1178    | 6 Jul 1178 – 7 Jul 1178   | 6 Jul 1178 – 11 Sep 1178  |        0.092 |                         -1   | 16, 24, 31, 60, 90, 111                                           |
| Regnal-year error 2%                                                 | 7 Jul 1178    | 6 Jul 1178 – 7 Jul 1178   | 6 Jul 1178 – 24 Jul 1178  |        0.093 |                          0.1 | 16, 24, 31, 60, 90, 111                                           |
| Regnal-year error 10%                                                | 6 Jul 1178    | 6 Jul 1178 – 8 Jul 1178   | 8 Jun 1178 – 11 Sep 1178  |        0.088 |                         -0.2 | 16, 24, 31, 60, 90, 111                                           |
