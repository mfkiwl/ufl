"""This module defines the Indexed class."""

# Copyright (C) 2008-2014 Martin Sandve Alnes
#
# This file is part of UFL.
#
# UFL is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# UFL is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with UFL. If not, see <http://www.gnu.org/licenses/>.

from six.moves import zip
from ufl.log import error
from ufl.expr import Expr
from ufl.operatorbase import WrapperType
from ufl.indexing import Index, FixedIndex, MultiIndex, as_multi_index
from ufl.indexutils import unique_indices
from ufl.precedence import parstr
from ufl.common import EmptyDict
from ufl.core.ufl_type import ufl_type

#--- Indexed expression ---

@ufl_type(is_shaping=True, num_ops=2)
class Indexed(WrapperType):
    #__slots__ = ("ufl_free_indices", "ufl_index_dimensions",) # INDEXING
    __slots__ = ("_free_indices", "_index_dimensions",)

    def __init__(self, expression, multiindex):
        # Error checking
        if not isinstance(expression, Expr):
            error("Expecting Expr instance, not %s." % repr(expression))
        if not isinstance(multiindex, MultiIndex):
            error("Expecting MultiIndex instance, not %s." % repr(multiindex))

        shape = expression.ufl_shape

        # Error checking
        if len(shape) != len(multiindex):
            error("Invalid number of indices (%d) for tensor "\
                "expression of rank %d:\n\t%r\n"\
                % (len(multiindex), expression.rank(), expression))

        # Store operands
        WrapperType.__init__(self, (expression, multiindex))

        # Error checking
        for si, di in zip(shape, multiindex):
            if isinstance(di, FixedIndex) and int(di) >= int(si):
                error("Fixed index out of range!")

        # Build free index tuple and dimensions
        idims = dict((i, s) for (i, s) in zip(multiindex._indices, shape)
                     if isinstance(i, Index))
        idims.update(expression.index_dimensions())
        fi = unique_indices(expression.free_indices() + multiindex._indices)

        # Cache free index and dimensions
        self._free_indices = fi
        self._index_dimensions = idims or EmptyDict

        # INDEXING: FIXME
        #mi = [ind.count() for ind in multiindex._indices if isinstance(ind, Index)]
        #fi = tuple(sorted(expression.ufl_free_indices + mi))
        # Cache free index and dimensions # INDEXING
        #self.ufl_free_indices = fi
        #self.ufl_index_dimensions = fid

    ufl_shape = ()

    def free_indices(self):
        return self._free_indices

    def index_dimensions(self):
        return self._index_dimensions

    def is_cellwise_constant(self):
        "Return whether this expression is spatially constant over each cell."
        return self.ufl_operands[0].is_cellwise_constant()

    def evaluate(self, x, mapping, component, index_values, derivatives=()):
        A, ii = self.ufl_operands
        component = ii.evaluate(x, mapping, None, index_values)
        if derivatives:
            return A.evaluate(x, mapping, component, index_values, derivatives)
        else:
            return A.evaluate(x, mapping, component, index_values)

    def __str__(self):
        return "%s[%s]" % (parstr(self.ufl_operands[0], self), self.ufl_operands[1])

    def __repr__(self):
        return "Indexed(%r, %r)" % self.ufl_operands

    def __getitem__(self, key):
        error("Attempting to index with %r, but object is already indexed: %r" % (key, self))
