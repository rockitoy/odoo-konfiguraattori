**Status: Beta** – tested in a demo environment, not yet in customer production.

Small extension of OCA *mrp_bom_attribute_match* (not modified; shipped in this
repository as a vendored Odoo 20 copy, see `VENDORED.md`).

*mrp_bom_attribute_match* adds a *Component (product template)* field to BoM lines: the
line points to a component template and the component variant is chosen from the
attribute values of the produced variant (for example Model + Size → the matching raw
frame variant). One line replaces many variant-specific lines.

This module fixes four things found when using it on Odoo 20:

1. **Dynamic attributes.** When the matching component variant does not exist yet, the
   OCA module silently skips the line and the component is missing from the
   manufacturing order. Here the variant is created (or reactivated) with the standard
   `product.template._create_product_variant` whenever the BoM is exploded (manufacturing
   order, MTO chain). Read-only reports do not create variants. A newly created
   manufactured variant gets its cost from its own BoM.
2. **BoM cost.** Odoo 20 (`mrp_account._get_bom_components_price`) computes the cost from
   `line.product_id.standard_price`. A template line has no `product_id`, so the
   computation fails with *Expected singleton: uom.uom()*; if the line still carries the
   previous variant left by the OCA `explode`, the cost is computed with the wrong
   variant. Lines are now resolved per variant before costing.
3. **Conditional lines in the virtual BoM.** The OCA module resolves template lines on a
   virtual copy of the BoM (`bom.new(origin=bom)`) used by the BoM structure report and
   cost computation. In Odoo 20 the *Apply on Variants* values of that copy are NewId
   records, so every conditional line and operation was skipped. The skip decision is
   now taken from the original line.
4. **Consumption warning.** Standard Odoo considers the component of a template line
   "unexpected" (expected quantity 0) because the line has no product on the confirmed
   MO, so every MO opened the consumption warning. The expected quantity is now taken
   from the line quantity.
