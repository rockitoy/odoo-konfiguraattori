# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestComponentFamily(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Attr = cls.env["product.attribute"]
        cls.model = Attr.create({"name": "CF Model", "value_ids": [(0, 0, {"name": "Gravel"}), (0, 0, {"name": "City"})]})
        cls.size = Attr.create({"name": "CF Size", "value_ids": [(0, 0, {"name": "S"}), (0, 0, {"name": "M"})]})
        cls.gravel, cls.city = cls.model.value_ids
        PT = cls.env["product.template"]

        def tmpl(name, models, price):
            return PT.create({"name": name, "type": "consu", "standard_price": price, "attribute_line_ids": [
                (0, 0, {"attribute_id": cls.model.id, "value_ids": [(6, 0, models.ids)]}),
                (0, 0, {"attribute_id": cls.size.id, "value_ids": [(6, 0, cls.size.value_ids.ids)]})]})

        cls.fam_gravel = tmpl("CF Frame Gravel", cls.gravel, 100)
        cls.fam_other = tmpl("CF Frame other", cls.city, 50)
        cls.assembly = tmpl("CF Painted frame", cls.gravel | cls.city, 0)
        cls.line_vals = {"product_qty": 1, "component_family_ids": [(6, 0, (cls.fam_gravel | cls.fam_other).ids)]}
        cls.bom = cls.env["mrp.bom"].create({"product_tmpl_id": cls.assembly.id, "bom_line_ids": [(0, 0, cls.line_vals)]})

    def _variant(self, model, size):
        return self.assembly.product_variant_ids.filtered(
            lambda p: set(p.product_template_attribute_value_ids.mapped("name")) == {model, size})

    def test_primary_family_synced(self):
        self.assertEqual(self.bom.bom_line_ids.component_template_id, self.fam_gravel)

    def test_explode_picks_family_and_variant(self):
        for model, family in (("Gravel", self.fam_gravel), ("City", self.fam_other)):
            lines = self.bom.explode(self._variant(model, "M"), 1)[1]
            component = lines[0][0].product_id
            self.assertEqual(component.product_tmpl_id, family)
            self.assertIn("M", component.product_template_attribute_value_ids.mapped("name"))

    def test_virtual_bom_for_cost_and_report(self):
        variant = self._variant("City", "S")
        virtual = self.bom._prepare_dynamic_bom(self.bom, variant)
        self.assertEqual(virtual.bom_line_ids.product_id.product_tmpl_id, self.fam_other)
        data = self.env["report.mrp.report_bom_structure"]._get_report_data(self.bom.id, searchVariant=variant.id)
        names = [c["name"] for c in data["lines"]["components"]]
        self.assertTrue(any("CF Frame other" in n for n in names), names)
