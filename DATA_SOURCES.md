# Data sources

- The photo model was trained and evaluated on public image datasets. The selected demo photo is a held-out dataset example. [Model card](MODEL_CARD.md)
- Austin’s observed recycling loads inform the historical curve. Every Bengaluru ward allocation and forecast is synthetic. [Forecast method](docs/forecast-method.md)
- Bengaluru buyer rates, EPA WARM v16 factors and historical US material recovery rates inform the calculator. The rates and factors are dated and use representative material categories. [Material sources](docs/material-sources.md)
- The locator searches a saved directory from the Geofabrik India extract of OpenStreetMap. When the directory has no matches, the locator tries live Overpass. OpenStreetMap data is available under the ODbL. A material filter requires an explicit recycling tag. Confirm accepted materials and hours with the facility. Local seed listings and seeded citizen records are synthetic. [Geofabrik India extract](https://download.geofabrik.de/asia/india/) · [OpenStreetMap contributors and ODbL](https://www.openstreetmap.org/copyright)
- The homepage still life is an ImageGen illustration. It was never used in model training or evaluation.

## Refresh the recycling directory

Download the latest India `.osm.pbf` from Geofabrik with the project environment active. Run `python -m pip install osmium` and then `python -m scripts.extract_recycling india-latest.osm.pbf backend/recycling_india.json`. Commit the generated directory and rebuild the API image. The date displayed by the app comes from the extract metadata.
