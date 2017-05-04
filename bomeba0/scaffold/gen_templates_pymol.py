"""Use PyMOl to create templates for bomeba"""

import numpy as np
np.set_printoptions(precision=3)
import __main__
__main__.pymol_argv = ['pymol','-qc'] # Pymol: quiet and no GUI
import pymol
from pymol import cmd, stored
pymol.finish_launching()



sel = 'all'

aa = ['A', 'R', 'N', 'D', 'C', 'E', 'Q', 'G', 'H', 'I', 'L', 'K', 'M',
      'F', 'P', 'S', 'T', 'W', 'Y', 'V']

for res_name in aa:
    ## Get coordinates and offset
    cmd.fab(res_name)
    cmd.alter(sel, 'resi=str(int(ID)-1)')
    xyz = cmd.get_coords(sel)
    offset = len(xyz)

    ## get atom names
    stored.atom_names = []
    cmd.iterate(sel, 'stored.atom_names.append(name)')

    atom_names = []
    for n in stored.atom_names:
        if 'H' in n and n[0] in ['1', '2', '3']:
            if len(n) == 3:
                n = n[1:] + n[0]
            elif len(n) == 4:
                n = n[1:-1] + n[0] + n[-1]
            atom_names.append(n)
        else:
            atom_names.append(n)

    ## get bonds
    stored.bonds = []
    model = cmd.get_model('all')
    for at in model.atom:
        cmd.iterate('neighbor ID %s' % at.id, 
                        'stored.bonds.append((%s, ID))' % at.id)
    bonds = list(set([tuple(sorted(i)) for i in stored.bonds]))
    bonds.sort()
    
    ## small check before returning the results
    if len(atom_names) == offset:
    
        res = """{}_info = AA_info(coords=np.{},
             atom_names = {},
             bonds = {},
             offset = {})\n""".format(res_name, repr(xyz), atom_names, bonds, offset)
         
        print(res)
        print('GLY needs manual tweaking with the hydrogen names\nthis script has not been fully tested!!!')
    else:
        print('Something funny is going on here!')
    cmd.delete('all')