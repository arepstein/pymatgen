"""
Utility functions for assisting with cp2k IO
"""

import os
import re
import numpy as np
from ruamel import yaml
from monty.serialization import loadfn
from pathlib import Path

from pymatgen import SETTINGS

MODULE_DIR = Path(__file__).resolve().parent


def _postprocessor(s):
    """
    Helper function to post process the results of the pattern matching functions in Cp2kOutput and turn them to
    python types.
    """
    s = s.rstrip()  # Remove leading/trailing whitespace
    s = s.replace(" ", "_")  # Remove whitespaces

    if s.lower() == "no" or s.lower() == "none":
        return False
    elif s.lower() == "yes" or s.lower() == 'true':
        return True
    elif re.match(r"^-?\d+$", s):
        try:
            return int(s)
        except ValueError:
            raise IOError("Error in parsing CP2K output file.")
    elif re.match(r"^[+\-]?(?=.)(?:0|[1-9]\d*)?(?:\.\d*)?(?:\d[eE][+\-]?\d+)?$", s):
        try:
            return float(s)
        except ValueError:
            raise IOError("Error in parsing CP2K output file.")
    elif re.match(r"\*+", s):
        try:
            return np.NaN
        except ValueError:
            raise IOError("Error in parsing CP2K output file.")
    else:
        return s


def natural_keys(text):
    """
    Sort text by numbers coming after an underscore with natural number
    convention,
    Ex: [file_1, file_12, file_2] becomes [file_1, file_2, file_12]
    """
    def atoi(t):
        return int(t) if t.isdigit() else t

    return [atoi(c) for c in re.split(r'_(\d+)', text)]


def get_basis_and_potential(species, d, cardinality='DZVP', functional='PBE'):
    """
    Given a specie and a potential/basis type, this function accesses the available basis sets and potentials.
    Generally, the GTH potentials are used with the GTH basis sets.

    Args:
        species: (list) list of species for which to get the potential/basis strings
        d: (dict) a dictionary specifying how bases and/or potentials should be assigned to species
            E.g. {'Si': {'cardinality': 'DZVP', 'sr': True}, 'O': {'cardinality': 'TZVP'}}
        functional: (str) functional type. Default: 'PBE'
        basis_type: (str) the basis set type. Default: 'MOLOPT'
        cardinality: (str) basis set cardinality. Default: 'DZVP'

    Returns:
        (dict) of the form {'specie': {'potential': potential, 'basis': basis}...}
    """

    potential_filename = SETTINGS.get(
        "PMG_DEFAULT_CP2K_POTENTIAL_FILE", "GTH_POTENTIALS"
    )
    basis_filenames = ['BASIS_MOLOPT', 'BASIS_MOLOPT_UCL']

    functional = functional or SETTINGS.get(
        "PMG_DEFAULT_FUNCTIONAL", "PBE"
    )
    cardinality = cardinality or SETTINGS.get(
        "PMG_DEFAULT_BASIS_CARDINALITY", "DZVP"
    )
    basis_and_potential = {
        "basis_filenames": basis_filenames,
        "potential_filename": potential_filename,
    }
    for s in species:
        if s not in d:
            d[s] = {}
        if 'sr' not in d[s]:
            d[s]['sr'] = True
        if 'cardinality' not in d[s]:
            d[s]['cardinality'] = cardinality

    with open(os.path.join(MODULE_DIR, 'basis_molopt.yaml'), 'rt') as f:
        data_b = yaml.load(f, Loader=yaml.Loader)
    with open(os.path.join(MODULE_DIR, 'gth_potentials.yaml'), 'rt') as f:
        data_p = yaml.load(f, Loader=yaml.Loader)

    for s in species:
        basis_and_potential[s] = {}
        b = [_ for _ in data_b[s] if d[s]['cardinality'] in _.split('-')]
        if d[s]['sr'] and any(['SR' in _ for _ in b]):
            b = [_ for _ in b if 'SR' in _]
        else:
            b = [_ for _ in b if 'SR' not in _]
        if 'q' in d[s]:
            b = [_ for _ in b if d[s]['q'] in _]
        if len(b) == 0:
            raise LookupError('NO BASIS OF THAT TYPE AVAILABLE')
        elif len(b) > 1:
            raise LookupError('AMBIGUITY IN BASIS. PLEASE SPECIFY FURTHER')

        basis_and_potential[s]['basis'] = b[0]
        p = [_ for _ in data_p[s] if functional in _.split('-')]
        if len(p) == 0:
            raise LookupError('NO PSEUDOPOTENTIAL OF THAT TYPE AVAILABLE')
        if len(p) > 1:
            print(p)
            raise LookupError('AMBIGUITY IN POTENTIAL. PLEASE SPECIFY FURTHER')

        basis_and_potential[s]['potential'] = p[0]

    return basis_and_potential


def get_aux_basis(species, basis_type="cFIT"):
    """
    Get auxiliary basis info for a list of species.

    Args:
        species (list): list of species to get info for
        basis_type (str): default basis type to look for. Otherwise, follow defaults.

            Basis types:
                FIT
                cFIT
                pFIT
                cpFIT
                GTH-def2
                aug-{FIT,cFIT,pFIT,cpFIT, GTH-def2}
    """

    basis = {k: {} for k in species}
    aux_bases = loadfn(os.path.join(MODULE_DIR, 'aux_basis.yaml'))
    for k in species:
        if isinstance(aux_bases[k], list):
            for i in aux_bases[k]:
                if i.startswith(basis_type):
                    basis[k] = i
                    break
        else:
            basis[k] = aux_bases[k]
    return basis


def get_unique_site_indices(structure):
    """
    Get unique site indices for a structure according to site properties. Whatever site-property has the most
    unique values is used for indexing.

    For example, if you have magnetic CoO with half Co atoms having a positive moment, and the other
    half having a negative moment. Then this function will create a dict of sites for Co_1, Co_2, O.

    This creates unique sites, based on site properties, but does not have anything to do with turning
    those site properties into CP2K input parameters.
    """
    sites = {}
    _property = None
    for s in structure.symbol_set:
        s_ids = structure.indices_from_symbol(s)
        unique = [0]
        for site_prop, vals in structure.site_properties.items():
            _unique = np.unique([vals[i] for i in s_ids])
            if len(unique) < len(_unique):
                unique = _unique
                _property = site_prop
        if _property is None:
            sites[s] = s_ids
        else:
            for i, u in enumerate(unique):
                sites[s + "_" + str(i + 1)] = []
                for j, site in zip(
                    s_ids,
                    [structure.site_properties[_property][ids] for ids in s_ids],
                ):
                    if site == u:
                        sites[s + "_" + str(i + 1)].append(j)
    return sites
