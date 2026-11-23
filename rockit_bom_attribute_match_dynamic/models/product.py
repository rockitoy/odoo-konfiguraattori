# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models

from .mrp_bom import CREATE_CTX


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_bom_components_price(self, bom, boms_to_recompute=False, byproduct_bom=False):
        # Odoo sums line.product_id.standard_price; a component-template line has no
        # product_id, so it would be counted as 0. Resolve the lines for this variant first.
        if bom and self and any(bom.bom_line_ids.mapped("component_template_id")):
            bom = bom.with_context(**{CREATE_CTX: True})._prepare_dynamic_bom(bom, self)
        return super()._get_bom_components_price(
            bom, boms_to_recompute=boms_to_recompute, byproduct_bom=byproduct_bom
        )
