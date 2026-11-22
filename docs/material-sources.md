# Material prices, recovery benchmarks and impact estimates

The version `BLR-2026-11-WARM16` fixes the inputs used to estimate each record. It selects Bengaluru buyer rates in INR, US life-cycle factors and historical US recovery benchmarks. The user supplies the weight in kilograms.

| App category | Bangalore buyback category | INR/kg | WARM proxy | kg CO₂e saved/kg | kWh equivalent saved/kg | Recovery benchmark /100 |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| Plastic | Mixed plastic | 5 | Mixed Plastics | 1.042542 | 11.400706 | 8.7 |
| Glass | Glass | 1 | Glass | 0.326664 | 0.773293 | 31.3 |
| Metal | Iron | 22 | Steel Cans | 2.041844 | 6.536859 | 70.9 |
| E-waste | E-waste | 15 | Mixed Electronics | 1.018664 | 4.615285 | 38.5 |

Kabadify publishes its Bengaluru rate card under CC BY 4.0. EcoCycle selected and regrouped four entries from the card effective 8 September 2026, consulted 22 November 2026. A buyer can pay a different amount after inspecting contamination, grade, weight or the device. Multiply the rate by weight to estimate its scrap value. [Kabadify rate card](https://kabadify.com/rates) · [Reuse license](https://creativecommons.org/licenses/by/4.0/)

The 0–100 recyclability benchmark uses the share collected for recycling by weight in the US in 2018. Plastic uses all plastics. The glass, metal and electronics proxies use glass containers, steel cans and selected consumer electronics. The score describes historical recovery of that category. Item condition and local acceptance can differ. [EPA plastics data](https://www.epa.gov/facts-and-figures-about-materials-waste-and-recycling/plastics-material-specific-data) · [EPA 2018 facts, Figure 9](https://www.epa.gov/sites/default/files/2021-01/documents/2018_ff_fact_sheet_dec_2020_fnl_508.pdf)

For climate and energy, compare one US short ton sent to an average American landfill with one short ton sent to recycling. The December 2023 WARM v16 workbook stores recycling in column C and national-average landfilling in column E on both the **Summary Data** and **Summary Data NRG** sheets. Plastic, glass, metal and electronics come from spreadsheet rows 35, 5, 3 and 46 respectively. [EPA WARM v16 source workbook](https://www.epa.gov/system/files/documents/2023-12/warm_v16.xls)

- Climate factor = (E − C) × 1,000 / 907.18474. This converts metric tons CO₂e per short ton into kilograms CO₂e per kilogram.
- Energy factor = (E − C) × 293.0710701722 / 907.18474. This converts million international-table BTU per short ton into kWh equivalent per kilogram. Energy includes process and transport energy.
- Multiply each resulting factor by the confirmed weight. For 2 kg of glass the estimate is ₹2, 0.653328 kg CO₂e, 1.546586 kWh equivalent and 2 kg diverted from landfill if the batch is accepted.
- Diverted weight represents the amount reported for recycling. Process residues, rejection after collection and local electricity mixes can change realized savings. Indian field measurements would improve these estimates. [EPA methodology](https://www.epa.gov/waste-reduction-model/documentation-chapters-emissions-energy-and-economic-factors-used-waste)
