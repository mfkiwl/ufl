from ufl import *
#
# Author: Martin Sandve Alnes
# Date: 2008-10-30
#

element = FiniteElement("Lagrange", triangle, 1)

w = Function(element)

# H1 semi-norm
f = inner(grad(w), grad(w))/2*dx
# grad(w) : grad(v)
b = derivative(f, w)
# stiffness matrix, grad(u) : grad(v)
a = derivative(b, w)

# adjoint, grad(v) : grad(u)
astar = adjoint(a)
# action of adjoint, grad(v) : grad(w)
astaraction = action(astar)

