# odoo-konfiguraattori – variant BoMs for configurable products (Odoo 20 Community)

> **Status: Beta** – tested in a demo environment, not yet in customer production.
> **Tila: Beta** – testattu demoympäristössä, ei vielä asiakastuotannossa.

Modules by [RockIT Oy](https://rockit.fi) for configurable products in Odoo 20 Community
Edition: one bill of materials for a whole product family, where each line picks the
right component variant (or component family) from the attribute values of the produced
variant. Variants can be created on demand (dynamic attributes), so not every combination
has to exist beforehand. No PLM modules are needed.

A demo company using these modules is at <https://plm.rockit.fi> (presentation on
request). With the PLM extensions of [AvoinPLM](https://github.com/rockitoy/avoinplm) the
bridge module `rockit_plm_component_family_bridge` (in that repository) makes these lines
follow PLM revisions too.

## Modules

| Module | Description |
|---|---|
| [mrp_bom_attribute_match](mrp_bom_attribute_match) | OCA module (vendored, see [VENDORED.md](VENDORED.md)): a BoM line points to a component *template*; the variant is chosen by attribute values. |
| [rockit_bom_attribute_match_dynamic](rockit_bom_attribute_match_dynamic) | Creates missing component variants on demand (dynamic attributes), correct BoM cost and BoM structure report for template and conditional lines, no false consumption warnings. |
| [rockit_mrp_bom_component_family](rockit_mrp_bom_component_family) | One BoM line, several component families (templates): the first family whose attribute values match the produced variant is used. |

## Requirements and installation

- Odoo 20.0 Community Edition (`mrp`, `mrp_account`).
- Put this repository in the `addons_path` and install `rockit_mrp_bom_component_family`
  and `rockit_bom_attribute_match_dynamic` (they pull in `mrp_bom_attribute_match`).
- Tests: `odoo-bin -d <test db> -i rockit_mrp_bom_component_family,rockit_bom_attribute_match_dynamic
  --test-enable --test-tags /mrp_bom_attribute_match,/rockit_bom_attribute_match_dynamic,/rockit_mrp_bom_component_family`.

No special user rights are needed beyond the standard Manufacturing groups.

## Roadmap

- A rules engine (formulas and constraints for quantities and component choice) is
  planned but not started. Today the component choice is driven by attribute values and
  the order of component families only.
- When OCA merges `mrp_bom_attribute_match` for 20.0 (PR
  [OCA/manufacture#1871](https://github.com/OCA/manufacture/pull/1871)), the vendored copy
  is replaced by the official one.

## License

GNU Affero General Public License v3.0 or later (AGPL-3.0), see [LICENSE](LICENSE). The
vendored OCA module keeps its original authors and copyright notices.

## Status and support

Beta: automated tests, used in the plm.rockit.fi demo, not yet in customer production.
Test in a copy of your database first. Issues and pull requests are welcome.
Implementation and support: RockIT Oy, Tampere, Finland – <https://rockit.fi>,
mikko.salmela@rockit.fi.

---

## Suomeksi

> **Beta – testattu demoympäristössä, ei vielä asiakastuotannossa.**

Tuotekonfiguraattorin perusosat Odoo 20 Community -versioon: yksi osaluettelo koko
tuoteperheelle. Jokainen rivi valitsee oikean komponenttivariantin tai komponenttiperheen
valmistettavan variantin ominaisuuksien (esim. malli ja koko) perusteella. Variantit
voivat syntyä vasta tilattaessa, joten kaikkia yhdistelmiä ei tarvitse perustaa
etukäteen. Rivejä ei tarvitse kirjoittaa erikseen jokaiselle yhdistelmälle, ja
osaluettelon kustannus ja rakenneraportti lasketaan oikein.

Moduulit eivät tarvitse PLM:ää. Kun käytössä on myös [AvoinPLM](https://github.com/rockitoy/avoinplm),
sen siltamoduuli saa nämä rivit seuraamaan myös PLM-revisioita.

**Tiekartta:** sääntömoottori (kaavat ja rajoitteet määrille ja komponenttivalinnoille)
on suunnitteilla, mutta sitä ei ole vielä aloitettu.

**Lisenssi:** AGPL-3.0 tai uudempi. **Yhteys:** RockIT Oy, Tampere, <https://rockit.fi>,
mikko.salmela@rockit.fi.
