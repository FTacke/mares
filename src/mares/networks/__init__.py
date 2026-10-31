"""Networks: the single command line entry point for both network pipelines.

* ``network_v0`` (:mod:`mares.network_v0`) -- the earlier survey design: CSV package
  ``mares-network-package/v0-draft``, closeness 1-5, groups as drawn outlines. Kept unchanged.
* ``network_v1`` (:mod:`mares.network_v1`) -- the stand-alone network survey (context sheet, tables A, B, C):
  case folders ``network_v1/{pilots,cases}/<case>/{data,graphics}``, eight standard figures.

``python -m mares.networks <v0 command> ...`` keeps working (v0, as before); ``python -m mares.networks v0 ...``
says the same explicitly; ``python -m mares.networks v1 ...`` runs the new pipeline.
Versions: ``docs/architecture/network-versions.md``.
"""
