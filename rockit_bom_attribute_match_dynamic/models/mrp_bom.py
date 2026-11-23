# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import models

_logger = logging.getLogger(__name__)

CREATE_CTX = "bom_attribute_match_create_variant"


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    def explode(self, product, quantity, picking_type=False, never_attribute_values=False):
        # Exploding drives procurement (MO components, MTO chaining): allow creating
        # missing component variants here.
        return super(MrpBom, self.with_context(**{CREATE_CTX: True})).explode(
            product, quantity, picking_type=picking_type, never_attribute_values=never_attribute_values
        )

    def _get_component_template_product(self, bom_line, bom_product_id, line_product_id):
        product = super()._get_component_template_product(bom_line, bom_product_id, line_product_id)
        if product or not bom_line.component_template_id or not self.env.context.get(CREATE_CTX):
            return product
        return self._create_matched_component_variant(bom_line, bom_product_id)

    def _create_matched_component_variant(self, bom_line, bom_product):
        """Create (or reactivate) the component variant whose attribute values match ``bom_product``.

        mrp_bom_attribute_match silently skips the line when the matching combination
        has no variant yet. With dynamic attributes variants only exist once needed,
        so the component would disappear from the MO. Here the variant is created via
        the standard ``product.template._create_product_variant`` (dynamic templates only).
        """
        empty = self.env["product.product"]
        comp = bom_line.component_template_id
        if not bom_product or getattr(self.env.cr, "readonly", False):
            return empty
        comp_lines = comp.valid_product_template_attribute_line_ids.filtered(
            lambda line: line.attribute_id.create_variant != "no_variant"
        )
        prod_attrs = bom_product.valid_product_template_attribute_line_ids.attribute_id
        if not comp_lines or any(attr not in prod_attrs for attr in comp_lines.attribute_id):
            return empty
        values = bom_product.product_template_attribute_value_ids.product_attribute_value_id
        combination = comp_lines.product_template_value_ids.filtered(
            lambda ptav: ptav.ptav_active and ptav.product_attribute_value_id in values
        )
        if len(combination) != len(comp_lines):
            _logger.info(
                "No complete attribute combination of %s for %s: component skipped.",
                comp.display_name,
                bom_product.display_name,
            )
            return empty
        variant = comp._create_product_variant(combination, log_warning=True)
        if not variant or not variant.active:
            return empty
        if not variant.standard_price and self._bom_find(variant).get(variant):
            # A new manufactured variant would otherwise be valued at 0.
            variant.sudo()._set_price_from_bom()
        _logger.info("Created/activated component variant %s for %s", variant.display_name, bom_product.display_name)
        return variant


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    def _skip_bom_line(self, product, never_attribute_values=False):
        # mrp_bom_attribute_match resolves template lines on a virtual copy of the BoM
        # (``bom.new(origin=bom)``, used by the BoM structure report and BoM cost). In Odoo 20
        # the copied "Apply on Variants" values are NewIds, so the intersection with the
        # variant's real values is empty and every conditional line was skipped.
        if self._origin and self.id != self._origin.id:
            return self._origin._skip_bom_line(product, never_attribute_values=never_attribute_values)
        return super()._skip_bom_line(product, never_attribute_values=never_attribute_values)


class MrpRoutingWorkcenter(models.Model):
    _inherit = "mrp.routing.workcenter"

    def _skip_operation_line(self, product, never_attribute_values=False):
        # Same NewId issue as mrp.bom.line._skip_bom_line for operations of the virtual BoM.
        if self._origin and self.id != self._origin.id:
            return self._origin._skip_operation_line(product, never_attribute_values=never_attribute_values)
        return super()._skip_operation_line(product, never_attribute_values=never_attribute_values)
