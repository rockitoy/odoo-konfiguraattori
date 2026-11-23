# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _get_consumption_issues(self):
        """Standard Odoo flattens the BoM with ``line.product_id.type == 'consu'``. A template line of
        mrp_bom_attribute_match has no product_id after the MO is confirmed, so its move is treated as a
        foreign component with expected quantity 0 and every MO opens the consumption warning.
        Re-evaluate those moves against their own BoM line."""
        issues = super()._get_consumption_issues()
        result = []
        for issue in issues:
            order, _product, _uom, move, picked_qty, _expected = issue
            line = move and move.bom_line_id
            if line and line.component_template_id and not line.product_id and line.bom_id == order.bom_id:
                if self.env.context.get("close_production") or order.picking_type_id.create_backorder == "never":
                    qty_producing = order.product_qty
                else:
                    qty_producing = order.qty_producing
                bom_qty = order.bom_id.uom_id._compute_quantity(order.bom_id.product_qty, order.uom_id, round=False)
                expected = line.uom_id._compute_quantity(line.product_qty * qty_producing / bom_qty, move.uom_id)
                if not move.uom_id.compare(picked_qty, expected):
                    continue
                issue = issue[:5] + (expected,)
            result.append(issue)
        return result
