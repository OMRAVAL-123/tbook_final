import sqlite3

conn = sqlite3.connect("summaries.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS summaries (
    chapter_no INTEGER PRIMARY KEY,
    chapter_title TEXT,
    summary TEXT
)
""")

data = [

(1, "Relations and Functions",
"""This chapter discusses types of relations and functions, including reflexive, symmetric, 
transitive relations and one-one, onto functions. It explains composition of functions, 
invertible functions, and establishes foundational concepts required for higher algebra and calculus."""),

(2, "Inverse Trigonometric Functions",
"""This chapter introduces inverse trigonometric functions, their domains and ranges, 
principal values, identities, and properties. It builds understanding of solving 
trigonometric equations and calculus applications."""),

(3, "Matrices",
"""This chapter explains matrices, their order, types, equality, and operations such as 
addition, scalar multiplication, and matrix multiplication. It covers transpose, symmetric 
and skew-symmetric matrices, and invertible matrices, forming the basis for linear algebra."""),

(4, "Determinants",
"""This chapter introduces determinants of different orders and their properties. 
It explains minors, cofactors, adjoint, inverse of a matrix, area of a triangle using determinants, 
and application of matrices and determinants in solving systems of linear equations."""),

(5, "Continuity and Differentiability",
"""This chapter develops the concepts of continuity and differentiability of functions. 
It includes derivatives of composite, implicit, inverse trigonometric, exponential, and logarithmic functions, 
logarithmic differentiation, parametric forms, and second order derivatives, forming the core of calculus."""),

(6, "Application of Derivatives",
"""This chapter applies derivatives to study rate of change, increasing and decreasing functions, 
and determination of maxima and minima. It focuses on real-life optimization problems and graphical behavior of functions."""),

(7, "Integrals",
"""This chapter introduces integration as the inverse process of differentiation. 
It covers methods of integration such as substitution, partial fractions, and integration by parts, 
definite integrals, fundamental theorem of calculus, and properties and evaluation of definite integrals."""),

(8, "Application of Integrals",
"""This chapter applies definite integrals to find area under curves and between curves. 
It demonstrates geometric interpretation and practical applications of integration."""),

(9, "Differential Equations",
"""This chapter introduces differential equations, their order and degree, general and particular solutions, 
and methods of solving first order differential equations including separable, homogeneous, and linear equations."""),

(10, "Vector Algebra",
"""This chapter explains basic concepts of vectors, types of vectors, vector addition, scalar multiplication, 
dot product and cross product. It includes projection of vectors, section formula, and applications in geometry and physics."""),

(11, "Three Dimensional Geometry",
"""This chapter extends coordinate geometry to three dimensions. 
It covers direction ratios and cosines, equations of lines in space, angle between lines, 
and shortest distance between two lines including skew and parallel lines."""),

(12, "Linear Programming",
"""This chapter introduces linear programming problems, mathematical formulation, 
constraints, objective functions, and graphical method of solving optimization problems."""),

(13, "Probability",
"""This chapter develops advanced probability concepts including conditional probability, 
multiplication theorem, independent events, Bayes’ theorem, total probability theorem, 
and partition of sample space, forming the basis of statistical reasoning.""")

]

cursor.executemany("INSERT OR REPLACE INTO summaries VALUES (?, ?, ?)", data)

conn.commit()
conn.close()

print("Class 12 Maths summaries inserted successfully.")
