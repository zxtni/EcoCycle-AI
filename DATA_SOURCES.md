# Data sources

- The photo model was trained and evaluated on public image datasets. The selected demo photo is a held-out dataset example. [Model card](MODEL_CARD.md)
- Austin’s observed recycling loads inform the historical curve. Every Bengaluru ward allocation and forecast is synthetic. [Forecast method](docs/forecast-method.md)
- Bengaluru buyer rates, EPA WARM v16 factors and historical US material recovery rates inform the calculator. The rates and factors are dated and use representative material categories. [Material sources](docs/material-sources.md)
- OpenStreetMap supplies live drop-off listings and map tiles. Tags and coverage vary. Local seed listings and seeded citizen records are synthetic. [OpenStreetMap contributors](https://www.openstreetmap.org/copyright)
- The homepage still life is an ImageGen illustration. It was never used in model training or evaluation.
