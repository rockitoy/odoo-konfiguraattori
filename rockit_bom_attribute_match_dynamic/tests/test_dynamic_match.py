# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.mrp_account.models.product import ProductProduct as MrpAccountProduct


@tagged("post_install", "-at_install")
class TestDynamicMatch(BaseCommon):
    _test_user_groups = (
        "mrp.group_mrp_manager",
        "mrp.group_mrp_routings",
        "stock.group_stock_manager",
        "product.group_product_manager",
        "product.group_product_variant",
        "uom.group_uom",
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        Attr = cls.env["product.attribute"]
        cls.attr_model = Attr.create({"name": "T Model", "create_variant": "dynamic",
                                      "value_ids": [Command.create({"name": n}) for n in ("A", "B")]})
        cls.attr_color = Attr.create({"name": "T Color", "create_variant": "dynamic",
                                      "value_ids": [Command.create({"name": n}) for n in ("Red", "Blue")]})
        cls.v_a, cls.v_b = cls.attr_model.value_ids
        cls.v_red, cls.v_blue = cls.attr_color.value_ids
        wh = cls.env.ref("stock.warehouse0")
        cls.mto = cls.env.ref("stock.route_warehouse0_mto")
        if not cls.mto.active:
            cls.mto.with_context(active_test=False).action_unarchive()
            cls.env["stock.rule"].with_context(active_test=False).search(
                [("route_id", "=", cls.mto.id)]).write({"active": True})
        cls.manufacture = wh.manufacture_pull_id.route_id

        def tmpl(name, attrs, **kw):
            return cls.env["product.template"].create({
                "name": name, "is_storable": True,
                "attribute_line_ids": [Command.create({"attribute_id": a.id, "value_ids": [Command.set(a.value_ids.ids)]})
                                       for a in attrs], **kw})
        cls.raw = cls.env["product.product"].create({"name": "T Raw", "is_storable": True, "standard_price": 5})
        # Sub-assembly matched on Model, manufactured on demand
        cls.sub = tmpl("T Sub", cls.attr_model, route_ids=[Command.set(cls.mto.ids)])
        cls.env["mrp.bom"].create({"product_tmpl_id": cls.sub.id, "product_qty": 1,
                                   "bom_line_ids": [Command.create({"product_id": cls.raw.id, "product_qty": 3})]})
        cls.fin = tmpl("T Finished", cls.attr_model | cls.attr_color)
        cls.bom = cls.env["mrp.bom"].create({"product_tmpl_id": cls.fin.id, "product_qty": 1,
                                             "bom_line_ids": [Command.create({"component_template_id": cls.sub.id, "product_qty": 2})]})

    def _ptavs(self, tmpl, values):
        return tmpl.attribute_line_ids.product_template_value_ids.filtered(lambda v: v.product_attribute_value_id in values)

    def _fin_variant(self, values):
        return self.fin._create_product_variant(self._ptavs(self.fin, values))

    def _sub_variant(self, value):
        return self.sub.with_context(active_test=False).product_variant_ids.filtered(
            lambda p: p.product_template_attribute_value_ids.product_attribute_value_id == value)

    def test_00_dynamic_templates_have_no_variants(self):
        self.assertFalse(self.sub.product_variant_ids)

    def test_01_upstream_skips_missing_variant(self):
        fin = self._fin_variant(self.v_b | self.v_red)
        line = self.bom.bom_line_ids
        self.assertFalse(self.bom._get_component_template_product(line, fin, line.product_id))
        self.assertFalse(self._sub_variant(self.v_b))

    def test_02_explode_creates_matched_variant(self):
        fin = self._fin_variant(self.v_b | self.v_red)
        _boms, lines = self.bom.explode(fin, 1)
        self.assertEqual(len(lines), 1)
        created = self._sub_variant(self.v_b)
        self.assertEqual(len(created), 1)
        self.assertEqual(lines[0][0].product_id, created)
        self.assertEqual(lines[0][1]["qty"], 2)
        # second explode reuses the same variant
        self.bom.explode(fin, 1)
        self.assertEqual(len(self.sub.product_variant_ids), 1)
        # new manufactured variant is valued from its own BoM (3 x 5)
        self.assertEqual(created.standard_price, 15)

    def test_03_mo_and_mto_chaining(self):
        fin = self._fin_variant(self.v_a | self.v_blue)
        mo = self.env["mrp.production"].create({"product_id": fin.id, "bom_id": self.bom.id, "product_qty": 1})
        mo.action_confirm()
        sub_a = self._sub_variant(self.v_a)
        self.assertEqual(mo.move_raw_ids.product_id, sub_a)
        self.assertEqual(mo.move_raw_ids.product_uom_qty, 2)
        self.assertEqual(mo.move_raw_ids.procure_method, "make_to_order")
        child = self.env["mrp.production"].search([("product_id", "=", sub_a.id)])
        self.assertEqual(len(child), 1, "MTO must chain a manufacturing order for the created variant")
        self.assertEqual(child.move_raw_ids.product_id, self.raw)
        self.assertFalse(self.bom.bom_line_ids.product_id, "template line must stay template-based")

    def test_04_bom_cost_counts_template_lines(self):
        fin_a = self._fin_variant(self.v_a | self.v_red)
        fin_b = self._fin_variant(self.v_b | self.v_red)
        self.bom.explode(fin_a, 1)
        self.bom.explode(fin_b, 1)
        sub_a, sub_b = self._sub_variant(self.v_a), self._sub_variant(self.v_b)
        sub_a.standard_price, sub_b.standard_price = 20, 30
        line = self.bom.bom_line_ids
        # Upstream explode leaves the last resolved variant on the line until an MO is confirmed:
        # standard Odoo (mrp_account) would then price fin_a with sub_b ...
        self.assertEqual(line.product_id, sub_b)
        self.assertEqual(MrpAccountProduct._get_bom_components_price(fin_a, self.bom), 60)
        # ... and with the line in its normal state (no product_id) the cost computation crashes
        # (empty uom recordset: "Expected singleton: uom.uom()").
        line.product_id = False
        with self.assertRaises(ValueError):
            MrpAccountProduct._get_bom_components_price(fin_a, self.bom)
        # Fixed: resolved per variant
        self.assertEqual(fin_a._compute_bom_price(self.bom), 40)
        self.assertEqual(fin_b._compute_bom_price(self.bom), 60)
        fin_a.button_bom_cost()
        self.assertEqual(fin_a.standard_price, 40)

    def test_05_bom_structure_report(self):
        fin = self._fin_variant(self.v_b | self.v_blue)
        self.bom.explode(fin, 1)
        data = self.env["report.mrp.report_bom_structure"]._get_report_data(self.bom.id, searchVariant=fin.id)
        comps = data["lines"]["components"]
        self.assertEqual(len(comps), 1)
        self.assertEqual(comps[0]["product_id"], self._sub_variant(self.v_b).id)

    def test_06_conditional_lines_in_report_and_cost(self):
        """'Apply on Variants' lines and operations must survive the virtual BoM (NewId values)."""
        extra = self.env["product.product"].create({"name": "T Extra", "standard_price": 7})
        ptav_a = self._ptavs(self.fin, self.v_a)
        wc = self.env["mrp.workcenter"].create({"name": "T WC", "costs_hour": 60})
        self.bom.write({
            "bom_line_ids": [Command.create({"product_id": extra.id, "product_qty": 1,
                                             "bom_product_template_attribute_value_ids": [Command.set(ptav_a.ids)]})],
            "operation_ids": [Command.create({"name": "T Op", "workcenter_id": wc.id, "time_cycle_manual": 10,
                                              "bom_product_template_attribute_value_ids": [Command.set(ptav_a.ids)]})],
        })
        fin_a = self._fin_variant(self.v_a | self.v_red)
        fin_b = self._fin_variant(self.v_b | self.v_red)
        self.bom.explode(fin_a, 1)
        self.bom.explode(fin_b, 1)
        self._sub_variant(self.v_a).standard_price = 20
        self._sub_variant(self.v_b).standard_price = 30
        rep = self.env["report.mrp.report_bom_structure"]
        names = [c["product_id"] for c in rep._get_report_data(self.bom.id, searchVariant=fin_a.id)["lines"]["components"]]
        self.assertIn(extra.id, names)
        names_b = [c["product_id"] for c in rep._get_report_data(self.bom.id, searchVariant=fin_b.id)["lines"]["components"]]
        self.assertNotIn(extra.id, names_b)
        # A: 2 x 20 + 7 + operation 10 min at 60/h = 10 ; B: 2 x 30
        self.assertAlmostEqual(fin_a._compute_bom_price(self.bom), 57, places=2)
        self.assertAlmostEqual(fin_b._compute_bom_price(self.bom), 60, places=2)

    def test_07_no_consumption_warning_for_template_lines(self):
        fin = self._fin_variant(self.v_b | self.v_blue)
        mo = self.env["mrp.production"].create({"product_id": fin.id, "bom_id": self.bom.id, "product_qty": 1})
        mo.action_confirm()
        mo.qty_producing = 1
        move = mo.move_raw_ids
        move.quantity, move.picked = 2, True
        self.assertFalse(mo._get_consumption_issues(), "exact consumption of a template line is not an issue")
        move.quantity = 3
        issues = mo._get_consumption_issues()
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0][4:], (3, 2))
