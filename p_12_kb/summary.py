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

(1, "Electric Charges and Fields",
"""This chapter introduces electric charge, its properties, Coulomb’s law, forces between multiple charges, 
electric field and field lines, electric dipole, continuous charge distribution, electric flux, 
and Gauss’s law along with its applications for symmetric charge distributions."""),

(2, "Electrostatic Potential and Capacitance",
"""This chapter explains electrostatic potential, potential due to point charges and dipoles, 
equipotential surfaces, relation between electric field and potential, potential energy of charge systems, 
electrostatics of conductors, dielectric properties, capacitance, parallel plate capacitors, 
combination of capacitors, and energy stored in capacitors."""),

(3, "Current Electricity",
"""This chapter introduces electric current, drift velocity, mobility, Ohm’s law and its limitations, 
resistivity of materials, electrical power and energy, EMF and internal resistance of cells, 
Kirchhoff’s rules, and Wheatstone bridge for circuit analysis."""),

(4, "Moving Charges and Magnetism",
"""This chapter explains magnetic force on moving charges and current-carrying conductors, 
Lorentz force, motion of charged particles in magnetic field, Ampere’s circuital law, 
magnetic field due to current loops and solenoids, torque on current loop, magnetic dipole, 
and working of moving coil galvanometer."""),

(5, "Magnetism and Matter",
"""This chapter discusses magnetic field lines, magnetic dipole, magnetisation, magnetic intensity, 
Gauss’s law in magnetism, and magnetic properties of materials including diamagnetism, paramagnetism, 
and ferromagnetism."""),

(6, "Electromagnetic Induction",
"""This chapter introduces Faraday’s experiments, magnetic flux, Faraday’s law of induction, 
Lenz’s law, motional EMF, self and mutual inductance, and working of AC generator."""),

(7, "Alternating Current",
"""This chapter explains alternating current and voltage, AC applied to resistor, inductor, and capacitor, 
series LCR circuits, phasor representation, resonance, power factor, and working of transformers."""),

(8, "Electromagnetic Waves",
"""This chapter discusses displacement current, electromagnetic waves, their sources and properties, 
and the electromagnetic spectrum including radio waves, microwaves, infrared, visible, ultraviolet, 
X-rays and gamma rays."""),

(9, "Ray Optics and Optical Instruments",
"""This chapter covers reflection and refraction of light, spherical mirrors, mirror formula, 
refraction through lenses and prisms, total internal reflection, optical instruments such as microscope 
and telescope, and image formation concepts."""),

(10, "Wave Optics",
"""This chapter introduces Huygens’ principle, reflection and refraction of waves, interference of light, 
Young’s double slit experiment, diffraction (single slit), and polarisation of light."""),

(11, "Dual Nature of Radiation and Matter",
"""This chapter explains photoelectric effect, experimental observations, Einstein’s photoelectric equation, 
particle nature of light (photons), and wave nature of matter through de Broglie hypothesis."""),

(12, "Atoms",
"""This chapter discusses Rutherford’s alpha scattering experiment, atomic spectra, Bohr model of hydrogen atom, 
energy levels, line spectra, and de Broglie’s explanation of quantised orbits."""),

(13, "Nuclei",
"""This chapter explains composition and size of nucleus, mass-energy relation, nuclear binding energy, 
nuclear forces, radioactivity, nuclear fission, fusion, and energy generation in stars."""),

(14, "Semiconductor Electronics: Materials, Devices and Simple Circuits",
"""This chapter introduces intrinsic and extrinsic semiconductors, p-n junction formation, 
semiconductor diode, forward and reverse biasing, and application of junction diode as rectifier.""")

]

cursor.executemany("INSERT OR REPLACE INTO summaries VALUES (?, ?, ?)", data)

conn.commit()
conn.close()

print("Class 12 Physics summaries inserted successfully.")
