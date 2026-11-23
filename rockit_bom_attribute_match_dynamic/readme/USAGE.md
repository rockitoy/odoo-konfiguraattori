Nothing to configure. Install the module and use *Component (product template)* on BoM
lines as described in *mrp_bom_attribute_match*.

- Component attributes can use the *Dynamically* variant creation mode: the matching
  variant is created when a manufacturing order (or an MTO chain) needs it.
- *Compute Price from BoM* and the BoM structure report include template lines and
  conditional (*Apply on Variants*) lines.

Tests: `odoo-bin -d <test db> -i rockit_bom_attribute_match_dynamic --test-enable
--test-tags /mrp_bom_attribute_match,/rockit_bom_attribute_match_dynamic`.
