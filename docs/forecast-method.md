# Weekly ward collection scenario

The color on the municipal map represents estimated kilograms of recyclable material collected in a week. A hotspot means a relatively large modeled collection load. A city would need local scale tickets and actual stop coordinates before using these estimates to assign trucks.

## Observed inputs

Austin Resource Recovery publishes individual vehicle loads. The public-domain source marks the weight unit as pounds. The download groups positive **RECYCLING - SINGLE STREAM** records by report date, then sums dates into weeks starting Monday. The bundled snapshot covers 66,876 loads and 286 observed weeks from 4 January 2016 through the week of 28 June 2021. The week starting 15 February 2021 has no matching rows and is excluded. [City of Austin collection dataset](https://data.austintexas.gov/d/mbnu-4wq9) · [Publisher metadata and public-domain designation](https://data.austintexas.gov/api/views/mbnu-4wq9)

## Constructed inputs

For each observed week, multiply the city's total by 0.45359237 to convert pounds to kilograms. Scale by 0.075 to create a six-ward demonstration. The 7.5% scale and the six base shares are design assumptions. Each base share varies with an annual sine wave of amplitude 0.15 and seeded noise between −0.09 and +0.09. Divide by the sum of the adjusted shares so that the six allocations sum to exactly the scaled weekly weight.

Indiranagar, Koramangala, Jayanagar, Malleshwaram, HSR Layout and Whitefield are real place names. Their map points are approximate neighborhood centers. All ward measurements, rankings and forecast loads are synthetic. Citizen scans belong to a separate record system and do not train this model.

## Training and measured results

Ridge regression in scikit-learn learns each ward's average level and two annual sine/cosine cycles. Week of year and ward ID are the only inputs. The first 234 observed weeks train the evaluation model. The following 52 observed weeks, from 29 June 2020 through 28 June 2021, provide 312 unseen ward-week rows. The split is chronological across all six wards. The fixed regularization parameter is 1.0.

| Error on held-out synthetic ward-weeks | kg per ward-week |
| --- | ---: |
| Mean absolute error (MAE) | 1,564.57 |
| Root mean square error (RMSE) | 2,144.14 |
| Baseline MAE, always predict each ward's training average | 1,949.56 |

MAE measures the typical size of the miss. RMSE gives more weight to large misses. These numbers describe the synthetic evaluation task. Real Bengaluru ward-level predictive accuracy remains unknown. The deployed model refits all 286 observed weeks after evaluation. Future dates use the learned yearly cycle. A fixed seasonal model cannot anticipate new collection policies, population changes, holidays or disruptions.

## Reproduce the model

From the repository root, use the project Python environment to run `python -m backend.forecast_tools.train`. It reads the checked-in weekly CSV and replaces the local coefficient file atomically. Training never fetches data from an external service. To explicitly re-download the source snapshot, run `python -m backend.forecast_tools.download` first. An upstream correction can change its hash and measured errors. The model artifact records the input SHA-256 and training library version.

The API calls `backend.forecast.forecast(week, weeks)`. An omitted date starts on the next Monday. Supply a specific date to select its Monday. The horizon accepts one through twelve weeks. Every response carries the source, synthetic flag and held-out metrics. `refresh_model()` retrains the same model against the immutable snapshot. Set `FORECAST_MODEL_PATH` to a writable persistent path to retain refreshed coefficients through a redeploy. Until that path has a model, inference uses the bundled artifact.

