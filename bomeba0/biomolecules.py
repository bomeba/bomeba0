import numpy as np
from .residues import aa_templates, one_to_three
from .utils import mod, perp_vector, get_angle, get_torsional
from .geometry import rotation_matrix_3d, set_torsional
from .constants import constants
from .ff import compute_neighbors, LJ

class TestTube():
    """
    This is a "container" class instanciated only once (Singleton)
    """
    _instance = None
    def __new__(cls, solvent=None, temperature=298, force_field='simple_lj',
    *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TestTube, cls).__new__(
                                cls, *args, **kwargs)
            cls.solvent = solvent
            cls.temperature = temperature
            cls.force_field = force_field
            cls.molecules = []
        return cls._instance

    def energy(self):
        """
        Compute the energy of the system.
        ToDo: It should be possible to compute partial energy,
        like without solvent or excluding molecules.
        At the moment this method lives in Protein class
        """
        pass

    def add(self, name):
        """
        add molecules to TestTube
        """
        molecules = self.molecules
        if name in molecules:
            print('We already have a copy of {:s} in the test tube!'.format(name))
        else:
            molecules.append(name)
    
    def remove(self, name):
        """
        remove molecules from TestTube
        """
        molecules = self.molecules
        if name in molecules:
            molecules.remove(name)


class Protein:
    '''write me'''
    def __init__(self, sequence):
        '''Initialize a new protein from a sequence of amino acids'''
        self.sequence = sequence
        self.coords, self._names, self._elements, self._offsets, self._exclusions = _prot_builder(sequence)
        # add instance of Protein to TestTube automatically

    def __len__(self):
        return len(self.sequence)
        
    def at_coords(self, resnum, at_name=None):
        """
        Returns the coordinate of an specified residue and atom (optionally)

        Parameters
        ----------
        resnum : int
            residue number from which to obtain the coordinates
        sele : string or None
            atom name from which to obtain the coordinates. If none is provided
            it will return the coordinates of the whole residue (default).

        Returns
        ----------
        coords: array
            Cartesian coordinates of a given residue or from an atom in the
            given residue.
        """
        offset_0, offset_1 = self._offsets[resnum:resnum+2]
        if sele is None:
            return self.coords[offset_0 : offset_1]

	elif sele == 'sc':#sidechain_
	    at_idx = self._names[offset_0+4 :offset_1].index(sele)
            return self.coords[offset_0 + 4+ at_idx]
		
	elif sele == 'bb':#backbone_
	    at_idx = self._names[offset_0:offset_0+4].index(sele)
            return self.coords[offset_0 + 4+ at_idx]
	
        else:
            at_idx = self._names[offset_0:offset_1].index(sele)
            return self.coords[offset_0 + at_idx]
        
    def energy(self, cut_off=6):
        """
        Write ME!
        """
        coords = self.coords
        neighbors = compute_neighbors(coords, self._exclusions, cut_off)
        energy = LJ(neighbors, coords, self._elements)
        return energy

    def get_phi(self, resnum):
        """
        Compute phi torsional angle

        Parameters
        ----------
        resnum : int
            residue number from which to compute torsional
        """
        # C(i-1),N(i),Ca(i),C(i)
        if resnum != 0:
            coords = self.coords
            prev = self._offsets[resnum - 1]
            this = self._offsets[resnum]

            a = coords[prev + 2]
            b = coords[this]
            c = coords[this + 1]
            d = coords[this + 2]
            return get_torsional(a, b, c, d) * constants.radians_to_degrees
        else:
            return np.nan

    def get_psi(self, resnum):
        """
        Compute psi torsional angle

        Parameters
        ----------
        resnum : int
            residue number from which to compute torsional
        """
        # N(i),Ca(i),C(i),N(i+1)
        if resnum + 1 < len(self):
            coords = self.coords
            next = self._offsets[resnum + 1]
            this = self._offsets[resnum]
            a = coords[this]
            b = coords[this + 1]
            c = coords[this + 2]
            d = coords[next]
            return get_torsional(a, b, c, d) * constants.radians_to_degrees
        else:
            return np.nan

    def get_chi(self, resnum, chi_num):
        """
        Compute chi torsional angle

        Parameters
        ----------
        resnum : int
            residue number from which to compute torsional
        chi_num : int
            number of chi, some residues have more than one chi torsional:
        """
        return np.nan

    def get_torsionals(self, sidechain=True):
        """
        Compute all phi, psi and chi torsional angles of a given molecule

        Parameters
        ----------
        sidechain : Boolean
            Wheter to compute all torsional angles including the chi angles or
            only backbone ones. The default (True) is to include the sidechain.

        Returns
        ----------
        DataFrame with the type of torsional angles as colums: # ToDo
        
        """
        for i in range(len(self)):
            tors = []
            tors.append(self.get_phi(i))
            tors.append(self.get_psi(i))
            if sidechain:
                for j in range(2):
                    tors.append(self.get_chi(i, j))
                print(('{:8.2f}' * 4).format(*tors))
            else:
                print(('{:8.2f}' * 2).format(*tors))


    def set_phi(self, resnum, theta):
        """
        set the phi torsional angle to the value theta

        Parameters
        ----------
        resnum : int
            residue number from which to compute torsional
        theta : float
            value of the angle to set in degrees
        """
        # C(i-1),N(i),Ca(i),C(i)
        if resnum != 0:
            theta_rad = (self.get_phi(resnum) - theta) * constants.degrees_to_radians
            xyz = self.coords
            i = self._offsets[resnum]
            j = i + 1
            # the hydrogen attached to N(i) was unnecessarily rotated, so we
            # need to fix it
            resname = self.sequence[resnum]
            H = aa_templates[resname].atom_names.index('H')
            idx_to_fix = (H, H+1)
            set_torsional(xyz, i, j, theta_rad, idx_to_fix)

    def set_psi(self, resnum, theta):
        """
        set the psi torsional angle to the value theta

        Parameters
        ----------
        resnum : int
            residue number from which to compute torsional
        theta : float
            value of the angle to set in degrees
        """
        # N(i),Ca(i),C(i),N(i+1)
        if resnum + 1 < len(self):
            theta_rad = (self.get_psi(resnum) - theta) * constants.degrees_to_radians
            xyz = self.coords
            i = self._offsets[resnum] + 1
            j = i + 1
            # We have made a rotation starting from the next residue and we
            # left C and O atoms unrotated, now we fix this
            resname = self.sequence[resnum]
            idx_to_fix = (3, aa_templates[resname].offset - 1)
            set_torsional(xyz, i, j, theta_rad, idx_to_fix)

    def dump_pdb(self, filename, b_factor=None):
        """
        Write a protein to a pdb file

        Parameters
        ----------
        filename : string
            name of the file without the pdb extension
        b_factor : list optional
            list of values to fill the b-factor column. one value per atom
        """
        coords = self.coords
        names = self._names
        elements = self._elements
        sequence = self.sequence
        
        if b_factor is None:
            b_factor = [1.] * len(coords)

        rep_seq_nam = []
        rep_seq = []
        for idx, aa in enumerate(sequence):
            lenght = aa_templates[aa].offset
            seq_nam = aa * lenght
            res = [str(idx + 1)] * lenght
            rep_seq_nam.extend(seq_nam)
            rep_seq.extend(res)

        fd = open('{}.pdb'.format(filename), 'w')
        for i in range(len(coords)):
            serial = str(i + 1)
            name = names[i]
            resname = one_to_three[rep_seq_nam[i]]
            resseq = rep_seq[i]
            line = "ATOM {:>6s}{:>4s} {:>4s} {:>5s}    {:8.3f}{:8.3f}{:8.3f}  1.00 {:5.2f}           {:2s}  \n".format(serial, name, resname, resseq, *coords[i], b_factor[i], elements[i])
            fd.write(line)
        fd.close()


