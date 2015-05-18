from six.moves import zip
from numpy import (array, zeros, arange, searchsorted,
    unique)

from pyNastran.bdf.dev_vectorized.cards.elements.shell.shell_element import ShellElement

from pyNastran.bdf.field_writer_8 import print_card_8
from pyNastran.bdf.bdfInterface.assign_type import (integer, integer_or_blank,
    double_or_blank)
from pyNastran.bdf.dev_vectorized.cards.elements.shell.cquad4 import _cquad4_normal_A


class CQUAD8(ShellElement):
    type = 'CQUAD8'
    def __init__(self, model):
        ShellElement.__init__(self, model)

    def allocate(self, ncards):
        self.n = ncards
        float_fmt = self.model.float
        #: Element ID
        self.element_id = zeros(ncards, 'int32')
        #: Property ID
        self.property_id = zeros(ncards, 'int32')
        #: Node IDs
        self.node_ids = zeros((ncards, 4), 'int32')

        self.zoffset = zeros(ncards, 'int32')
        self.t_flag = zeros(ncards, 'int32')
        self.thickness = zeros((ncards, 8), float_fmt)

    def add(self, card, comment=''):
        i = self.i
        self.element_id[i] = integer(card, 1, 'element_id')

        self.property_id[i] = integer(card, 2, 'property_id')

        self.node_ids[i, :] = [
            integer(card, 3, 'n1'),
            integer(card, 4, 'n2'),
            integer(card, 5, 'n3'),
            integer(card, 6, 'n4'),
            integer_or_blank(card, 7, 'n5', 0),
            integer_or_blank(card, 8, 'n6', 0),
            integer_or_blank(card, 9, 'n7', 0),
            integer_or_blank(card, 10, 'n8', 0)]

        self.thickness[i, :] = [
            double_or_blank(card, 11, 'T1', 1.0),
            double_or_blank(card, 12, 'T2', 1.0),
            double_or_blank(card, 13, 'T3', 1.0),
            double_or_blank(card, 14, 'T4', 1.0), ]

        #self.thetaMcid[i] = integer_double_or_blank(card, 15, 'thetaMcid', 0.0)
        self.zoffset[i] = double_or_blank(card, 16, 'zOffset', 0.0)
        self.t_flag[i] = integer_or_blank(card, 17, 'TFlag', 0)
        self.i += 1

    def build(self):
        if self.n:
            i = self.element_id.argsort()
            self.element_id = self.element_id[i]
            self.property_id = self.property_id[i]
            self.node_ids = self.node_ids[i, :]
            self.thickness = self.thickness[i, :]
            self.zoffset = self.zoffset[i]
            self.t_flag = self.t_flag[i]
            assert self.node_ids.min() > 0
            self._cards = []
            self._comments = []
        else:
            self.element_id = array([], 'int32')
            self.property_id = array([], dtype='int32')

    #=========================================================================
    def _node_locations(self, xyz_cid0, i=None):
        if xyz_cid0 is None:
            xyz_cid0 = self.model.grid.get_position_by_node_index()
        if i is None:
            n1 = xyz_cid0[self.model.grid.get_node_index_by_node_id(self.node_ids[:, 0]), :]
            n2 = xyz_cid0[self.model.grid.get_node_index_by_node_id(self.node_ids[:, 1]), :]
            n3 = xyz_cid0[self.model.grid.get_node_index_by_node_id(self.node_ids[:, 2]), :]
            n4 = xyz_cid0[self.model.grid.get_node_index_by_node_id(self.node_ids[:, 3]), :]
        else:
            n1 = xyz_cid0[self.model.grid.get_node_index_by_node_id(self.node_ids[i, 0]), :]
            n2 = xyz_cid0[self.model.grid.get_node_index_by_node_id(self.node_ids[i, 1]), :]
            n3 = xyz_cid0[self.model.grid.get_node_index_by_node_id(self.node_ids[i, 2]), :]
            n4 = xyz_cid0[self.model.grid.get_node_index_by_node_id(self.node_ids[i, 3]), :]
        return n1, n2, n3, n4

    def _mass_area_normal(self, element_id=None, node_ids=None, xyz_cid0=None,
                          calculate_mass=True, calculate_area=True,
                          calculate_normal=True):
        """
        Gets the mass, area, and normals of the CQUAD4s on a per
        element basis.

        :param self: the CQUAD4 object
        :param element_id: the elements to consider (default=None -> all)

        :param xyz_cid0: the GRIDs as an (N, 3) NDARRAY in CORD2R=0 (or None)

        :param calculate_mass: should the mass be calculated (default=True)
        :param calculate_area: should the area be calculated (default=True)
        :param calculate_normal: should the normals be calculated (default=True)

        .. note:: If node_ids is None, the positions of all the GRID cards
                  must be calculated
        """
        if element_id is None:
            element_id = self.element_id
            property_id = self.property_id
            i = None
        else:
            i = searchsorted(self.element_id, element_id)
            property_id = self.property_id[i]

        n1, n2, n3, n4 = self._node_locations(xyz_cid0, i)
        if calculate_mass:
            calculate_area = True
        normal, A = _cquad4_normal_A(n1, n2, n3, n4, calculate_area=calculate_area, normalize=True)

        massi = None
        if calculate_mass:
            mpa = self.model.properties_shell.get_mass_per_area(property_id)
            assert mpa is not None
            massi = mpa * A
        return massi, A, normal

    def get_centroid_by_element_id(self, element_id=None, node_ids=None, xyz_cid0=None):
        if element_id is None:
            element_id = self.element_id
            i = None
        else:
            i = searchsorted(self.element_id, element_id)
        n1, n2, n3, n4 = self._node_locations(xyz_cid0, i)
        return (n1 + n2 + n3 + n4) / 4.

    #=========================================================================
    def write_card(self, f, size=8, element_id=None):
        if self.n:
            if element_id is None:
                i = arange(self.n)
            else:
                assert len(unique(element_id)) == len(element_id), unique(element_id)
                i = searchsorted(self.element_id, element_id)

            for (eid, pid, n) in zip(self.element_id[i], self.property_id[i], self.node_ids[i]):
                card = ['CQUAD8', eid, pid, n[0], n[1], n[2], n[3]]
                f.write(print_card_8(card))

    def _verify(self, xref=True):
        self.get_mass_by_element_id()
        self.get_area_by_element_id()
        self.get_normal_by_element_id()

    def rebuild(self):
        raise NotImplementedError()

    def _positions(self, nids_to_get):
        """
        Gets the positions of a list of nodes

        :param nids_to_get:  the node IDs to get as an NDARRAY
        :param node_ids:     the node IDs that contains all the nids_to_get
                             as an NDARRAY
        :param grids_cid_0:  the GRIDs as an (N, )  NDARRAY

        :returns grids2_cid_0 : the corresponding positins of the requested
                                GRIDs
        """
        positions = self.model.grid.get_position_by_node_id(nids_to_get)
        #grids2_cid_0 = grids_cid0[searchsorted(node_ids, nids_to_get), :]
        #return grids2_cid_0
        return positions

    #def slice_by_index(self, i):
        #i = self._validate_slice(i)
        #obj = CQUAD8(self.model)
        #obj.n = len(i)
        ##obj._cards = self._cards[i]
        ##obj._comments = obj._comments[i]
        ##obj.comments = obj.comments[i]
        #obj.element_id = self.element_id[i]
        #obj.property_id = self.property_id[i]
        #obj.node_ids = self.node_ids[i, :]
        #obj.zoffset = self.zoffset[i]
        #obj.t_flag = self.t_flag[i]
        #obj.thickness = self.thickness[i, :]
        #return obj
