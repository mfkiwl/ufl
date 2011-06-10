"The Form class."

# Copyright (C) 2008-2011 Martin Sandve Alnes
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
#
# Modified by Anders Logg, 2009-2011.
#
# First added:  2008-03-14
# Last changed: 2009-12-08

from ufl.log import error
from ufl.assertions import ufl_assert
from ufl.constantvalue import as_ufl, is_python_scalar
from ufl.sorting import cmp_expr
from ufl.integral import Integral, Measure

# --- The Form class, representing a complete variational form or functional ---

class Form(object):
    """Description of a weak form consisting of a sum of integrals over subdomains."""
    __slots__ = ("_integrals",
                 "_repr", "_hash", "_str", "_form_data", "_is_preprocessed",
                 "cell_domains", "exterior_facet_domains", "interior_facet_domains")

    # Note: cell_domains, exterior_facet_domains and interior_facet_domains
    # are used by DOLFIN to pass data to the assembler. They can otherwise
    # safely be ignored.

    def __init__(self, integrals):
        self._integrals = tuple(integrals)
        ufl_assert(all(isinstance(itg, Integral) for itg in integrals), "Expecting list of integrals.")
        self._str = None
        self._repr = None
        self._hash = None
        self._form_data = None
        self._is_preprocessed = False

        # TODO: Can we attach non-ufl payloads in a more generic fashion?
        # This seems prone to change with dolfin versions.
        self.cell_domains = None
        self.exterior_facet_domains = None
        self.interior_facet_domains = None

    def cell(self):
        c = None
        for itg in self._integrals:
            d = itg.integrand().cell()
            if d is not None:
                c = d # Best we found so far
                if not d.is_undefined():
                    # Use the first fully defined cell we find
                    break
        return c

    def integral_groups(self):
        """Return a dict, which is a mapping from domains to integrals.

        In particular, each key of the dict is a distinct tuple
        (domain_type, domain_id), and each value is a list of
        Integral instances. The Integrals in each list share the
        same domain (the key), but have different measures."""
        d = {}
        for itg in self.integrals():
            m = itg.measure()
            k = (m.domain_type(), m.domain_id())
            l = d.get(k)
            if not l:
                l = []
                d[k] = l
            l.append(itg)
        return d

    def integrals(self, domain_type = None):
        if domain_type is None:
            return self._integrals
        return tuple(itg for itg in self._integrals if itg.measure().domain_type() == domain_type)

    def measures(self, domain_type = None):
        return tuple(itg.measure() for itg in self.integrals(domain_type))

    def domains(self, domain_type = None):
        return tuple((m.domain_type(), m.domain_id()) for m in self.measures(domain_type))

    def cell_integrals(self):
        from ufl.integral import Measure
        return self.integrals(Measure.CELL)

    def exterior_facet_integrals(self):
        from ufl.integral import Measure
        return self.integrals(Measure.EXTERIOR_FACET)

    def interior_facet_integrals(self):
        from ufl.integral import Measure
        return self.integrals(Measure.INTERIOR_FACET)

    def macro_cell_integrals(self):
        from ufl.integral import Measure
        return self.integrals(Measure.MACRO_CELL)

    def surface_integrals(self):
        from ufl.integral import Measure
        return self.integrals(Measure.SURFACE)

    def form_data(self):
        "Return form metadata (None if form has not been preprocessed)"
        return self._form_data

    def compute_form_data(self,
                          object_names=None,
                          common_cell=None,
                          element_mapping=None):
        "Compute and return form metadata"
        if self._form_data is None:
            from ufl.algorithms.preprocess import preprocess
            self._form_data = preprocess(self,
                                         object_names=object_names,
                                         common_cell=common_cell,
                                         element_mapping=element_mapping)
        return self.form_data()

    def is_preprocessed(self):
        "Check whether form is preprocessed"
        return self._is_preprocessed

    def __add__(self, other):
        # --- Add integrands of integrals with the same measure

        # Start with integrals in self
        newintegrals = list(self._integrals)

        # Build mapping: (measure -> self._integrals index)
        measure2idx = {}
        for i, itg in enumerate(newintegrals):
            ufl_assert(itg.measure() not in measure2idx, "Form invariant breached.")
            measure2idx[itg.measure()] = i

        for itg in other._integrals:
            idx = measure2idx.get(itg.measure())
            if idx is None:
                # Append integral with new measure to list
                idx = len(newintegrals)
                measure2idx[itg.measure()] = idx
                newintegrals.append(itg)
            else:
                # Accumulate integrands with same measure
                a = newintegrals[idx].integrand()
                b = itg.integrand()
                # Invariant ordering of terms (shouldn't Sum fix this?)
                #if cmp_expr(a, b) > 0:
                #    a, b = b, a
                newintegrals[idx] = itg.reconstruct(a + b)

        return Form(newintegrals)

    def __sub__(self, other):
        return self + (-other)

    def __neg__(self):
        # This enables the handy "-form" syntax for e.g. the linearized system (J, -F) from a nonlinear form F
        return Form([-itg for itg in self._integrals])

    def __rmul__(self, scalar):
        # This enables the handy "0*form" syntax
        ufl_assert(is_python_scalar(scalar), "Only multiplication by scalar literals currently supported.")
        return Form([scalar*itg for itg in self._integrals])

    def __mul__(self, coefficient):
        "The action of this form on the given coefficient."
        from ufl.formoperators import action
        return action(self, coefficient)

    def __str__(self):
        if self._str is None:
            if self._integrals:
                self._str = "\n  +  ".join(str(itg) for itg in self._integrals)
            else:
                self._str = "<empty Form>"
        return self._str

    def __repr__(self):
        if self._repr is None:
            self._repr = "Form([%s])" % ", ".join(repr(itg) for itg in self._integrals)
        return self._repr

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(tuple(type(itg) for itg in self._integrals))
            # TODO: This is probably better, using a couple of levels of types from the integrands:
            #self._hash = hash(tuple((compute_hash(itg.integrand()), itg.measure()) for itg in self._integrals))
            # TODO: This is probably best, is it that slow? Don't remember why it was disabled...
            #self._hash = hash(repr(self))
        return self._hash

    def __eq__(self, other):
        if not isinstance(other, Form):
            return False
        return repr(self) == repr(other)

    def signature(self):
        return repr(self)
