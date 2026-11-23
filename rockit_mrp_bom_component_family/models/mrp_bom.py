# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    component_family_ids = fields.Many2many(
        "product.template",
        "mrp_bom_line_component_family_rel",
        "line_id",
        "template_id",
        string="Component families",
        help="Candidate component templates, in order. The first one whose attribute "
        "values all include the produced variant's values is used, e.g. one frame "
        "family per model with the size as variant.",
    )

    @api.model
    def _sync_primary_family(self, vals):
        """mrp_bom_attribute_match only resolves lines that have a component template:
        keep the first family as that template so users only maintain the families."""
        families = vals.get("component_family_ids")
        if not families:
            return vals
        ids = self.env["mrp.bom.line"].new({"component_family_ids": families}).component_family_ids._origin.ids
        if ids and vals.get("component_template_id") not in ids:
            vals = dict(vals, component_template_id=ids[0], product_id=False)
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([self._sync_primary_family(v) for v in vals_list])

    def write(self, vals):
        return super().write(self._sync_primary_family(vals))

    @api.onchange("component_family_ids")
    def _onchange_component_family_ids(self):
        families = self.component_family_ids._origin
        if families and self.component_template_id not in families:
            self.component_template_id = families[:1]


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    @api.model
    def _component_family_matches(self, template, product):
        """True if every variant-creating attribute line of ``template`` contains one of
        ``product``'s attribute values."""
        values = product.product_template_attribute_value_ids.product_attribute_value_id
        lines = template.valid_product_template_attribute_line_ids.filtered(
            lambda line: line.attribute_id.create_variant != "no_variant"
        )
        return bool(lines) and all(line.value_ids & values for line in lines)

    def _pick_component_family(self, bom_line, product):
        # ._origin: on the virtual BoM of mrp_bom_attribute_match (bom.new(origin=bom),
        # used by BoM cost and the structure report) x2many values are NewId copies
        candidates = (bom_line.component_family_ids or bom_line.component_template_id)._origin
        for template in candidates:
            if self._component_family_matches(template, product):
                return template
        return self.env["product.template"]

    @api.model
    def _component_variant_for(self, template, product, create=False):
        """Variant of ``template`` whose attribute values match ``product``."""
        values = product.product_template_attribute_value_ids.product_attribute_value_id
        lines = template.valid_product_template_attribute_line_ids.filtered(
            lambda line: line.attribute_id.create_variant != "no_variant"
        )
        combination = lines.product_template_value_ids.filtered(
            lambda v: v.ptav_active and v.product_attribute_value_id in values
        )
        empty = self.env["product.product"]
        if not lines or len(combination) != len(lines):
            return empty
        variant = template._get_variant_for_combination(combination)
        if not variant and create and not getattr(self.env.cr, "readonly", False):
            variant = template._create_product_variant(combination)
        return variant if variant and variant.active else empty

    def _get_component_template_product(self, bom_line, bom_product_id, line_product_id):
        if not bom_line.component_family_ids or not bom_product_id:
            return super()._get_component_template_product(bom_line, bom_product_id, line_product_id)
        family = self._pick_component_family(bom_line, bom_product_id)
        if not family:
            return self.env["product.product"]
        if family == bom_line.component_template_id._origin:
            return super()._get_component_template_product(bom_line, bom_product_id, line_product_id)
        create = bool(self.env.context.get("bom_attribute_match_create_variant"))
        return self._component_variant_for(family, bom_product_id, create=create)
