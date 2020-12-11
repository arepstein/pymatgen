import unittest
import os
from pymatgen.io.gaussian import GaussianOutput
from pymatgen.io.qchem.outputs import QCOutput

from pymatgen.analysis.quasirrho import QuasiRRHO

test_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                        'test_files', "molecules")


class TestQuasiRRHO(unittest.TestCase):

    def setUp(self):
        self.gout = GaussianOutput(os.path.join(test_dir, "quasirrho_gaufreq.log"))

    def test_qrrho_gaussian(self):
        m = 46.1
        correct_g_conc = -884.770251
        correct_g = -884.776886
        qrrho = QuasiRRHO(self.gout, conc=m)
        self.assertAlmostEqual(correct_g, qrrho.free_energy_quasiRRHO, 3)
        self.assertAlmostEqual(correct_g_conc, qrrho.concentration_corrected_g_quasiRRHO, 3)

    # def test_qrrho_gaussian(self):
    #     m = 46.1
    #     mass = self.gout.mass
    #     correct_g_conc = -76.413157
    #     correct_g = -76.419793
    #     gout_g = self.gout.final_energy + self.gout.corrections['Gibbs Free Energy']
    #     print(gout_g)
    #     qrrho = QuasiRRHO(self.gout, conc=m)
    #     self.assertAlmostEqual(correct_g, qrrho.free_energy_quasiRRHO, 4)
    #     self.assertAlmostEqual(correct_g_conc, qrrho.concentration_corrected_g_quasiRRHO, 4)