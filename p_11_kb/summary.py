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

(1, "Units and Measurements",
"""This chapter introduces the International System of Units (SI), significant figures, 
rounding rules, uncertainty in measurements, dimensions of physical quantities, dimensional formulae, 
and dimensional analysis. It provides tools for checking correctness and consistency of physical equations."""),

(2, "Motion in a Straight Line",
"""This chapter explains concepts of displacement, velocity, acceleration, and instantaneous velocity. 
It derives kinematic equations for uniformly accelerated motion and develops graphical understanding of motion."""),

(3, "Motion in a Plane",
"""This chapter introduces scalars and vectors, vector addition and subtraction (graphical and analytical methods), 
resolution of vectors, projectile motion, uniform circular motion, and motion in two dimensions."""),

(4, "Laws of Motion",
"""This chapter discusses Newton’s laws of motion, inertia, conservation of momentum, equilibrium of a particle, 
friction, circular motion, and application of force concepts to solve mechanical problems."""),

(5, "Work, Energy and Power",
"""This chapter explains work, kinetic energy, work-energy theorem, potential energy, conservation of mechanical energy, 
power, spring potential energy, and collisions (elastic and inelastic) in one and two dimensions."""),

(6, "System of Particles and Rotational Motion",
"""This chapter introduces centre of mass, motion of a system of particles, torque, angular momentum, moment of inertia, 
rotational kinematics and dynamics, equilibrium of rigid bodies, and conservation of angular momentum."""),

(7, "Gravitation",
"""This chapter explains universal law of gravitation, Kepler’s laws, gravitational constant, acceleration due to gravity, 
variation of g with height and depth, gravitational potential energy, escape velocity, satellites, and orbital energy."""),

(8, "Mechanical Properties of Solids",
"""This chapter discusses stress, strain, Hooke’s law, stress-strain curve, elastic moduli (Young’s, shear, bulk), 
Poisson’s ratio, elastic potential energy, and applications of elasticity in engineering."""),

(9, "Mechanical Properties of Fluids",
"""This chapter explains pressure in fluids, Pascal’s law, variation of pressure with depth, hydraulic machines, 
streamline flow, Bernoulli’s principle, viscosity (Stokes’ law), surface tension, capillarity, and related phenomena."""),

(10, "Thermal Properties of Matter",
"""This chapter introduces temperature, heat, measurement scales, ideal gas equation, thermal expansion, specific heat capacity, 
calorimetry, change of state and latent heat, heat transfer (conduction, convection, radiation), blackbody radiation, 
and Newton’s law of cooling."""),

(11, "Thermodynamics",
"""This chapter explains thermal equilibrium, zeroth law, first and second laws of thermodynamics, 
thermodynamic state variables, thermodynamic processes (isothermal, adiabatic, isobaric, isochoric), 
Carnot engine, and reversible and irreversible processes."""),

(12, "Kinetic Theory",
"""This chapter develops molecular nature of matter, kinetic theory of gases, pressure of ideal gas, 
kinetic interpretation of temperature, law of equipartition of energy, specific heat capacities of gases and solids, 
and mean free path."""),

(13, "Oscillations",
"""This chapter explains periodic and oscillatory motion, simple harmonic motion (SHM), 
relation between SHM and uniform circular motion, velocity and acceleration in SHM, 
force law, and energy in oscillations."""),

(14, "Waves",
"""This chapter introduces transverse and longitudinal waves, wave motion, displacement relation in progressive waves, 
wave speed, principle of superposition, reflection of waves, beats, and properties of sound waves.""")

]

cursor.executemany("INSERT OR REPLACE INTO summaries VALUES (?, ?, ?)", data)

conn.commit()
conn.close()

print("Physics summaries inserted successfully.")
