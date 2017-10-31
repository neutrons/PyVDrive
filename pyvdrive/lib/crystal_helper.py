__author__ = 'wzz'

import mantid
import mantid.geometry


class UnitCell(object):
    """ A simple class to pass the unit cell information
    """
    PRIMITIVE = 0
    BCC = 1
    FCC = 2
    BC = 3   # body-centre
    FC = 4   # face-centre
    HCP = 5  # HCP

    SpaceGroupDict = {
        PRIMITIVE: 'P m m m',
        BC: 'I m m m',
        FC: 'F m m m',
        HCP: 'P 63/m m c',
        BCC: 'I m -3 m',
        FCC: 'F d -3 m',
    }

    def __init__(self, unit_cell_type, a, b=None, c=None):
        """
        Initialize and set up a unit cell
        :param unit_cell_type:
        :param a:
        :param b:
        :param c:
        :return:
        """
        # unit cell type, primitive, bcc or fcc
        assert 0 <= unit_cell_type <= 4, 'Unit cell type %d is not supported.' % unit_cell_type
        self._unitCellType = unit_cell_type

        # lattice size
        assert isinstance(a, float)
        assert a > 0, 'Lattice parameter must larger than 0.'
        self._a = a

        assert (b is None and c is None) or (b is not None and c is not None)
        if b is None and c is None:
            # cubic
            self._isCubic = True
            self._b = self._a
            self._c = self._a
        else:
            # tetrehedron
            self._isCubic = False
            assert isinstance(b, float)
            assert b > 0
            self._b = b
            assert isinstance(c, float)
            assert c > 0
            self._c = c

        return

    @property
    def space_group(self):
        """ Get space group
        :return:
        """
        return UnitCell.SpaceGroupDict[self._unitCellType]

    def get_cell_parameters(self):
        """
        Put cell parameters a, b and c to a list and return
        :return: list of 3 elements, a, b and c
        """
        return [self._a, self._b, self._c]

    def is_cubic(self):
        """ Whether it is cubic
        :return:
        """
        return self._isCubic


def calculate_reflections(unit_cell, min_d, max_d):
    """ Calculate reflections' position in d-spacing
    Purpose:
        Calculate a crystal's Bragg peaks' positions in d-spacing
    Requirements:
        Crystal unit cell must be tetrahegonal (including cubic)
        Lattice parameters (a, b, c) must be valid
        d-spacing range must be given
        Structure must be primitive, body-centre, or face-centre
    Guarantees:
        Bragg peaks' position along with HKL will be returned
    :param unit_cell: UnitCell instance
    :param min_d: minimum d-spacing value
    :param max_d: maximum d-spacing value
    :return: a list of reflections.  Each reflection is a 2-tuple as ... ...
    """
    from mantid.geometry import CrystalStructure, ReflectionGenerator, ReflectionConditionFilter

    def get_generator(lattice_parameters, space_group):
        """
        """
        crystal_structure = CrystalStructure(' '.join([str(x) for x in lattice_parameters]), space_group, '')
        generator = ReflectionGenerator(crystal_structure, ReflectionConditionFilter.Centering)
        return generator

    def get_unique_reflections(lattice_parameters, space_group, d_min, d_max):
        """
        """
        generator = get_generator(lattice_parameters, space_group)

        hkls = generator.getUniqueHKLs(d_min, d_max)

        dvalues = generator.getDValues(hkls)

        return zip(hkls, dvalues)

    def get_all_reflections(lattice_parameters, space_group, d_min, d_max):
        """
        """
        generator = get_generator(lattice_parameters, space_group)

        hkls = generator.getHKLs(d_min, d_max)

        dvalues = generator.getDValues(hkls)

        return zip(hkls, dvalues)

    # Check inputs
    assert isinstance(unit_cell, UnitCell), 'Input must be an instance of UnitCell but not %s.' % str(type(unit_cell))
    assert min_d < max_d, 'Minimum d-spacing %f must be smaller than maximum d-spacing %f.' % (min_d, max_d)
    assert 0. <= min_d, 'Minimum d-spacing %f must be larger or equal to 0.' % min_d

    # cell_parameters = [5, 4, 3]
    cell_parameters = unit_cell.get_cell_parameters()
    cell_type = unit_cell.space_group

    reflection_list = get_unique_reflections(cell_parameters, cell_type, min_d, max_d)

    """
    print get_unique_reflections(cell_parameters, 'P m m m', 0.5, 5.0)  # primitive
    print get_unique_reflections(cell_parameters, 'I m m m', 0.5, 5.0)  # body center
    print get_unique_reflections(cell_parameters, 'F m m m', 0.5, 5.0)  # face center
    print get_all_reflections(cell_parameters, 'F m m m', 0.5, 5.0)
    """

    return reflection_list

