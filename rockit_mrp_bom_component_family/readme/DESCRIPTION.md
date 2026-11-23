**Status: Beta** – tested in a demo environment, not yet in customer production.

Extends *mrp_bom_attribute_match* (not modified): an attribute-matched BoM line can list
several **component families** (product templates). For each produced variant the first
family whose attribute values all match is used, and the component variant is taken from
it. Example: one *Raw frame* line in the painted-frame BoM, with families *Raw frame
Gravel* (Model = Gravel, Size S–XL) and *Raw frame, other models*. The number of BoM lines
no longer grows with the number of model × size combinations.

The first family is kept as the line's *Component (product template)* automatically.
