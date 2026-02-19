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

(1, "Sets",
"""This chapter introduces the concept of sets, their representation in roster and set-builder form, 
types of sets such as empty, finite and infinite sets, subsets, universal set, Venn diagrams, 
operations on sets including union, intersection and difference, and complement of a set. 
It forms the foundation for relations, functions and advanced mathematical reasoning."""),

(2, "Relations and Functions",
"""This chapter explains ordered pairs, Cartesian products of sets, and relations between sets. 
It introduces different types of relations and functions, domain and range, and builds the basic 
framework required for understanding algebra and calculus."""),

(3, "Trigonometric Functions",
"""This chapter introduces angles and trigonometric functions, their definitions, identities, 
and properties. It covers trigonometric functions of sum and difference of two angles and establishes 
the foundation for solving trigonometric equations and advanced applications."""),

(4, "Complex Numbers and Quadratic Equations",
"""This chapter introduces complex numbers, algebra of complex numbers, modulus and conjugate, 
Argand plane representation, and polar form. It also explains solutions of quadratic equations, 
especially when roots are not real, extending number system beyond real numbers."""),

(5, "Linear Inequalities",
"""This chapter discusses inequalities, algebraic solutions of linear inequalities in one variable, 
and graphical representation on number line. It develops understanding of solution sets and 
interval notation for inequality-based problems."""),

(6, "Permutations and Combinations",
"""This chapter introduces the fundamental principle of counting, permutations, and combinations. 
It explains arrangement and selection techniques used in probability, statistics, and combinatorics."""),

(7, "Binomial Theorem",
"""This chapter explains the binomial theorem for positive integral indices, binomial expansion, 
general term, and properties of binomial coefficients. It is useful in algebraic expansion and 
probability calculations."""),

(8, "Sequences and Series",
"""This chapter introduces sequences and series, arithmetic progression (A.P.), geometric progression (G.P.), 
sum of terms, and relationship between arithmetic mean and geometric mean. It forms the basis for 
advanced mathematical series and financial mathematics."""),

(9, "Straight Lines",
"""This chapter discusses coordinate geometry of straight lines including slope, different forms 
of equation of a line, angle between lines, and distance of a point from a line. It builds analytical 
geometry concepts used in higher mathematics."""),

(10, "Conic Sections",
"""This chapter introduces conic sections with focus on parabola and its properties. 
It explains geometric definition, equations, and applications of conic curves in coordinate geometry."""),

(11, "Introduction to Three Dimensional Geometry",
"""This chapter introduces three-dimensional coordinate geometry including coordinate axes, 
planes, coordinates of a point in space, and distance between two points in space. 
It extends two-dimensional geometry into three dimensions."""),

(12, "Limits and Derivatives",
"""This chapter introduces the concept of limits and intuitive idea of derivatives. 
It covers limits of trigonometric functions, basic limit laws, and definition of derivative 
as rate of change, forming the foundation of calculus."""),

(13, "Statistics",
"""This chapter explains collection and presentation of data and measures of dispersion 
such as range, variance, and standard deviation. It provides tools for analyzing and 
interpreting statistical data mathematically."""),

(14, "Probability",
"""This chapter introduces the concept of events and probability using the axiomatic approach. 
It explains probability rules, outcomes, and basic probability calculations, forming 
the foundation for advanced probability theory.""")

]

cursor.executemany("INSERT OR REPLACE INTO summaries VALUES (?, ?, ?)", data)

conn.commit()
conn.close()

print("Math summaries inserted successfully.")
