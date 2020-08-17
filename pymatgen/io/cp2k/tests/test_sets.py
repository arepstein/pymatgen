# coding: utf-8
# Copyright (c) Pymatgen Development Team.
# Distributed under the terms of the MIT License.

import unittest
from pathlib import Path

from pymatgen.util.testing import PymatgenTest
from pymatgen.io.cp2k.sets import \
    Cp2kInputSet, DftSet, StaticSet, HybridStaticSet, \
    RelaxSet, HybridRelaxSet, CellOptSet, \
    HybridCellOptSet
from pymatgen.io.cp2k.inputs import Cp2kInput
from pymatgen import Structure, Molecule

MODULE_DIR = Path(__file__).resolve().parent

Si_structure = Structure(lattice=[[0, 2.734364, 2.734364],
                                  [2.734364, 0, 2.734364],
                                  [2.734364, 2.734364, 0]],
                         species=['Si', 'Si'],
                         coords=[[0, 0, 0], [0.25, 0.25, 0.25]])

nonsense_Structure = Structure(lattice=[[-1, -10, -100], [0.1,0.01,0.001],[7,11,21]],
                               species=['X'], coords=[[-1,-1,-1]])

molecule = Molecule(species=['C', 'H'], coords=[[0,0,0], [1,1,1]])


class SetTest(PymatgenTest):

    def setUp(self):
        pass

    def test_all_sets(self):
        for s in [Si_structure, molecule]:
            cis = Cp2kInputSet(s)
            self.assertMSONable(cis)
            cis = DftSet(s)
            self.assertMSONable(cis)
            cis = StaticSet(s)
            self.assertMSONable(cis)
            cis = HybridStaticSet(s)
            self.assertMSONable(cis)
            cis = RelaxSet(s)
            self.assertMSONable(cis)
            cis = HybridRelaxSet(s)
            self.assertMSONable(cis)
            cis = CellOptSet(s)
            self.assertMSONable(cis)
            cis = HybridCellOptSet(s)
            self.assertMSONable(cis)

    def test_aux_basis(self):
        Si_aux_bases = ['FIT', 'cFIT', 'pFIT', 'cpFIT']
        for s in Si_aux_bases:
            cis = HybridStaticSet(Si_structure, aux_basis={'Si': s})
            cis = Cp2kInput.from_string(cis.get_string())


if __name__ == "__main__":
    unittest.main()