def _prot_builder(sequence):
    """
    Build a protein from a template.
    Adapted from fragbuilder
    """
    names = []
    bonds_mol = []
    pept_coords, pept_at, bonds, offset = aa_templates[sequence[0]]
    names.extend(pept_at)
    bonds_mol.extend(bonds)
    offsets = [0, offset]
    for idx, aa in enumerate(sequence[1:]):
        tmp_coords, tmp_at, bonds, offset = aa_templates[aa]
        
        v3 = pept_coords[2 + offsets[idx]]  # C
        v2 = pept_coords[1 + offsets[idx]]  # CA
        v1 = pept_coords[0 + offsets[idx]]  # N
        
        connectionpoint = v3 + (v2 - v1) / mod(v2 - v1) * constants.peptide_bond_lenght
        connectionvector = tmp_coords[0] - connectionpoint

        # translate
        tmp_coords = tmp_coords - connectionvector
        
        # first rotation
        v4 = v3 - v2 + connectionpoint
        axis1 = perp_vector(tmp_coords[1], connectionpoint, v4)
        angle1 =  get_angle(tmp_coords[1], connectionpoint, v4)
        center1 = connectionpoint

        ba =  axis1 - center1
        tmp_coords = tmp_coords - center1
        tmp_coords = tmp_coords @ rotation_matrix_3d(ba, angle1)
        tmp_coords = tmp_coords + center1

        axis2 = tmp_coords[1] - connectionpoint
        axis2 = axis2 / mod(axis2) + connectionpoint
        d3 = tmp_coords[1]
        d4 = tmp_coords[2]
        angle2 = constants.pi + get_torsional(v3, connectionpoint, d3, d4) # si res_next Pro sumar 90 grados
        center2 = connectionpoint
        ba =  axis2 - center2
        tmp_coords = tmp_coords - center2
        tmp_coords = tmp_coords @ rotation_matrix_3d(ba, angle2)
        tmp_coords = tmp_coords + center2
        
        names.extend(tmp_at)
        offsets.append(offsets[idx+1] + offset)
        pept_coords = np.concatenate([pept_coords, tmp_coords])

        # create a list of bonds from the template-bonds by adding the offset
        prev_offset = offsets[-3]
        last_offset = offsets[-2]
        bonds_mol.extend([(i + last_offset, j + last_offset) for i, j in bonds] + [(2 + prev_offset, last_offset)])

    offsets.append(offsets[-1] + offset)
    exclusions = _exclusiones_1_3(bonds_mol)
    
    # generate a list with the names of chemical elements
    elements = []
    for i in names:
        element = i[0]
        if element in ['1', '2', '3']:
            element = i[1]
        elements.append(element)
    
    return pept_coords, names, elements, offsets, exclusions
    
    
def _exclusiones_1_3(bonds_mol):
    # based on the information inside bonds_mol determine the 1-3 exclusions
    # ToDo: write a not-naive version of this
    angles_mol = []
    for idx, i in enumerate(bonds_mol):
        a, b = i
        for j in bonds_mol[idx+1:]:
            c, d = j
            if (a == c and b != d):
                angles_mol.append((b, d))
            elif (a == d and b != c):
                angles_mol.append((b, c))
            elif b == c and d != a:
                angles_mol.append((a, d))
            elif b == d and c != a:
                angles_mol.append((a, c))

    exclusions = bonds_mol + angles_mol
    return set([tuple(sorted(i)) for i in exclusions])
