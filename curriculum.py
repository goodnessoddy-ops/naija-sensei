"""
Nigerian secondary school curriculum corpus.

216 short passages across 41 of the 72 subjects a student can actually
select in student_profile.py (compulsory + department core/optional +
trade). SS1-SS3 only, no JSS.

COVERAGE STATUS (checked programmatically against student_profile.py, not
eyeballed): all 3 compulsory subjects, all science/commercial/arts core
subjects, and this pass's 14 added core/optional subjects (Animal
Husbandry, Arabic, Edo/Efik/Ibibio Language, Fine Art, Foods and Nutrition,
French, Health Education, Music, Office Practice, Physical Education,
Store Management, Technical Drawing) are now covered. Content for these 14
was grounded in real WAEC syllabus sources (waecsyllabus.com) where found -
Animal Husbandry, Foods and Nutrition, Health Education, Music, Office
Practice, and Technical Drawing were cross-checked against actual syllabus
text. Fine Art, Store Management, French, Edo, Efik, and Ibibio Language
have now also been directly cross-checked against waecsyllabus.com (July
2026 pass) and their content rewritten from the actual syllabus pages
rather than a generic template - see the entries themselves for what
changed. Arabic remains unsourced: waecsyllabus.com does not currently
publish an Arabic syllabus page, so those entries are still written from
general subject knowledge and flagged inline.

STILL MISSING ENTIRELY (31 subjects, all trade subjects except the 3
already covered - Catering Craft Practice, Fashion Design and Garment
Making, GSM Maintenance and Repairs): Auto Mechanics, Basketry, Batik and
Tie-Dye, Beauty and Cosmetology, Block Laying/Bricklaying/Concreting, Book
Binding, Business Management, Cabinet Making, Computer Craft Practice,
Dyeing and Bleaching, Electrical Installation and Maintenance, Electronics,
Fishery, Floral Decoration, Furniture Making, Glass and Ceramics, Graphic
Design, Home Management, Horticulture, Iron and Steel Fabrication, Leather
Goods Manufacturing, Painting and Decorating, Photo Technology, Plumbing
and Pipe Fitting, Printing Craft Practice, Refrigeration and Air
Conditioning, Sculpture, Shoemaking, Typewriting, Upholstery, Welding and
Fabrication. These were deprioritized because they're far less commonly
selected than the core/optional subjects above - revisit if a specific
trade is confirmed relevant to actual current students.

Every subject name in this file has been verified to match
student_profile.py's DEPARTMENTS/TRADE_SUBJECTS strings exactly
(programmatic diff, not manual check) - this matters because subject
filtering in rag.py is an exact string match, so even one character of
mismatch means zero retrieval for that subject, silently.

Format kept tight - short, fact-dense passages. Better retrieval comes from
many narrow chunks than few wide ones.

STILL UNREVIEWED IN ANY PASS: data/generated_curriculum.py, this app's
other and much larger curriculum file (~1,700 of the app's ~1,830 total
passages) - never inspected in any session covering this file.
"""

CURRICULUM = [
    # =========== BIOLOGY ===========
    {
        "id": "bio_ss1_digestion",
        "subject": "Biology",
        "grade": "SS1",
        "topic": "Digestion",
        "content": (
            "Digestion is the breakdown of food into small absorbable molecules. "
            "It starts in the mouth where saliva contains amylase, which breaks down starch. "
            "In the stomach, hydrochloric acid and pepsin break down proteins. "
            "The small intestine absorbs nutrients into the blood. "
            "The large intestine absorbs water and forms waste."
        ),
    },
    {
        "id": "bio_ss1_cell",
        "subject": "Biology",
        "grade": "SS1",
        "topic": "The Cell",
        "content": (
            "The cell is the smallest unit of life. Plant and animal cells share a nucleus, "
            "cytoplasm, mitochondria, and a cell membrane. Plant cells additionally have a "
            "rigid cell wall made of cellulose, large vacuoles, and chloroplasts containing "
            "chlorophyll. Animal cells lack these but are flexible in shape."
        ),
    },
    {
        "id": "bio_ss2_photosynthesis",
        "subject": "Biology",
        "grade": "SS2",
        "topic": "Photosynthesis",
        "content": (
            "Photosynthesis is how green plants make food using sunlight. "
            "It happens in chloroplasts, which contain the green pigment chlorophyll. "
            "Inputs: carbon dioxide and water. Outputs: glucose and oxygen. "
            "Word equation: carbon dioxide + water -> glucose + oxygen (in sunlight, chlorophyll). "
            "The light reactions split water; the dark reactions fix carbon dioxide into glucose."
        ),
    },
    {
        "id": "bio_ss2_respiration",
        "subject": "Biology",
        "grade": "SS2",
        "topic": "Cellular Respiration",
        "content": (
            "Respiration breaks down glucose to release energy stored as ATP. "
            "Aerobic respiration uses oxygen, fully breaks glucose into carbon dioxide and water, "
            "and produces about 38 ATP per glucose molecule. "
            "Anaerobic respiration in muscles produces lactic acid; in yeast it produces ethanol "
            "and carbon dioxide. Anaerobic respiration releases far less energy."
        ),
    },
    {
        "id": "bio_ss2_circulation",
        "subject": "Biology",
        "grade": "SS2",
        "topic": "Circulatory System",
        "content": (
            "The human circulatory system has the heart, blood vessels, and blood. "
            "The heart has four chambers: two atria (top) and two ventricles (bottom). "
            "Arteries carry blood away from the heart; veins return blood to the heart. "
            "Capillaries are tiny vessels where exchange of gases and nutrients happens. "
            "Pulmonary circulation goes to the lungs; systemic circulation goes to the body."
        ),
    },
    {
        "id": "bio_ss2_genetics",
        "subject": "Biology",
        "grade": "SS2",
        "topic": "Genetics and Heredity",
        "content": (
            "Genetics is the study of how traits pass from parents to offspring. "
            "Genes are units of heredity made of DNA. Each trait usually has two alleles, "
            "one from each parent. Dominant alleles mask recessive ones. "
            "Mendel's first law (segregation): each parent passes only one allele per trait. "
            "A Punnett square shows the probability of offspring genotypes."
        ),
    },
    {
        "id": "bio_ss3_ecology",
        "subject": "Biology",
        "grade": "SS3",
        "topic": "Ecology and Ecosystems",
        "content": (
            "An ecosystem is a community of living organisms interacting with their non-living environment. "
            "Producers (plants) make their own food via photosynthesis. "
            "Consumers eat other organisms: herbivores eat plants, carnivores eat animals, omnivores eat both. "
            "Decomposers (fungi and bacteria) break down dead matter, returning nutrients to the soil. "
            "Energy flows in food chains; about 10% transfers between each trophic level."
        ),
    },
    {
        "id": "bio_ss3_reproduction",
        "subject": "Biology",
        "grade": "SS3",
        "topic": "Human Reproduction",
        "content": (
            "Human reproduction is sexual: it requires a sperm cell from the male and an egg cell from the female. "
            "Fertilization happens in the fallopian tube, forming a zygote. "
            "The zygote divides as it travels to the uterus and implants in the lining. "
            "Pregnancy lasts about 40 weeks. The placenta supplies oxygen and nutrients to the developing fetus."
        ),
    },
    {
        "id": "bio_ss2_nervous_coordination",
        "subject": "Biology",
        "grade": "SS2",
        "topic": "Nervous Coordination",
        "content": (
            "The nervous system has two parts: the central nervous system (brain and spinal cord) and the "
            "peripheral nervous system (nerves connecting the CNS to the body). "
            "A neuron (nerve cell) has a cell body, dendrites (receive signals), and an axon (sends signals). "
            "A reflex action is a fast, automatic response to a stimulus that does not involve conscious "
            "thought, e.g. withdrawing a hand from a hot object — it travels through a reflex arc. "
            "The brain has three main regions: the cerebrum (thought, voluntary movement), the cerebellum "
            "(balance and coordination), and the medulla oblongata (controls breathing and heart rate)."
        ),
    },
    {
        "id": "bio_ss2_excretion",
        "subject": "Biology",
        "grade": "SS2",
        "topic": "Excretion",
        "content": (
            "Excretion is the removal of metabolic waste products from the body. "
            "The kidney is the main excretory organ in mammals; its functional unit is the nephron, which "
            "filters blood and reabsorbs useful substances. "
            "The kidney removes urea (from protein breakdown) and excess water and salts as urine. "
            "The lungs excrete carbon (IV) oxide and water vapour; the skin excretes water and salts as sweat; "
            "the liver breaks down toxins and excess amino acids into urea. "
            "Kidney failure can be treated with dialysis, which filters the blood artificially."
        ),
    },
    {
        "id": "bio_ss3_evolution",
        "subject": "Biology",
        "grade": "SS3",
        "topic": "Evolution",
        "content": (
            "Evolution is the gradual change in inherited characteristics of a population over generations. "
            "Charles Darwin's theory of natural selection: organisms produce more offspring than can survive; "
            "variation exists within a population; organisms with favourable traits survive and reproduce "
            "more (survival of the fittest); favourable traits become more common over time. "
            "Evidence for evolution includes fossils (showing gradual change over time), homologous "
            "structures (similar bone structures across species with different functions, e.g. human arm "
            "and bird wing), and comparative anatomy/embryology. "
            "Natural selection differs from artificial selection, where humans choose which traits to breed for."
        ),
    },
    {
        "id": "bio_ss1_support_movement",
        "subject": "Biology",
        "grade": "SS1",
        "topic": "Support and Movement",
        "content": (
            "The skeleton provides support, protection, locomotion, and a site for muscle attachment. "
            "Three skeleton types: exoskeleton (external, e.g. insects), endoskeleton (internal, e.g. "
            "vertebrates), and hydrostatic skeleton (fluid-filled, e.g. earthworms). "
            "The human skeleton includes the axial skeleton (skull, vertebral column, ribs) and appendicular "
            "skeleton (limbs and girdles). "
            "Joints allow movement: ball-and-socket joints (e.g. hip) allow movement in many directions; "
            "hinge joints (e.g. knee) allow movement in one plane. "
            "Muscles work in antagonistic pairs — as one contracts, its pair relaxes, e.g. biceps and triceps."
        ),
    },

    # =========== CHEMISTRY ===========
    {
        "id": "chem_ss1_atom",
        "subject": "Chemistry",
        "grade": "SS1",
        "topic": "Atomic Structure",
        "content": (
            "An atom is the smallest particle of an element that retains its properties. "
            "It has a nucleus containing positively charged protons and neutral neutrons. "
            "Negatively charged electrons orbit the nucleus in shells. "
            "Atomic number = number of protons. Mass number = protons + neutrons. "
            "Isotopes are atoms of the same element with different numbers of neutrons."
        ),
    },
    {
        "id": "chem_ss1_periodic_table",
        "subject": "Chemistry",
        "grade": "SS1",
        "topic": "Periodic Table",
        "content": (
            "The periodic table arranges elements by increasing atomic number. "
            "Vertical columns are groups; elements in a group share similar chemical properties. "
            "Horizontal rows are periods. Group 1 are alkali metals (very reactive). "
            "Group 7 are halogens. Group 0 are noble gases (very unreactive). "
            "Metals are on the left, non-metals on the right."
        ),
    },
    {
        "id": "chem_ss1_chemical_bonding",
        "subject": "Chemistry",
        "grade": "SS1",
        "topic": "Chemical Bonding",
        "content": (
            "Atoms bond to achieve a stable electron configuration like a noble gas. "
            "Ionic bonding: a metal donates electrons to a non-metal, forming oppositely charged ions "
            "that attract (e.g., NaCl). Covalent bonding: two non-metals share electrons (e.g., H2O). "
            "Metallic bonding: metal atoms share a sea of free electrons, giving conductivity and malleability."
        ),
    },
    {
        "id": "chem_ss2_acids_bases",
        "subject": "Chemistry",
        "grade": "SS2",
        "topic": "Acids and Bases",
        "content": (
            "Acids release hydrogen ions (H+) in water, taste sour, turn blue litmus red, and have pH below 7. "
            "Bases release hydroxide ions (OH-) in water, feel slippery, turn red litmus blue, and have pH above 7. "
            "Strong acids fully ionize (HCl, H2SO4); weak acids only partially ionize (CH3COOH). "
            "Acid + base -> salt + water (neutralization). pH 7 is neutral, like pure water."
        ),
    },
    {
        "id": "chem_ss2_mole_concept",
        "subject": "Chemistry",
        "grade": "SS2",
        "topic": "Mole Concept",
        "content": (
            "A mole is 6.02 x 10^23 particles (Avogadro's number). "
            "The molar mass of a substance equals its relative atomic or molecular mass in grams. "
            "Number of moles = mass (g) / molar mass (g/mol). "
            "At standard temperature and pressure (STP), one mole of any gas occupies 22.4 dm^3."
        ),
    },
    {
        "id": "chem_ss2_redox",
        "subject": "Chemistry",
        "grade": "SS2",
        "topic": "Oxidation and Reduction",
        "content": (
            "Oxidation is the loss of electrons or gain of oxygen. Reduction is the gain of electrons or loss of oxygen. "
            "Mnemonic: OIL RIG (Oxidation Is Loss, Reduction Is Gain). "
            "Both happen together in a redox reaction. The substance oxidized is the reducing agent; "
            "the substance reduced is the oxidizing agent. Rusting of iron is a slow oxidation."
        ),
    },
    {
        "id": "chem_ss3_organic",
        "subject": "Chemistry",
        "grade": "SS3",
        "topic": "Organic Chemistry",
        "content": (
            "Organic chemistry is the study of carbon compounds. "
            "Alkanes are saturated hydrocarbons (single bonds), general formula CnH2n+2 (e.g., methane CH4). "
            "Alkenes have one double bond, formula CnH2n (e.g., ethene C2H4). "
            "Alkynes have a triple bond, formula CnH2n-2 (e.g., ethyne C2H2). "
            "Functional groups define compound families: -OH (alcohols), -COOH (carboxylic acids)."
        ),
    },
    {
        "id": "chem_ss3_electrochem",
        "subject": "Chemistry",
        "grade": "SS3",
        "topic": "Electrolysis",
        "content": (
            "Electrolysis decomposes a compound by passing electric current through it. "
            "The electrolyte is the molten or aqueous compound. "
            "The cathode is the negative electrode where reduction happens (positive ions gain electrons). "
            "The anode is the positive electrode where oxidation happens (negative ions lose electrons). "
            "Electrolysis is used to extract reactive metals like aluminium and to electroplate objects."
        ),
    },
    {
        "id": "chem_ss1_separation_techniques",
        "subject": "Chemistry",
        "grade": "SS1",
        "topic": "Separation Techniques",
        "content": (
            "Filtration separates an insoluble solid from a liquid using filter paper. "
            "Decantation pours off a liquid from a settled solid without disturbing the sediment. "
            "Crystallization separates a dissolved solid from a solution by evaporating the solvent until "
            "crystals form. "
            "Simple distillation separates a solvent from a dissolved solid by evaporation and condensation; "
            "fractional distillation separates liquids with different boiling points, e.g. in crude oil refining. "
            "Chromatography separates dissolved substances based on how far they travel on a medium, e.g. "
            "paper chromatography for separating dyes. "
            "Criteria for purity: a pure substance has a sharp, fixed melting and boiling point."
        ),
    },
    {
        "id": "chem_ss2_rate_of_reaction",
        "subject": "Chemistry",
        "grade": "SS2",
        "topic": "Rate of Reaction and Energy Changes",
        "content": (
            "Rate of reaction increases with higher temperature, higher concentration, greater surface area "
            "(for solids), and the presence of a catalyst. "
            "A catalyst speeds up a reaction without being used up itself, by lowering the activation energy — "
            "the minimum energy needed for a reaction to occur. "
            "An exothermic reaction releases heat to the surroundings (temperature rises), e.g. combustion. "
            "An endothermic reaction absorbs heat from the surroundings (temperature falls), e.g. photosynthesis. "
            "Enthalpy change (delta H) is negative for exothermic reactions and positive for endothermic reactions."
        ),
    },
    {
        "id": "chem_ss2_salts",
        "subject": "Chemistry",
        "grade": "SS2",
        "topic": "Salts",
        "content": (
            "A salt is formed when the hydrogen ion of an acid is replaced by a metal or ammonium ion. "
            "Normal salts have all replaceable hydrogens substituted, e.g. NaCl. "
            "Acid salts have some hydrogen remaining, e.g. NaHCO3. "
            "Salts can be prepared by neutralization (acid + base), direct combination, or precipitation. "
            "Hydrolysis of salts: salts of strong acid + weak base are acidic in solution; salts of weak "
            "acid + strong base are alkaline in solution; salts of strong acid + strong base are neutral."
        ),
    },

    # =========== PHYSICS ===========
    {
        "id": "phy_ss1_motion",
        "subject": "Physics",
        "grade": "SS1",
        "topic": "Motion",
        "content": (
            "Motion is change of position with time. Distance is the total path travelled (scalar). "
            "Displacement is the straight-line change of position with direction (vector). "
            "Speed = distance / time. Velocity = displacement / time. "
            "Acceleration = change in velocity / time. "
            "For uniform acceleration: v = u + at, s = ut + 0.5at^2, v^2 = u^2 + 2as."
        ),
    },
    {
        "id": "phy_ss1_newton_laws",
        "subject": "Physics",
        "grade": "SS1",
        "topic": "Newton's Laws of Motion",
        "content": (
            "Newton's first law: an object remains at rest or in uniform motion unless acted on by a net external force. "
            "This is also called the law of inertia. "
            "Newton's second law: force equals mass times acceleration (F = ma). "
            "The unit of force is the newton (N). "
            "Newton's third law: for every action there is an equal and opposite reaction."
        ),
    },
    {
        "id": "phy_ss1_energy",
        "subject": "Physics",
        "grade": "SS1",
        "topic": "Work, Energy, and Power",
        "content": (
            "Work = force x distance moved in the direction of force, measured in joules (J). "
            "Energy is the capacity to do work. Kinetic energy = 0.5 x mass x velocity^2. "
            "Gravitational potential energy = mass x g x height. "
            "Power = work done / time taken, measured in watts (W). "
            "The principle of conservation of energy: energy is neither created nor destroyed, only transformed."
        ),
    },
    {
        "id": "phy_ss2_waves",
        "subject": "Physics",
        "grade": "SS2",
        "topic": "Waves",
        "content": (
            "A wave is a disturbance that transfers energy without transferring matter. "
            "Transverse waves vibrate perpendicular to direction of travel (light, water surface). "
            "Longitudinal waves vibrate parallel to direction of travel (sound). "
            "Wavelength is the distance between two crests. Frequency is waves per second (hertz). "
            "Wave speed = frequency x wavelength."
        ),
    },
    {
        "id": "phy_ss2_light",
        "subject": "Physics",
        "grade": "SS2",
        "topic": "Reflection and Refraction of Light",
        "content": (
            "Reflection: light bouncing off a surface. Angle of incidence equals angle of reflection. "
            "Refraction: light bending when it passes from one medium to another due to a speed change. "
            "Light slows down in denser media (e.g., from air to water). "
            "Snell's law: n1 sin(i) = n2 sin(r), where n is the refractive index. "
            "Convex lenses converge light; concave lenses diverge it."
        ),
    },
    {
        "id": "phy_ss2_electricity",
        "subject": "Physics",
        "grade": "SS2",
        "topic": "Current Electricity",
        "content": (
            "Electric current is the rate of flow of charge, measured in amperes (A). "
            "Voltage (potential difference) drives current through a circuit, measured in volts (V). "
            "Resistance opposes current flow, measured in ohms (omega). "
            "Ohm's law: V = IR. "
            "In series circuits, current is the same through all components. "
            "In parallel circuits, voltage is the same across all branches."
        ),
    },
    {
        "id": "phy_ss3_em_induction",
        "subject": "Physics",
        "grade": "SS3",
        "topic": "Electromagnetic Induction",
        "content": (
            "Electromagnetic induction: a changing magnetic field induces a voltage in a conductor. "
            "Faraday's law: induced EMF is proportional to the rate of change of magnetic flux. "
            "Lenz's law: the induced current opposes the change that produced it. "
            "Generators convert mechanical energy to electrical energy by rotating a coil in a magnetic field. "
            "Transformers change voltage levels using two coupled coils on an iron core."
        ),
    },
    {
        "id": "phy_ss3_modern",
        "subject": "Physics",
        "grade": "SS3",
        "topic": "Modern Physics",
        "content": (
            "An atom has a small dense nucleus of protons and neutrons, with electrons in orbitals. "
            "Radioactivity is the spontaneous emission of radiation from unstable nuclei. "
            "Three types: alpha (helium nucleus, low penetration), beta (electron, medium penetration), "
            "and gamma (high-energy photon, very high penetration). "
            "Half-life is the time for half a sample to decay. Used in radiocarbon dating and medical imaging."
        ),
    },
    {
        "id": "phy_ss1_heat_energy",
        "subject": "Physics",
        "grade": "SS1",
        "topic": "Heat Energy",
        "content": (
            "Temperature is measured in Celsius, Fahrenheit, or Kelvin (K = °C + 273). "
            "Heat transfers by conduction (through solids), convection (through fluids via density "
            "differences), and radiation (through empty space, no medium needed). "
            "Specific heat capacity is the heat needed to raise 1 kg of a substance by 1°C: Q = mc(delta T). "
            "Latent heat is the heat absorbed or released during a change of state without a temperature "
            "change (fusion: solid to liquid; vaporization: liquid to gas). "
            "Boyle's law: PV = constant at fixed temperature. Charles' law: V/T = constant at fixed pressure."
        ),
    },
    {
        "id": "phy_ss1_pressure",
        "subject": "Physics",
        "grade": "SS1",
        "topic": "Pressure",
        "content": (
            "Pressure = Force / Area, measured in Pascals (Pa = N/m²). "
            "Pressure in a fluid increases with depth: P = h x rho x g (height x density x gravity). "
            "Pascal's principle: pressure applied to an enclosed fluid is transmitted equally in all "
            "directions — this is the basis of hydraulic machines. "
            "Atmospheric pressure is measured with a barometer; standard atmospheric pressure is about "
            "101,325 Pa at sea level. "
            "A manometer measures the pressure of a gas relative to atmospheric pressure."
        ),
    },
    {
        "id": "phy_ss2_electrostatics",
        "subject": "Physics",
        "grade": "SS2",
        "topic": "Electrostatics",
        "content": (
            "Electrostatics studies electric charges at rest. Like charges repel; unlike charges attract. "
            "Objects can be charged by friction, contact, or induction. "
            "An electric field is the region around a charge where another charge experiences a force; "
            "field lines point from positive to negative charges. "
            "A capacitor stores electric charge; capacitance C = Q/V (charge over voltage), measured in Farads. "
            "Earthing (grounding) removes excess charge by connecting an object to the earth with a conductor."
        ),
    },

    # =========== MATHEMATICS ===========
    {
        "id": "math_ss1_algebra_basics",
        "subject": "Mathematics",
        "grade": "SS1",
        "topic": "Algebraic Expressions",
        "content": (
            "An algebraic expression uses letters to represent numbers, e.g., 3x + 2. "
            "Like terms have the same variable to the same power: 3x and 5x are like terms; 3x and 3x^2 are not. "
            "To simplify, combine like terms: 3x + 5x - 2 + 7 = 8x + 5. "
            "When expanding brackets, multiply each term inside by the term outside: 3(x + 2) = 3x + 6."
        ),
    },
    {
        "id": "math_ss1_quadratic",
        "subject": "Mathematics",
        "grade": "SS1",
        "topic": "Quadratic Equations",
        "content": (
            "A quadratic equation has the form ax^2 + bx + c = 0, where a is not zero. "
            "Three solving methods: factorization, completing the square, and the quadratic formula. "
            "Quadratic formula: x = (-b +/- sqrt(b^2 - 4ac)) / 2a. "
            "The discriminant b^2 - 4ac tells you the number of real roots: "
            "positive = two roots, zero = one repeated root, negative = no real roots."
        ),
    },
    {
        "id": "math_ss1_indices_logs",
        "subject": "Mathematics",
        "grade": "SS1",
        "topic": "Indices and Logarithms",
        "content": (
            "Indices (powers) follow these rules: a^m x a^n = a^(m+n); a^m / a^n = a^(m-n); (a^m)^n = a^(mn); "
            "a^0 = 1; a^(-n) = 1/a^n. "
            "Logarithms are the inverse of indices: if a^x = y, then log_a(y) = x. "
            "Common logs use base 10 and are written log(y). "
            "Useful identities: log(ab) = log(a) + log(b); log(a/b) = log(a) - log(b)."
        ),
    },
    {
        "id": "math_ss2_simultaneous",
        "subject": "Mathematics",
        "grade": "SS2",
        "topic": "Simultaneous Equations",
        "content": (
            "Simultaneous equations are two or more equations sharing the same variables, solved together. "
            "Two main methods: substitution (rearrange one equation, plug into the other) and "
            "elimination (add or subtract to remove one variable). "
            "Example: x + y = 7 and x - y = 3. Adding both: 2x = 10, so x = 5, then y = 2. "
            "Graphically, the solution is the point where the two lines intersect."
        ),
    },
    {
        "id": "math_ss2_trig",
        "subject": "Mathematics",
        "grade": "SS2",
        "topic": "Trigonometry",
        "content": (
            "In a right-angled triangle with angle theta: "
            "sine = opposite / hypotenuse, cosine = adjacent / hypotenuse, tangent = opposite / adjacent. "
            "Mnemonic: SOHCAHTOA. "
            "Pythagoras' theorem: a^2 + b^2 = c^2, where c is the hypotenuse. "
            "Sine rule: a/sin(A) = b/sin(B) = c/sin(C). "
            "Cosine rule: a^2 = b^2 + c^2 - 2bc cos(A)."
        ),
    },
    {
        "id": "math_ss2_geometry",
        "subject": "Mathematics",
        "grade": "SS2",
        "topic": "Plane Geometry",
        "content": (
            "Angles on a straight line sum to 180 degrees. Angles around a point sum to 360 degrees. "
            "Vertically opposite angles are equal. "
            "Sum of interior angles of a triangle = 180. Sum of interior angles of a polygon = (n-2) x 180. "
            "Area of a triangle = 0.5 x base x height. Area of a circle = pi x r^2. "
            "Circumference of a circle = 2 x pi x r."
        ),
    },
    {
        "id": "math_ss3_calculus_intro",
        "subject": "Mathematics",
        "grade": "SS3",
        "topic": "Differentiation",
        "content": (
            "Differentiation finds the rate of change of a function (the gradient at any point). "
            "Power rule: if y = x^n, then dy/dx = nx^(n-1). "
            "Constants: if y = c, then dy/dx = 0. "
            "Sum rule: differentiate each term separately. "
            "Example: y = 3x^2 + 5x - 4 gives dy/dx = 6x + 5. "
            "At a turning point, dy/dx = 0."
        ),
    },
    {
        "id": "math_ss3_integration_intro",
        "subject": "Mathematics",
        "grade": "SS3",
        "topic": "Integration",
        "content": (
            "Integration is the reverse of differentiation; it finds the function whose derivative is given. "
            "Integral of x^n = x^(n+1) / (n+1) + C, for n not equal to -1. "
            "Always include the constant of integration C for indefinite integrals. "
            "Definite integrals from a to b give the area under the curve between those limits. "
            "Example: integral of 3x^2 dx = x^3 + C."
        ),
    },
    {
        "id": "math_ss3_statistics",
        "subject": "Mathematics",
        "grade": "SS3",
        "topic": "Statistics",
        "content": (
            "Measures of central tendency: mean (average), median (middle value), mode (most frequent value). "
            "Mean = sum of values / number of values. "
            "For grouped data, use class midpoints. "
            "Range = highest - lowest. Standard deviation measures how spread out the data is from the mean. "
            "Histograms display frequency distributions; pie charts show proportions of a whole."
        ),
    },
    {
        "id": "math_ss3_probability",
        "subject": "Mathematics",
        "grade": "SS3",
        "topic": "Probability",
        "content": (
            "Probability measures the likelihood of an event, between 0 (impossible) and 1 (certain). "
            "P(event) = number of favourable outcomes / total number of outcomes. "
            "For independent events A and B: P(A and B) = P(A) x P(B). "
            "For mutually exclusive events: P(A or B) = P(A) + P(B). "
            "Example: probability of rolling a 6 on a fair die = 1/6."
        ),
    },
    {
        "id": "math_ss1_number_numeration",
        "subject": "Mathematics",
        "grade": "SS1",
        "topic": "Number and Numeration",
        "content": (
            "Number bases: numbers can be expressed in bases other than 10, e.g. binary (base 2) uses only 0 and 1. "
            "To convert base 10 to base 2, divide repeatedly by 2 and read the remainders bottom-up: "
            "13 in base 10 = 1101 in base 2. "
            "LCM (Lowest Common Multiple) and HCF (Highest Common Factor) are found using prime factorization. "
            "Standard form writes numbers as A x 10^n, where 1 <= A < 10, e.g. 4500 = 4.5 x 10^3. "
            "Approximation rounds a number to a given number of significant figures or decimal places."
        ),
    },
    {
        "id": "math_ss1_mensuration",
        "subject": "Mathematics",
        "grade": "SS1",
        "topic": "Mensuration",
        "content": (
            "Mensuration is the calculation of lengths, areas, and volumes of shapes. "
            "Perimeter of a rectangle = 2(l + w); area = l x w. "
            "Volume of a cuboid = l x w x h; volume of a cylinder = pi x r^2 x h. "
            "Surface area of a cylinder = 2 x pi x r x (r + h). "
            "Volume of a cone = (1/3) x pi x r^2 x h; volume of a sphere = (4/3) x pi x r^3. "
            "Area of a trapezium = 0.5 x (sum of parallel sides) x height."
        ),
    },
    {
        "id": "math_ss1_sets",
        "subject": "Mathematics",
        "grade": "SS1",
        "topic": "Sets",
        "content": (
            "A set is a well-defined collection of objects, e.g. A = {1, 2, 3}. "
            "The universal set contains all elements under consideration; the empty set has no elements. "
            "Union (A union B) combines all elements in A or B; intersection (A intersect B) contains only "
            "elements in both. "
            "The complement of A contains elements in the universal set but not in A. "
            "Venn diagrams show these relationships visually using overlapping circles. "
            "n(A union B) = n(A) + n(B) - n(A intersect B) for finding how many elements are in a combined set."
        ),
    },
    {
        "id": "math_ss2_matrices",
        "subject": "Mathematics",
        "grade": "SS2",
        "topic": "Matrices",
        "content": (
            "A matrix is a rectangular array of numbers arranged in rows and columns, e.g. a 2x2 matrix has "
            "2 rows and 2 columns. "
            "To add or subtract matrices, they must have the same order (dimensions); combine corresponding elements. "
            "To multiply two matrices, the number of columns in the first must equal the number of rows in the second. "
            "The determinant of a 2x2 matrix [[a,b],[c,d]] is ad - bc. "
            "A matrix with determinant zero has no inverse and is called singular. "
            "The identity matrix has 1s on the diagonal and 0s elsewhere, and leaves any matrix unchanged when "
            "multiplied by it."
        ),
    },
    {
        "id": "math_ss2_coordinate_geometry",
        "subject": "Mathematics",
        "grade": "SS2",
        "topic": "Coordinate Geometry",
        "content": (
            "Coordinate geometry studies shapes and lines using an x-y plane. "
            "Gradient (slope) of a line through points (x1,y1) and (x2,y2) = (y2-y1)/(x2-x1). "
            "The equation of a straight line is y = mx + c, where m is the gradient and c is the y-intercept. "
            "Distance between two points = sqrt((x2-x1)^2 + (y2-y1)^2). "
            "Midpoint of a line segment = ((x1+x2)/2, (y1+y2)/2). "
            "Two lines are parallel if they have equal gradients, and perpendicular if the product of their "
            "gradients is -1."
        ),
    },
    {
        "id": "math_ss3_vectors",
        "subject": "Mathematics",
        "grade": "SS3",
        "topic": "Vectors",
        "content": (
            "A vector has both magnitude (size) and direction, unlike a scalar which has magnitude only. "
            "Vectors are written as column vectors, e.g. (3, 4) meaning 3 units right and 4 units up. "
            "Vector addition combines column vectors component-wise: (3,4) + (1,2) = (4,6). "
            "Magnitude of a vector (x,y) = sqrt(x^2 + y^2). "
            "A vector can be multiplied by a scalar: 2 x (3,4) = (6,8), which changes its magnitude but not "
            "its direction. "
            "The zero vector has magnitude 0 and no defined direction."
        ),
    },
    {
        "id": "math_ss2_financial_arithmetic",
        "subject": "Mathematics",
        "grade": "SS2",
        "topic": "Commercial and Financial Arithmetic",
        "content": (
            "Simple interest = (Principal x Rate x Time) / 100. "
            "Compound interest adds interest to the principal each period: Amount = P(1 + r/100)^n, where n "
            "is the number of periods. "
            "Profit or loss percentage = (Profit or Loss / Cost Price) x 100. "
            "Discount is a reduction from the marked price; commission is a percentage payment for a service or sale. "
            "Depreciation reduces an asset's value over time, often using the reducing balance method: "
            "Value = P(1 - r/100)^n. "
            "Hire purchase spreads a payment over instalments, usually at a higher total cost than paying in "
            "full upfront."
        ),
    },

    # =========== ENGLISH ===========
    {
        "id": "eng_ss1_parts_of_speech",
        "subject": "English Language",
        "grade": "SS1",
        "topic": "Parts of Speech",
        "content": (
            "The eight parts of speech are: noun (person, place, thing), pronoun (he, she, it), "
            "verb (action or state), adjective (describes a noun), adverb (describes a verb or adjective), "
            "preposition (in, on, under), conjunction (and, but, because), and interjection (wow, oh)."
        ),
    },
    {
        "id": "eng_ss1_tenses",
        "subject": "English Language",
        "grade": "SS1",
        "topic": "Tenses",
        "content": (
            "Tense shows when an action happens. Three main tenses: past, present, and future. "
            "Each has four forms: simple (I eat), continuous (I am eating), "
            "perfect (I have eaten), and perfect continuous (I have been eating). "
            "Common errors include mixing tenses in one sentence and confusing past simple with present perfect."
        ),
    },
    {
        "id": "eng_ss2_essay_writing",
        "subject": "English Language",
        "grade": "SS2",
        "topic": "Essay Writing",
        "content": (
            "A good essay has three parts: introduction, body, conclusion. "
            "The introduction states the topic and your main argument or thesis. "
            "Each body paragraph covers one main point with supporting examples. "
            "The conclusion restates your argument and gives a final thought. "
            "Use formal language, vary your sentence structures, and avoid contractions in formal essays."
        ),
    },
    {
        "id": "eng_ss2_comprehension",
        "subject": "English Language",
        "grade": "SS2",
        "topic": "Reading Comprehension",
        "content": (
            "For comprehension passages, read the questions first to know what to look for. "
            "Skim the passage for general meaning, then scan for specific details. "
            "Answer in your own words where possible; quote only when asked. "
            "For 'in your own words' questions, paraphrase fully without copying phrases. "
            "For inferential questions, use clues in the text plus reasoning."
        ),
    },
    {
        "id": "eng_ss3_summary",
        "subject": "English Language",
        "grade": "SS3",
        "topic": "Summary Writing",
        "content": (
            "A summary captures only the main ideas of a passage in fewer words. "
            "Stick to the word limit (often around one-third the original). "
            "Use your own words; do not copy whole sentences. "
            "Identify topic sentences in each paragraph as a starting point. "
            "Avoid examples, illustrations, and repeated ideas. Write in continuous prose, not bullet points."
        ),
    },
    {
        "id": "eng_ss3_oral",
        "subject": "English Language",
        "grade": "SS3",
        "topic": "Oral English (Phonetics)",
        "content": (
            "Oral English tests vowel and consonant sounds. "
            "Pure vowels (monophthongs): /i:/ as in see, /I/ as in sit, /a:/ as in car. "
            "Diphthongs (gliding vowels): /eI/ as in say, /aI/ as in five, /OI/ as in boy. "
            "Consonant pairs: /p/ vs /b/, /t/ vs /d/, /k/ vs /g/ (voiceless vs voiced). "
            "Stress placement changes meaning: REcord (noun) vs reCORD (verb)."
        ),
    },
    {
        "id": "eng_ss3_literary_devices",
        "subject": "English Language",
        "grade": "SS3",
        "topic": "Literary Devices",
        "content": (
            "Simile: comparing two things using like or as ('as fast as a cheetah'). "
            "Metaphor: a direct comparison without like or as ('time is money'). "
            "Personification: giving human qualities to non-humans ('the wind whispered'). "
            "Alliteration: repeated consonant sounds ('Peter Piper picked'). "
            "Hyperbole: deliberate exaggeration ('I've told you a million times'). "
            "Onomatopoeia: words that imitate sounds (buzz, hiss, crash)."
        ),
    },
    {
        "id": "eng_ss2_lexis_structure",
        "subject": "English Language",
        "grade": "SS2",
        "topic": "Lexis and Structure",
        "content": (
            "Lexis and Structure tests vocabulary and grammar, usually in the objective test paper. "
            "Synonyms are words with similar meanings (e.g. happy/glad); antonyms are opposites (e.g. hot/cold). "
            "Idioms are fixed expressions whose meaning differs from the literal words, e.g. 'kick the bucket' "
            "means to die. "
            "Register is the level of formality used for a given audience — formal register avoids slang and "
            "contractions. "
            "Active voice has the subject performing the action (The boy kicked the ball); passive voice has "
            "the subject receiving the action (The ball was kicked by the boy). "
            "Direct speech quotes exact words ('I am tired,' she said); indirect speech restates them without "
            "quotation marks and shifts tense backward (She said she was tired). "
            "Concord means subject-verb agreement: singular subjects take singular verbs (He goes), plural "
            "subjects take plural verbs (They go)."
        ),
    },

    # =========== CIVIC EDUCATION ===========
    {
        "id": "civ_ss1_citizenship",
        "subject": "Civic Education",
        "grade": "SS1",
        "topic": "Citizenship",
        "content": (
            "A citizen is a legal member of a country entitled to its rights and bound by its duties. "
            "Nigeria recognises citizenship by birth, registration, or naturalisation. "
            "Citizenship by birth applies to those born in Nigeria to Nigerian parents. "
            "Naturalisation is granted to a qualified foreigner after meeting residency and character requirements. "
            "Duties of a citizen include obeying the law, paying taxes, and voting responsibly."
        ),
    },
    {
        "id": "civ_ss1_national_values",
        "subject": "Civic Education",
        "grade": "SS1",
        "topic": "National Values",
        "content": (
            "National values are shared ideals that unite the citizens of a country. "
            "Nigeria's core national values include discipline, integrity, dignity of labour, social justice, "
            "religious tolerance, self-reliance, and patriotism. "
            "These values are promoted through the National Orientation Agency and the school curriculum. "
            "Upholding national values reduces corruption and strengthens national unity."
        ),
    },
    {
        "id": "civ_ss1_democracy",
        "subject": "Civic Education",
        "grade": "SS1",
        "topic": "Democracy",
        "content": (
            "Democracy is a system of government where power belongs to the people, exercised directly "
            "or through elected representatives. Abraham Lincoln described it as government of the people, "
            "by the people, for the people. Features of democracy include free and fair elections, "
            "rule of law, separation of powers, and respect for human rights. "
            "Nigeria practises a presidential representative democracy since the Fourth Republic began in 1999."
        ),
    },
    {
        "id": "civ_ss1_constitution",
        "subject": "Civic Education",
        "grade": "SS1",
        "topic": "The Constitution",
        "content": (
            "A constitution is the supreme law of a country, setting out how it is governed. "
            "Nigeria's current constitution is the 1999 Constitution (as amended). "
            "It establishes three arms of government: the Executive, the Legislature, and the Judiciary. "
            "It also guarantees fundamental human rights in Chapter IV, such as the right to life, "
            "dignity of the human person, personal liberty, and freedom of expression."
        ),
    },
    {
        "id": "civ_ss1_three_arms",
        "subject": "Civic Education",
        "grade": "SS1",
        "topic": "The Three Arms of Government",
        "content": (
            "The Executive implements laws and is headed by the President at the federal level. "
            "The Legislature makes laws; Nigeria's National Assembly has two chambers, the Senate and the "
            "House of Representatives. The Judiciary interprets laws and settles disputes, headed by the "
            "Supreme Court. Separation of powers between these arms prevents any single arm from becoming "
            "too powerful, supported by a system of checks and balances."
        ),
    },
    {
        "id": "civ_ss2_human_rights",
        "subject": "Civic Education",
        "grade": "SS2",
        "topic": "Human Rights",
        "content": (
            "Human rights are entitlements every person has simply by being human, regardless of nationality. "
            "They include civil rights (life, liberty, fair trial), political rights (vote, free speech), "
            "and socio-economic rights (education, health, work). "
            "The Universal Declaration of Human Rights (1948) is the foundational international document. "
            "In Nigeria, human rights are enforced through the courts and bodies like the National Human Rights Commission."
        ),
    },
    {
        "id": "civ_ss2_electoral_process",
        "subject": "Civic Education",
        "grade": "SS2",
        "topic": "The Electoral Process",
        "content": (
            "An election is the formal process of choosing leaders by voting. "
            "In Nigeria, the Independent National Electoral Commission (INEC) organises elections. "
            "Stages include voter registration, party primaries, campaigns, voting, and collation of results. "
            "Features of a credible election include secrecy of the ballot, transparency, and freedom from violence or rigging. "
            "Permanent Voter Cards (PVC) are required to vote in Nigerian elections."
        ),
    },
    {
        "id": "civ_ss2_rule_of_law",
        "subject": "Civic Education",
        "grade": "SS2",
        "topic": "Rule of Law",
        "content": (
            "The rule of law means everyone, including government officials, is subject to and accountable "
            "under the law, and no one is above it. "
            "Its principles include equality before the law, supremacy of the law over arbitrary power, "
            "and the right to fair hearing. "
            "The rule of law protects citizens from abuse of power and supports democracy and good governance."
        ),
    },
    {
        "id": "civ_ss2_federalism",
        "subject": "Civic Education",
        "grade": "SS2",
        "topic": "Federalism",
        "content": (
            "Federalism is a system where power is constitutionally shared between a central government "
            "and constituent states or regions. "
            "Nigeria operates a federal system with three tiers: federal, state, and local government. "
            "The Exclusive Legislative List covers matters only the federal government can legislate on "
            "(e.g. defence, currency), while the Concurrent List covers matters both federal and state "
            "governments can legislate on (e.g. education, health)."
        ),
    },
    {
        "id": "civ_ss3_corruption",
        "subject": "Civic Education",
        "grade": "SS3",
        "topic": "Corruption and Anti-Corruption Agencies",
        "content": (
            "Corruption is the abuse of entrusted power for private gain, including bribery, embezzlement, "
            "and nepotism. It weakens institutions, discourages investment, and worsens poverty. "
            "Nigeria's main anti-corruption agencies are the EFCC (Economic and Financial Crimes Commission) "
            "and the ICPC (Independent Corrupt Practices and Other Related Offences Commission). "
            "Whistleblowing, transparency, and strong institutions help curb corruption."
        ),
    },
    {
        "id": "civ_ss3_drug_abuse",
        "subject": "Civic Education",
        "grade": "SS3",
        "topic": "Drug Abuse and Trafficking",
        "content": (
            "Drug abuse is the harmful or excessive use of substances such as cocaine, heroin, tramadol, "
            "and cannabis outside of medical supervision. "
            "Effects include addiction, mental health disorders, poor academic performance, and crime. "
            "The National Drug Law Enforcement Agency (NDLEA) is responsible for combating drug trafficking "
            "and abuse in Nigeria. Prevention strategies include education, counselling, and community support."
        ),
    },
    {
        "id": "civ_ss3_consumer_rights",
        "subject": "Civic Education",
        "grade": "SS3",
        "topic": "Consumer Rights and Responsibilities",
        "content": (
            "A consumer is anyone who buys or uses goods and services. "
            "Consumer rights include the right to safety, to be informed, to choose, and to be heard. "
            "Consumer responsibilities include reading instructions carefully and reporting faulty goods. "
            "In Nigeria, the Federal Competition and Consumer Protection Commission (FCCPC) protects consumers "
            "from exploitation, unsafe products, and unfair trade practices."
        ),
    },

    # =========== FURTHER MATHEMATICS ===========
    {
        "id": "furthermaths_ss1_sets",
        "subject": "Further Mathematics",
        "grade": "SS1",
        "topic": "Sets",
        "content": (
            "A set is a well-defined collection of distinct objects, called elements. "
            "Union (A ∪ B) combines all elements in A or B. Intersection (A ∩ B) contains elements in both. "
            "The complement (A') contains elements in the universal set but not in A. "
            "Venn diagrams visually represent set relationships. "
            "For finite sets, n(A ∪ B) = n(A) + n(B) − n(A ∩ B)."
        ),
    },
    {
        "id": "furthermaths_ss1_surds",
        "subject": "Further Mathematics",
        "grade": "SS1",
        "topic": "Surds and Indices",
        "content": (
            "A surd is an irrational root that cannot be simplified to a whole number, e.g. √2, √3. "
            "Rationalising the denominator removes surds from the bottom of a fraction by multiplying by "
            "the conjugate, e.g. 1/(√2) becomes √2/2. "
            "Laws of indices: a^m × a^n = a^(m+n); a^m ÷ a^n = a^(m−n); (a^m)^n = a^(mn); a^0 = 1. "
            "Surds combine only when they share the same radicand: 2√3 + 5√3 = 7√3."
        ),
    },
    {
        "id": "furthermaths_ss1_polynomials",
        "subject": "Further Mathematics",
        "grade": "SS1",
        "topic": "Polynomials",
        "content": (
            "A polynomial is an expression with terms of non-negative integer powers of a variable. "
            "The Remainder Theorem states that dividing a polynomial f(x) by (x − a) leaves a remainder of f(a). "
            "The Factor Theorem states that (x − a) is a factor of f(x) if and only if f(a) = 0. "
            "These theorems help factorise cubic and higher-degree polynomials without long division."
        ),
    },
    {
        "id": "furthermaths_ss2_sequences_series",
        "subject": "Further Mathematics",
        "grade": "SS2",
        "topic": "Sequences and Series",
        "content": (
            "An arithmetic progression (AP) has a common difference d between terms: nth term = a + (n−1)d. "
            "Sum of n terms of an AP: Sn = n/2 [2a + (n−1)d]. "
            "A geometric progression (GP) has a common ratio r: nth term = ar^(n−1). "
            "Sum of n terms of a GP: Sn = a(1 − r^n)/(1 − r) for r ≠ 1. "
            "Sum to infinity of a GP (|r| < 1): S∞ = a/(1 − r)."
        ),
    },
    {
        "id": "furthermaths_ss2_matrices",
        "subject": "Further Mathematics",
        "grade": "SS2",
        "topic": "Matrices",
        "content": (
            "A matrix is a rectangular array of numbers arranged in rows and columns. "
            "Matrices can be added or subtracted only if they have the same dimensions, element by element. "
            "Matrix multiplication requires the number of columns in the first matrix to equal the number "
            "of rows in the second. "
            "For a 2×2 matrix [[a,b],[c,d]], the determinant is ad − bc, and the inverse exists only if "
            "the determinant is not zero."
        ),
    },
    {
        "id": "furthermaths_ss2_differentiation",
        "subject": "Further Mathematics",
        "grade": "SS2",
        "topic": "Differentiation",
        "content": (
            "Differentiation finds the rate of change (gradient) of a function. "
            "Power rule: if y = x^n, then dy/dx = nx^(n−1). "
            "The derivative of a constant is zero; the derivative of a sum is the sum of derivatives. "
            "Stationary points occur where dy/dx = 0, found by setting the first derivative to zero. "
            "The second derivative determines whether a stationary point is a maximum or minimum."
        ),
    },
    {
        "id": "furthermaths_ss2_integration",
        "subject": "Further Mathematics",
        "grade": "SS2",
        "topic": "Integration",
        "content": (
            "Integration is the reverse process of differentiation, used to find areas under curves. "
            "Power rule for integration: ∫x^n dx = x^(n+1)/(n+1) + C, for n ≠ −1. "
            "Definite integrals (with limits a and b) give a numerical value, often representing area. "
            "Indefinite integrals include an arbitrary constant C since differentiation of a constant is zero."
        ),
    },
    {
        "id": "furthermaths_ss3_vectors",
        "subject": "Further Mathematics",
        "grade": "SS3",
        "topic": "Vectors",
        "content": (
            "A vector has both magnitude and direction, unlike a scalar which has magnitude only. "
            "Vectors can be added tip-to-tail or by adding corresponding components. "
            "The magnitude of vector (x, y) is √(x² + y²). "
            "The dot product of two vectors a·b = |a||b|cosθ is used to find the angle between them. "
            "Unit vectors i and j represent one unit along the x-axis and y-axis respectively."
        ),
    },
    {
        "id": "furthermaths_ss3_complex_numbers",
        "subject": "Further Mathematics",
        "grade": "SS3",
        "topic": "Complex Numbers",
        "content": (
            "A complex number has the form a + bi, where i² = −1. "
            "'a' is the real part and 'b' is the imaginary part. "
            "Complex numbers are added/subtracted by combining real and imaginary parts separately. "
            "The modulus of a + bi is √(a² + b²), representing its distance from the origin on an Argand diagram. "
            "The conjugate of a + bi is a − bi, used to simplify division of complex numbers."
        ),
    },
    {
        "id": "furthermaths_ss3_permutation_combination",
        "subject": "Further Mathematics",
        "grade": "SS3",
        "topic": "Permutation and Combination",
        "content": (
            "Permutation counts arrangements where order matters: nPr = n!/(n−r)!. "
            "Combination counts selections where order does not matter: nCr = n!/[r!(n−r)!]. "
            "Factorial notation: n! = n × (n−1) × (n−2) × ... × 1, with 0! defined as 1. "
            "Use permutations for arranging items (e.g. seating order) and combinations for choosing groups "
            "(e.g. selecting a committee)."
        ),
    },
    {
        "id": "furthermaths_ss3_probability",
        "subject": "Further Mathematics",
        "grade": "SS3",
        "topic": "Probability",
        "content": (
            "Probability measures the likelihood of an event, ranging from 0 (impossible) to 1 (certain). "
            "P(A) = number of favourable outcomes / total possible outcomes. "
            "For independent events, P(A and B) = P(A) × P(B). "
            "For mutually exclusive events, P(A or B) = P(A) + P(B). "
            "A probability tree diagram helps visualise combined and conditional probabilities across stages."
        ),
    },
    {
        "id": "furthermaths_ss2_trigonometry",
        "subject": "Further Mathematics",
        "grade": "SS2",
        "topic": "Trigonometry",
        "content": (
            "Compound angle formulae: sin(A±B) = sinAcosB ± cosAsinB; cos(A±B) = cosAcosB ∓ sinAsinB. "
            "Double angle formulae: sin2A = 2sinAcosA; cos2A = cos²A − sin²A = 1 − 2sin²A = 2cos²A − 1. "
            "The general solution of trig equations adds multiples of the period (360° or 2π radians) "
            "to the principal solution found within one cycle. "
            "R-formula: a sinθ + b cosθ can be rewritten as R sin(θ + α), where R = √(a² + b²), "
            "useful for finding maximum/minimum values and solving equations."
        ),
    },
    {
        "id": "furthermaths_ss3_coordinate_geometry",
        "subject": "Further Mathematics",
        "grade": "SS3",
        "topic": "Coordinate Geometry (Conic Sections)",
        "content": (
            "A conic section is a curve formed by the intersection of a plane and a cone. "
            "A circle centred at (a,b) with radius r has equation (x−a)² + (y−b)² = r². "
            "A parabola y² = 4ax opens rightward with focus (a,0) and directrix x = −a. "
            "An ellipse x²/a² + y²/b² = 1 has two foci; eccentricity e < 1 measures how stretched it is. "
            "A hyperbola x²/a² − y²/b² = 1 has two separate branches and asymptotes y = ±(b/a)x."
        ),
    },
    {
        "id": "furthermaths_ss3_mechanics",
        "subject": "Further Mathematics",
        "grade": "SS3",
        "topic": "Kinematics (Mechanics)",
        "content": (
            "Kinematics studies motion without considering its causes. "
            "The equations of motion for constant acceleration: v = u + at; s = ut + ½at²; v² = u² + 2as, "
            "where u is initial velocity, v is final velocity, a is acceleration, s is displacement, t is time. "
            "Velocity is the rate of change of displacement; acceleration is the rate of change of velocity. "
            "A velocity-time graph's gradient gives acceleration, and the area under it gives displacement."
        ),
    },

    # =========== ECONOMICS ===========
    {
        "id": "econ_ss1_basic_concepts",
        "subject": "Economics",
        "grade": "SS1",
        "topic": "Basic Economic Concepts",
        "content": (
            "Economics studies how scarce resources are allocated to satisfy unlimited human wants. "
            "Scarcity is the basic economic problem — resources are limited but wants are unlimited. "
            "Opportunity cost is the value of the next best alternative given up when a choice is made. "
            "The four factors of production are land (natural resources), labour (human effort), capital "
            "(man-made resources like machinery), and entrepreneurship (organizing the other factors, "
            "bearing risk). "
            "Every economy must decide what to produce, how to produce, and for whom to produce."
        ),
    },
    {
        "id": "econ_ss1_demand_supply",
        "subject": "Economics",
        "grade": "SS1",
        "topic": "Demand and Supply",
        "content": (
            "The law of demand states that as price rises, quantity demanded falls, all else being equal — "
            "shown as a downward-sloping demand curve. "
            "The law of supply states that as price rises, quantity supplied rises — shown as an "
            "upward-sloping supply curve. "
            "Equilibrium price is where the demand and supply curves intersect — quantity demanded equals "
            "quantity supplied. "
            "A shift in a curve (caused by income, taste, or input costs) differs from a movement along the "
            "curve (caused only by price change). "
            "Elasticity of demand measures how responsive quantity demanded is to a price change."
        ),
    },
    {
        "id": "econ_ss2_market_structures",
        "subject": "Economics",
        "grade": "SS2",
        "topic": "Market Structures",
        "content": (
            "Perfect competition has many buyers and sellers, identical products, and no single firm can "
            "influence price. "
            "Monopoly has a single seller controlling the entire market, with high barriers to entry, "
            "allowing the firm to set prices. "
            "Oligopoly has a few large firms dominating the market, often with interdependent pricing decisions. "
            "Monopolistic competition has many sellers with slightly differentiated products, e.g. branded goods. "
            "Market structure affects pricing power, competition, and consumer choice."
        ),
    },
    {
        "id": "econ_ss2_money_banking",
        "subject": "Economics",
        "grade": "SS2",
        "topic": "Money and Banking",
        "content": (
            "Money functions as a medium of exchange, a store of value, a unit of account, and a standard "
            "for deferred payment. "
            "Commercial banks accept deposits, give loans, and provide payment services to individuals and "
            "businesses. "
            "The Central Bank (in Nigeria, the CBN) controls the money supply, regulates commercial banks, "
            "issues currency, and manages monetary policy. "
            "Monetary policy tools include the interest rate (Monetary Policy Rate), reserve requirements, "
            "and open market operations. "
            "Inflation is a general and sustained rise in the price level over time, reducing money's "
            "purchasing power."
        ),
    },
    {
        "id": "econ_ss3_national_income",
        "subject": "Economics",
        "grade": "SS3",
        "topic": "National Income",
        "content": (
            "National income measures the total value of goods and services produced in an economy over a "
            "period. "
            "GDP (Gross Domestic Product) is the value of output produced within a country's borders; GNP "
            "(Gross National Product) adds income earned abroad by citizens and subtracts income earned "
            "domestically by foreigners. "
            "National income can be measured three ways: the output method (sum of value added), the income "
            "method (sum of wages, rent, interest, profit), and the expenditure method (sum of consumption, "
            "investment, government spending, net exports). "
            "Per capita income divides national income by population, indicating average living standards."
        ),
    },

    # =========== GOVERNMENT ===========
    {
        "id": "gov_ss1_concepts",
        "subject": "Government",
        "grade": "SS1",
        "topic": "Basic Concepts in Government",
        "content": (
            "A state is a political community occupying a defined territory, with sovereignty, a government, "
            "and a permanent population. "
            "Government is the machinery or institutions through which the state's will is expressed and "
            "implemented. "
            "Sovereignty is the supreme authority of a state to govern itself without external interference — "
            "it can be internal (control within borders) or external (independence from other states). "
            "Power is the ability to influence or control others; authority is power recognized as "
            "legitimate; legitimacy is when people accept a government's right to rule."
        ),
    },
    {
        "id": "gov_ss1_arms_of_govt",
        "subject": "Government",
        "grade": "SS1",
        "topic": "Arms of Government",
        "content": (
            "The Executive implements and enforces laws — headed by the President (presidential system) or "
            "Prime Minister (parliamentary system). "
            "The Legislature makes laws — in Nigeria, the National Assembly (Senate and House of "
            "Representatives). "
            "The Judiciary interprets laws and administers justice, headed by the courts. "
            "Separation of powers keeps these three arms distinct so no single arm dominates. "
            "Checks and balances allow each arm to limit the powers of the others, e.g. the legislature can "
            "override a presidential veto, and courts can rule laws unconstitutional."
        ),
    },
    {
        "id": "gov_ss2_systems_of_govt",
        "subject": "Government",
        "grade": "SS2",
        "topic": "Systems of Government",
        "content": (
            "A federal system divides power between a central government and regional/state governments, "
            "each with defined powers, e.g. Nigeria, USA. "
            "A unitary system concentrates power in a central government, which may delegate some powers to "
            "local units, e.g. UK, France. "
            "A confederation is a loose union of independent states that retain most sovereignty. "
            "In a presidential system, the President is both head of state and head of government, elected "
            "separately from the legislature, e.g. Nigeria, USA. "
            "In a parliamentary system, the Prime Minister is head of government, drawn from and accountable "
            "to the legislature, e.g. UK."
        ),
    },
    {
        "id": "gov_ss2_constitution",
        "subject": "Government",
        "grade": "SS2",
        "topic": "The Constitution",
        "content": (
            "A constitution is the supreme law that establishes how a state is governed, defining the powers "
            "and structure of government and citizens' rights. "
            "A written constitution is a single codified document, e.g. Nigeria's 1999 Constitution; an "
            "unwritten constitution is based on conventions, statutes, and precedents, e.g. the UK. "
            "A rigid constitution is difficult to amend, requiring special procedures; a flexible "
            "constitution can be changed through ordinary legislation. "
            "Sources of a constitution include historical documents, judicial precedents, conventions, and "
            "statutes. "
            "Constitutionalism means government operates within limits set by the constitution, not by "
            "arbitrary rule."
        ),
    },
    {
        "id": "gov_ss3_political_parties",
        "subject": "Government",
        "grade": "SS3",
        "topic": "Political Parties and Pressure Groups",
        "content": (
            "A political party is an organized group that seeks to win elections and control government by "
            "presenting candidates and policies to voters. "
            "Functions of political parties include political education, candidate selection, policy "
            "formulation, and forming government or opposition. "
            "A pressure group seeks to influence government policy without seeking to win elections or hold "
            "office directly, e.g. trade unions, professional associations. "
            "Pressure groups differ from political parties because they focus on specific interests rather "
            "than governing broadly. "
            "A one-party system has a single legal party; a multi-party system allows several parties to "
            "compete for power."
        ),
    },

    # =========== LITERATURE IN ENGLISH ===========
    {
        "id": "lit_ss1_genres",
        "subject": "Literature in English",
        "grade": "SS1",
        "topic": "Genres of Literature",
        "content": (
            "Prose is written in ordinary sentences and paragraphs, without a regular rhythmic structure — "
            "includes novels and short stories. "
            "Drama is literature written to be performed, structured in acts and scenes, driven mainly by "
            "dialogue. "
            "Poetry uses condensed, rhythmic, and often figurative language, arranged in lines and stanzas, "
            "to express ideas and emotion. "
            "Each genre is examined through set texts prescribed by WAEC, which change periodically, so "
            "students must know the specific texts assigned for their examination year. "
            "All three genres can share literary devices like symbolism, irony, and imagery, but differ in "
            "form and structure."
        ),
    },
    {
        "id": "lit_ss1_poetic_devices",
        "subject": "Literature in English",
        "grade": "SS1",
        "topic": "Elements of Poetry",
        "content": (
            "Theme is the central idea or message of a poem. "
            "Tone is the poet's attitude toward the subject (e.g. mocking, solemn, celebratory); mood is the "
            "emotional atmosphere created for the reader. "
            "Imagery uses descriptive, sensory language to create mental pictures. "
            "Rhyme is the repetition of similar sounds, usually at the end of lines; rhythm is the pattern "
            "of stressed and unstressed syllables. "
            "A persona is the voice or character through which the poem speaks, which may differ from the "
            "poet's own voice. "
            "A stanza is a poem's grouped lines, similar to a paragraph in prose."
        ),
    },
    {
        "id": "lit_ss2_drama_elements",
        "subject": "Literature in English",
        "grade": "SS2",
        "topic": "Elements of Drama",
        "content": (
            "Plot is the sequence of events in a play, usually structured as exposition, rising action, "
            "climax, falling action, and resolution. "
            "Characterization is how a playwright develops and reveals character, through dialogue, action, "
            "and other characters' reactions. "
            "Setting is the time and place in which the action occurs. "
            "Dramatic irony occurs when the audience knows something a character does not. "
            "A soliloquy is a speech a character delivers alone on stage, revealing inner thoughts to the "
            "audience. "
            "Conflict — the struggle between opposing forces — drives the plot forward."
        ),
    },
    {
        "id": "lit_ss2_prose_elements",
        "subject": "Literature in English",
        "grade": "SS2",
        "topic": "Elements of Prose Fiction",
        "content": (
            "Plot structure follows exposition, rising action, climax, falling action, and "
            "resolution/denouement. "
            "Characterization can be direct (the narrator states traits) or indirect (traits shown through "
            "action, speech, thought). "
            "Point of view is the narrative perspective: first person (I), third person limited (he/she, one "
            "character's thoughts), or third person omniscient (all characters' thoughts known). "
            "Setting establishes time, place, and social context, often shaping mood and theme. "
            "Theme is the underlying message or central idea the writer explores through the story."
        ),
    },
    {
        "id": "lit_ss3_literary_appreciation",
        "subject": "Literature in English",
        "grade": "SS3",
        "topic": "Literary Appreciation and Criticism",
        "content": (
            "Literary appreciation involves analysing a text's theme, characters, setting, structure, and "
            "stylistic devices to understand the writer's intent and craft. "
            "When analysing a character, consider their actions, relationships, development, and role in "
            "advancing the theme. "
            "When identifying theme, look for ideas the text returns to repeatedly across events and "
            "characters. "
            "Stylistic devices (symbolism, irony, foreshadowing, flashback) should be identified with "
            "textual evidence — always reference specific scenes or events. "
            "WAEC's prescribed texts change periodically (roughly every five years), so students must study "
            "the current set texts for their examination year, not older ones."
        ),
    },

    # =========== FINANCIAL ACCOUNTING ===========
    {
        "id": "finacc_ss1_basics",
        "subject": "Financial Accounting",
        "grade": "SS1",
        "topic": "Basic Accounting Concepts",
        "content": (
            "The accounting equation is: Assets = Liabilities + Capital (Owner's Equity). "
            "Double-entry bookkeeping records every transaction in at least two accounts — a debit in one "
            "and a credit in another — keeping the equation balanced. "
            "Debit entries increase asset and expense accounts, and decrease liability, capital, and income "
            "accounts; credit entries do the opposite. "
            "Source documents (invoices, receipts, cheques) provide evidence for recording transactions. "
            "The accounting cycle flows: source documents to journal (day books) to ledger to trial balance "
            "to final accounts."
        ),
    },
    {
        "id": "finacc_ss1_ledger_trial_balance",
        "subject": "Financial Accounting",
        "grade": "SS1",
        "topic": "Ledger Accounts and Trial Balance",
        "content": (
            "A ledger account records all transactions affecting a particular item (e.g. cash, sales, a "
            "specific customer), with debits on the left and credits on the right. "
            "Posting transfers entries from the journal (day books) to the appropriate ledger accounts. "
            "Balancing an account finds the difference between its debit and credit totals to determine its "
            "closing balance. "
            "A trial balance lists all ledger account balances to check that total debits equal total "
            "credits, helping detect certain recording errors — though it cannot detect all types of error, "
            "such as an error of omission."
        ),
    },
    {
        "id": "finacc_ss2_final_accounts",
        "subject": "Financial Accounting",
        "grade": "SS2",
        "topic": "Trading, Profit and Loss Account and Balance Sheet",
        "content": (
            "The Trading Account calculates gross profit: Sales minus Cost of Goods Sold (Opening Stock + "
            "Purchases − Closing Stock). "
            "The Profit and Loss Account calculates net profit: Gross Profit plus other income, minus "
            "operating expenses (rent, salaries, utilities). "
            "The Balance Sheet is a snapshot of a business's financial position at a point in time, listing "
            "assets (fixed and current), liabilities (long-term and current), and capital. "
            "Fixed assets (buildings, equipment) are used long-term; current assets (cash, stock, debtors) "
            "are used or converted to cash within a year."
        ),
    },
    {
        "id": "finacc_ss2_depreciation",
        "subject": "Financial Accounting",
        "grade": "SS2",
        "topic": "Depreciation and Provision for Bad Debts",
        "content": (
            "Depreciation is the systematic allocation of a fixed asset's cost over its useful life, "
            "reflecting wear and tear or obsolescence. "
            "The straight-line method spreads depreciation equally each year: (Cost − Residual Value) / "
            "Useful Life. "
            "The reducing balance method applies a fixed percentage to the asset's remaining book value each "
            "year, so depreciation is highest in early years. "
            "A provision for bad debts anticipates debtors who may not pay, usually a percentage of "
            "outstanding debtors, and is deducted from debtors on the balance sheet. "
            "Writing off a bad debt removes it entirely from the books as an expense once confirmed "
            "unrecoverable."
        ),
    },

    # =========== COMMERCE ===========
    {
        "id": "comm_ss1_basics",
        "subject": "Commerce",
        "grade": "SS1",
        "topic": "Introduction to Commerce",
        "content": (
            "Commerce is the exchange and distribution of goods and services, including trade and the aids "
            "to trade that make trade possible. "
            "Trade is the buying and selling of goods — home trade (within a country: wholesale and retail) "
            "and foreign trade (import, export, and entrepot trade between countries). "
            "Aids to trade include banking (finance), insurance (risk protection), transportation (moving "
            "goods), communication (information exchange), warehousing (storage), and advertising "
            "(promotion). "
            "Industry produces goods (extractive, manufacturing, constructive); commerce distributes them; "
            "trade is the direct exchange within commerce."
        ),
    },
    {
        "id": "comm_ss2_channels_distribution",
        "subject": "Commerce",
        "grade": "SS2",
        "topic": "Channels of Distribution",
        "content": (
            "A channel of distribution is the path goods take from producer to final consumer. "
            "A wholesaler buys goods in bulk from producers and sells smaller quantities to retailers, "
            "breaking bulk and providing storage. "
            "A retailer buys from wholesalers (or sometimes producers) and sells directly to final consumers "
            "in small quantities. "
            "Direct distribution sells straight from producer to consumer, skipping intermediaries, e.g. "
            "farm produce sold at a farm gate. "
            "Choice of channel depends on the product type, market size, and cost — perishable goods often "
            "use shorter channels."
        ),
    },

    # =========== AGRICULTURAL SCIENCE ===========
    {
        "id": "agric_ss1_meaning_importance",
        "subject": "Agricultural Science",
        "grade": "SS1",
        "topic": "Meaning and Importance of Agriculture",
        "content": (
            "Agriculture is the science and practice of growing crops and rearing animals for food, "
            "raw materials, and income. It can be subsistence (small-scale, mainly for the farmer's own "
            "family) or commercial (large-scale, produced mainly for sale). "
            "Agriculture matters to the individual as a source of food and income, to the community as a "
            "source of employment and raw materials for local industry, and to the nation as a source of "
            "foreign exchange and food security. "
            "Common problems facing agricultural development include poor land tenure systems, inadequate "
            "finance, poor transportation and storage facilities, and low use of improved tools and inputs. "
            "Government supports agriculture through credit and subsidy schemes, agricultural extension "
            "services, and policies on land use."
        ),
    },
    {
        "id": "agric_ss1_soil",
        "subject": "Agricultural Science",
        "grade": "SS1",
        "topic": "Soil Formation and Properties",
        "content": (
            "Soil is formed from the weathering of parent rock, influenced by climate, organisms, "
            "topography, and time. Physical weathering breaks rock down mechanically; chemical weathering "
            "breaks it down through chemical reactions. "
            "A soil profile shows horizontal layers (horizons) from the surface down to the parent rock. "
            "Soil texture refers to the proportion of sand, silt, and clay particles, while soil structure "
            "describes how these particles clump together. "
            "Soil contains macronutrients and micronutrients needed by plants; nutrients are lost through "
            "leaching, crop removal, and erosion, and can be replenished by crop rotation, organic manuring, "
            "fertilizer application, and fallowing."
        ),
    },
    {
        "id": "agric_ss1_farm_tools",
        "subject": "Agricultural Science",
        "grade": "SS1",
        "topic": "Farm Tools and Machinery",
        "content": (
            "Simple farm tools include the cutlass, hoe, spade, and shovel, used for basic manual farm "
            "operations and requiring regular cleaning and sharpening to maintain. "
            "Farm machinery includes tractors, which can be fitted with implements such as ploughs, "
            "harrows, ridgers, planters, and sprayers to mechanize land preparation and planting. "
            "Agricultural mechanization is the use of machines to replace or supplement manual and animal "
            "labour on the farm; it increases the speed and scale of farm work but requires capital, fuel, "
            "and skilled maintenance. "
            "Regular maintenance — checking oil and water levels, servicing, and keeping machines clean — "
            "extends the working life of farm machinery and prevents breakdowns during critical farm "
            "operations."
        ),
    },
    {
        "id": "agric_ss2_crop_classification",
        "subject": "Agricultural Science",
        "grade": "SS2",
        "topic": "Classification and Production of Crops",
        "content": (
            "Crops can be classified by use (cereals, pulses, roots and tubers, vegetables, fruits), by "
            "life cycle (annual, biennial, perennial), or by morphology (monocotyledonous or dicotyledonous). "
            "Growing any crop successfully requires attention to climatic and soil requirements, land "
            "preparation, the right planting date and spacing, manuring and fertilizer application, weeding, "
            "and pest and disease control through to harvest and storage. "
            "Examples by group: cereals include maize and rice; pulses include cowpea and soya bean; roots "
            "and tubers include cassava and yam; oil crops include groundnut and oil palm. "
            "Crop improvement raises yield and quality through introduction of new varieties, selection of "
            "the best-performing plants, and controlled breeding based on Mendel's laws of inheritance."
        ),
    },
    {
        "id": "agric_ss2_pests_diseases_weeds",
        "subject": "Agricultural Science",
        "grade": "SS2",
        "topic": "Pests, Diseases, and Weeds",
        "content": (
            "A crop pest is any organism that damages crops and reduces yield; pests are classified as "
            "insect pests (grouped by mouth part — biting/chewing, piercing/sucking, or boring) and "
            "non-insect pests such as birds and rodents. "
            "Crop diseases are caused by organisms such as fungi, bacteria, and viruses, each with its own "
            "mode of transmission and symptoms — for example, cassava mosaic virus stunts and mottles "
            "cassava leaves. "
            "Weeds are unwanted plants that compete with crops for light, water, nutrients, and space, "
            "reducing yield and increasing the cost of production. "
            "Control methods for pests, diseases, and weeds fall into cultural (e.g. crop rotation), "
            "biological (using natural enemies), chemical (pesticides, fungicides, herbicides), and physical "
            "or mechanical methods (hand-picking, hand-weeding); chemical control can pollute the "
            "environment if misused."
        ),
    },
    {
        "id": "agric_ss2_animal_production",
        "subject": "Agricultural Science",
        "grade": "SS2",
        "topic": "Animal Production and Livestock Management",
        "content": (
            "Farm animals are classified by habitat (terrestrial or aquatic) and by use (food, work, pets). "
            "Livestock management covers housing, feeding, hygiene, and finishing an animal from birth to "
            "market weight; good management improves growth rate and productivity. "
            "Animal nutrition requires a balanced diet supplying energy, protein, vitamins, and minerals; "
            "poor nutrition causes malnutrition, reducing growth, milk yield, or egg production. "
            "Common livestock diseases include viral diseases like foot-and-mouth disease and Newcastle "
            "disease, bacterial diseases like anthrax, and parasitic infections from ticks and worms; "
            "prevention relies on quarantine, vaccination/immunization, and good hygiene. "
            "Animal improvement uses introduction of better breeds, selection, and breeding — including "
            "artificial insemination — to raise productivity."
        ),
    },
    {
        "id": "agric_ss3_agric_economics",
        "subject": "Agricultural Science",
        "grade": "SS3",
        "topic": "Agricultural Economics",
        "content": (
            "The basic economic principles underlying agriculture are scarcity, choice, scale of "
            "preference, and the law of diminishing returns. "
            "The factors of production are land, labour, capital, and management (the entrepreneur), each "
            "contributing differently to farm output. "
            "Demand is the quantity of a farm product buyers are willing and able to buy at a given price; "
            "supply is the quantity producers are willing to sell. The law of demand states that as price "
            "rises, quantity demanded falls, all else equal; the law of supply states the opposite "
            "relationship for sellers. "
            "Farm records — including inventory, production, and income-and-expenditure records — help a "
            "farm manager track performance and plan; farm accounts summarize this into a profit-and-loss "
            "account and a balance sheet."
        ),
    },
    {
        "id": "agric_ss3_finance_extension",
        "subject": "Agricultural Science",
        "grade": "SS3",
        "topic": "Agricultural Finance and Extension",
        "content": (
            "Agricultural finance is money made available to fund farm operations; farm credit is "
            "classified by length of time (short-, medium-, or long-term) and by source (institutional, "
            "such as banks, or non-institutional, such as friends and cooperatives). "
            "Farmers seeking credit often face high interest rates and lack of collateral, while lending "
            "institutions face the problem of farmers keeping poor records and accounts. "
            "Agricultural insurance protects farmers against losses from natural disasters, pests, and "
            "disease outbreaks by covering crops, livestock, and farm property. "
            "Agricultural extension is the process of transferring research-based knowledge to farmers "
            "through individual or group contact methods; in Nigeria this is delivered through programmes "
            "like the Agricultural Development Programme (ADP), though illiteracy and poor transport limit "
            "its reach in rural areas."
        ),
    },

    # =========== GEOGRAPHY ===========
    {
        "id": "geo_ss1_map_reading",
        "subject": "Geography",
        "grade": "SS1",
        "topic": "Map Reading and Practical Geography",
        "content": (
            "Map reading involves interpreting a contoured survey map to identify physical features (such "
            "as valleys and hills) and cultural or human features (such as settlements and roads). "
            "Scale relates distance on a map to actual distance on the ground and is used to measure real "
            "distances and to enlarge or reduce a map. "
            "Direction on a map is described using bearings, measured clockwise from north in degrees, and "
            "contour lines join points of equal height, with closely spaced lines showing steep slopes. "
            "Statistical data about a place can be shown visually using bar graphs, line graphs, dot maps, "
            "and proportional circles, making patterns like population distribution easier to compare."
        ),
    },
    {
        "id": "geo_ss1_earth_rocks",
        "subject": "Geography",
        "grade": "SS1",
        "topic": "The Earth, Rocks, and Landforms",
        "content": (
            "The earth rotates on its axis once approximately every 24 hours, causing day and night, and "
            "revolves around the sun once a year, which — combined with the tilt of its axis — causes the "
            "seasons. "
            "Rocks are classified into three types: igneous rocks form as molten magma cools and "
            "solidifies; sedimentary rocks form from compressed layers of sediment; metamorphic rocks form "
            "when existing rock is transformed by heat and pressure. "
            "Tectonic processes such as vulcanicity and earthquakes build landforms like mountains, while "
            "denudational processes — weathering, running water, wind, and waves — wear landforms down over "
            "time. "
            "Major landform types include mountains, plains, and coastal landforms, each shaped by a "
            "different balance of these building and wearing-down processes."
        ),
    },
    {
        "id": "geo_ss2_weather_climate_vegetation",
        "subject": "Geography",
        "grade": "SS2",
        "topic": "Weather, Climate, and Vegetation",
        "content": (
            "Weather is the day-to-day state of the atmosphere, while climate is the average weather pattern "
            "of a place over a long period, measured using instruments such as the rain gauge (rainfall), "
            "thermometer (temperature), and barometer (air pressure). "
            "Climate elements — rainfall, temperature, humidity, wind, and sunshine — are shaped by factors "
            "such as altitude, latitude, ocean currents, and distance from the sea. "
            "West Africa's major climate types include the hot, wet equatorial climate near the coast and "
            "the tropical continental climate further inland, with a marked dry and wet season. "
            "Vegetation belts follow climate zones — from tropical rainforest in wetter areas to tropical "
            "grassland (savanna) in drier areas — and human activities such as farming and logging can "
            "degrade vegetation cover, making conservation important."
        ),
    },
    {
        "id": "geo_ss2_population_settlement",
        "subject": "Geography",
        "grade": "SS2",
        "topic": "Population and Settlement",
        "content": (
            "World population growth and distribution are influenced by birth rate, death rate, and "
            "migration; population is unevenly distributed, concentrated in areas with favourable climate, "
            "fertile land, and economic opportunity. "
            "Settlements are classified as rural (small, mainly farming-based communities) or urban "
            "(larger, with more varied economic activities); their location is influenced by factors like "
            "water supply, relief, and accessibility. "
            "Rural-urban migration — the movement of people from rural to urban areas — is usually driven "
            "by the search for jobs, education, and better services, and can lead to overcrowding and "
            "pressure on infrastructure in cities. "
            "Settlements interact through the exchange of goods, services, and people, producing patterns "
            "of movement such as urban-rural and rural-urban interaction."
        ),
    },
    {
        "id": "geo_ss3_nigeria_resources_economy",
        "subject": "Geography",
        "grade": "SS3",
        "topic": "Nigeria's Resources and Economic Geography",
        "content": (
            "Nigeria's mineral resources include petroleum and gas (mainly in the Niger Delta), coal, "
            "tin/columbite, iron ore, and limestone, extracted through methods ranging from open-cast mining "
            "to drilling. "
            "Agriculture remains a major economic activity, producing both food crops (for local "
            "consumption) and cash crops (for sale and export), though it faces problems such as poor "
            "storage facilities and limited mechanization. "
            "Industry is classified as primary (extracting raw materials), secondary (manufacturing), or "
            "tertiary (services); major industrial zones tend to cluster around large cities and ports where "
            "raw materials, labour, and transport are accessible. "
            "Nigeria's trade includes both domestic trade and international trade (import and export), with "
            "the stock exchange and foreign exchange market playing roles in the wider economy; Nigeria is "
            "also a member of ECOWAS, which promotes regional economic cooperation in West Africa."
        ),
    },
    {
        "id": "geo_ss3_environmental_resources",
        "subject": "Geography",
        "grade": "SS3",
        "topic": "Environmental Resources and Conservation",
        "content": (
            "Environmental resources are classified as renewable (such as vegetation and water, which can "
            "replenish over time) or non-renewable (such as minerals, which cannot be replaced once used "
            "up). "
            "Environmental hazards common in West Africa include soil erosion, drought, desert "
            "encroachment, and flooding, each with distinct causes and effects on farming communities and "
            "settlements. "
            "Environmental conservation is the careful management of natural resources to prevent their "
            "depletion or degradation, using methods such as afforestation, controlled grazing, and "
            "regulated resource extraction. "
            "Issues of development and environmental conservation include rural and regional development, "
            "resource management, and reducing pollution of air, water, and soil from human and industrial "
            "activity."
        ),
    },

    # =========== HISTORY (Nigeria-focused) ===========
    {
        "id": "hist_ss1_sources_study",
        "subject": "History",
        "grade": "SS1",
        "topic": "Sources and Study of History",
        "content": (
            "History is the systematic study of past human events, aiming to understand cause and effect "
            "and to relate the past to the present. "
            "Sources of history are grouped as primary sources (firsthand accounts, artifacts, official "
            "records made at the time) and secondary sources (later interpretations, such as textbooks, "
            "based on primary sources). "
            "Historical skills include gathering evidence, cross-checking sources for reliability, and "
            "presenting a clear, logical argument supported by evidence. "
            "In West Africa, oral tradition is an especially important source of history, alongside "
            "archaeology, written records, and linguistic evidence, because many societies did not have "
            "written records before contact with outsiders."
        ),
    },
    {
        "id": "hist_ss1_precolonial_states",
        "subject": "History",
        "grade": "SS1",
        "topic": "Pre-Colonial States in Nigeria",
        "content": (
            "Nigeria's centres of ancient civilization include Nok (known for early terracotta art), Ife "
            "(a major Yoruba spiritual and political centre), Igbo-Ukwu (known for early bronze work), and "
            "Benin (renowned for bronze casting and a centralized kingdom). "
            "Centralized states, such as the Hausa states, Oyo, and Benin, had a recognized central "
            "authority (an Oba, Emir, or Alaafin) with organized systems of administration. "
            "Non-centralized societies, such as many Igbo communities, were organized instead around "
            "village councils, age grades, and lineage heads rather than a single ruler. "
            "Inter-group relations among these societies took the form of trade, intermarriage, and "
            "occasionally war, shaping cultural exchange across the region before European contact."
        ),
    },
    {
        "id": "hist_ss2_slave_trade_european_contact",
        "subject": "History",
        "grade": "SS2",
        "topic": "The Trans-Atlantic Slave Trade and European Contact",
        "content": (
            "European traders first made contact with the West African coast seeking goods such as gold and "
            "spices, later shifting their focus to the trans-Atlantic slave trade — the forced transport of "
            "enslaved Africans to the Americas. "
            "The slave trade was organized through African and European middlemen, with enslaved people "
            "exchanged for firearms, cloth, and other goods; it caused massive population loss and social "
            "disruption in affected communities. "
            "The slave trade was gradually suppressed in the 19th century following campaigns by abolitionists "
            "and the British navy's patrols of the West African coast. "
            "As the slave trade declined, Christian missionary activity increased, bringing formal Western "
            "education and new religious institutions alongside colonial trade in goods like palm oil."
        ),
    },
    {
        "id": "hist_ss2_colonial_rule_nigeria",
        "subject": "History",
        "grade": "SS2",
        "topic": "Colonial Rule in Nigeria",
        "content": (
            "The Scramble for Africa was the rapid colonization of the continent by European powers in the "
            "late 19th century, formalized at the Berlin Conference of 1884-85, which set rules for dividing "
            "African territory among European powers without African input. "
            "Britain administered Nigeria through indirect rule, governing through existing traditional "
            "rulers under British supervision, especially in the north where the Sokoto Caliphate's emirate "
            "system was already in place. "
            "The 1914 amalgamation merged the Northern and Southern Protectorates of Nigeria into a single "
            "colony under Governor-General Frederick Lugard, for administrative convenience. "
            "Colonial rule reshaped Nigeria's economy around the export of raw materials (such as palm oil, "
            "cocoa, and groundnuts) to Britain, while importing manufactured goods, a pattern that "
            "contributed to Nigeria's later economic dependence."
        ),
    },
    {
        "id": "hist_ss3_nationalism_independence",
        "subject": "History",
        "grade": "SS3",
        "topic": "Nigerian Nationalism and the Road to Independence",
        "content": (
            "Nigerian nationalism grew after World War II, driven by educated elites who organized political "
            "parties to campaign for self-government, influenced by ideas of self-determination spreading "
            "worldwide. "
            "Major nationalist figures included Herbert Macaulay (an early nationalist leader), Nnamdi "
            "Azikiwe, Obafemi Awolowo, and Ahmadu Bello, each associated with major political parties that "
            "often had regional bases. "
            "Constitutional developments — including the Richards, Macpherson, and Lyttleton constitutions — "
            "gradually expanded Nigerian representation in government through the 1940s and 1950s. "
            "Nigeria gained independence from Britain on 1 October 1960, becoming a Commonwealth republic in "
            "1963 under its first republican constitution."
        ),
    },
    {
        "id": "hist_ss3_nigeria_since_independence",
        "subject": "History",
        "grade": "SS3",
        "topic": "Nigeria Since Independence",
        "content": (
            "Nigeria's First Republic (1960-1966) ended with a military coup in January 1966, beginning a "
            "long period of military involvement in Nigerian politics. "
            "The Nigerian Civil War (1967-1970) was fought after the Eastern Region declared itself the "
            "independent Republic of Biafra; the war ended with Biafra's surrender and the reunification of "
            "the country. "
            "Nigeria alternated between military and civilian rule for decades, including the Second "
            "Republic (1979-1983) under Shehu Shagari, before transitioning to the Fourth Republic in 1999 "
            "under Olusegun Obasanjo, which continues today. "
            "As a member of international bodies such as the United Nations, the African Union, and "
            "ECOWAS (which it helped found), Nigeria has played a significant role in African diplomacy and "
            "regional peacekeeping."
        ),
    },

    # =========== COMPUTER STUDIES ===========
    {
        "id": "cs_ss1_evolution",
        "subject": "Computer Studies",
        "grade": "SS1",
        "topic": "Evolution of Computers",
        "content": (
            "Early computing devices included the abacus (a manual counting tool), Napier's bones and the "
            "slide rule (calculation aids), and Charles Babbage's analytical engine, considered an early "
            "forerunner of the modern computer. "
            "20th-century computers evolved through ENIAC and UNIVAC 1 (early large electronic computers), "
            "then to desktop personal computers, laptops, and palmtops as components shrank in size. "
            "A computer is an electronic device made up of hardware (physical parts) and software "
            "(programs and instructions) that work together to process data into information. "
            "Key characteristics of computers include speed, accuracy, and the ability to store and process "
            "large amounts of data, distinguishing them from earlier manual calculating devices."
        ),
    },
    {
        "id": "cs_ss1_hardware",
        "subject": "Computer Studies",
        "grade": "SS1",
        "topic": "Computer Hardware",
        "content": (
            "Input devices, such as the keyboard, mouse, and scanner, allow data and instructions to be fed "
            "into a computer, while output devices, such as the monitor, printer, and speaker, present "
            "processed information to the user. "
            "The Central Processing Unit (CPU) contains the Arithmetic and Logic Unit (which performs "
            "calculations and comparisons) and the Control Unit (which directs the operations of the "
            "computer). "
            "Primary memory includes ROM (Read-Only Memory, which permanently stores essential startup "
            "instructions) and RAM (Random Access Memory, which temporarily holds data being actively used "
            "and is cleared when power is off). "
            "Secondary storage devices, such as hard disks and flash drives, store data permanently; storage "
            "capacity is measured in units from bytes up to kilobytes, megabytes, gigabytes, and terabytes."
        ),
    },
    {
        "id": "cs_ss1_software",
        "subject": "Computer Studies",
        "grade": "SS1",
        "topic": "Computer Software",
        "content": (
            "System software manages the computer itself and includes the operating system (such as "
            "Windows or Linux), which controls hardware and lets other programs run. "
            "Application software performs specific tasks for the user, such as word processing (e.g. MS "
            "Word), spreadsheets (e.g. MS Excel), and databases (e.g. MS Access). "
            "A Graphic User Interface (GUI) lets users interact with a computer using icons and a mouse, "
            "while a command-line interface requires typed text commands; GUIs are generally easier for "
            "beginners to use. "
            "Translators convert programs written by humans into a form the computer can execute: compilers "
            "translate the whole program at once, while interpreters translate and execute it line by line."
        ),
    },
    {
        "id": "cs_ss2_ethics_security",
        "subject": "Computer Studies",
        "grade": "SS2",
        "topic": "Computer Ethics and Security",
        "content": (
            "Common sources of security breaches include computer viruses and worms, poor network setup, "
            "weak or absent ICT policies, and carelessness such as sharing personal information online. "
            "Preventive measures include installing antivirus software, using a firewall to control network "
            "traffic, and being cautious about opening email attachments or entering personal information on "
            "unfamiliar sites. "
            "Encryption converts data into a coded form that can only be read by someone with the correct "
            "key, protecting sensitive information from unauthorized access. "
            "Legal and ethical issues in computing include software copyright (the ownership rights to "
            "software, text, images, audio, and video) and cybercrimes such as hacking and internet fraud."
        ),
    },
    {
        "id": "cs_ss2_networking_internet",
        "subject": "Computer Studies",
        "grade": "SS2",
        "topic": "Networking and the Internet",
        "content": (
            "A computer network connects two or more computers to share data and resources; networks are "
            "classified by size as PAN (Personal Area Network), LAN (Local Area Network), MAN (Metropolitan "
            "Area Network), or WAN (Wide Area Network), with the internet being the largest global network. "
            "Common network devices include the hub, switch, router, and modem, each playing a role in "
            "connecting devices and directing data traffic. "
            "The internet is a global system of interconnected networks; key terms include a browser "
            "(software used to access websites), a website (a collection of related webpages), and HTTP "
            "(the protocol used to transfer web content). "
            "Common internet services include electronic mail (e-mail), instant messaging, and the File "
            "Transfer Protocol (FTP), used to move files between computers over a network."
        ),
    },
    {
        "id": "cs_ss3_algorithms_flowcharts",
        "subject": "Computer Studies",
        "grade": "SS3",
        "topic": "Algorithms and Flowcharts",
        "content": (
            "An algorithm is a finite, unambiguous, step-by-step procedure for solving a problem, written "
            "in plain language before it is turned into program code. "
            "A flowchart represents an algorithm visually, using standard symbols for input/output, "
            "processing steps, and decisions, connected by arrows showing the order of execution. "
            "A good algorithm must be finite (it terminates after a limited number of steps), effective "
            "(each step is doable), and unambiguous (each step has one clear meaning). "
            "Writing an algorithm to compute the average of a set of numbers, for example, involves steps "
            "to input the numbers, sum them, divide by the count, and output the result."
        ),
    },
    {
        "id": "cs_ss3_programming_languages",
        "subject": "Computer Studies",
        "grade": "SS3",
        "topic": "Programming Languages and Program Development",
        "content": (
            "Programming languages exist at different levels: machine language (raw binary instructions the "
            "computer executes directly), low-level language (such as assembly language, closer to machine "
            "code), and high-level language (such as BASIC, C, or Python, closer to human language and "
            "easier to write). "
            "The program development cycle includes problem definition, problem analysis, designing the "
            "algorithm/flowchart, coding, compiling, testing/debugging, and documentation. "
            "A good program should be accurate, readable, efficient, and well-documented so that others can "
            "maintain it later. "
            "The system development cycle — used for larger software projects — follows similar stages: "
            "preliminary study, feasibility study, analysis, design, implementation, and maintenance."
        ),
    },

    # =========== CHRISTIAN RELIGIOUS STUDIES ===========
    {
        "id": "crs_ss1_creation_sovereignty",
        "subject": "Christian Religious Studies",
        "grade": "SS1",
        "topic": "Creation and the Sovereignty of God",
        "content": (
            "The biblical narrative depicts God as the sovereign Creator of the universe. According to "
            "Genesis, creation is presented as systematically ordered across six days, followed by divine "
            "rest on the seventh. "
            "Human beings are presented as created in the image and likeness of God, given responsibility "
            "to care for the rest of creation. "
            "God's sovereignty in this narrative implies supreme authority, providential care, and "
            "ultimate control over the created order. "
            "This account is studied alongside figures such as Joseph, Moses, and Joshua, whose stories are "
            "read for lessons on forgiveness, deliverance, obedience, and covenant."
        ),
    },
    {
        "id": "crs_ss1_israelite_history",
        "subject": "Christian Religious Studies",
        "grade": "SS1",
        "topic": "History and Religion of Israel",
        "content": (
            "The Old Testament traces Israel's history from the patriarchs (Abraham, Isaac, and Jacob) "
            "through slavery in Egypt, the exodus, and settlement in Canaan. "
            "The period of the Judges was marked by cycles of the Israelites falling into disobedience, "
            "facing oppression, and being delivered by a raised-up leader (a judge). "
            "The united monarchy under kings such as Saul, David, and Solomon established a centralized "
            "kingdom, which later split into the northern kingdom of Israel and the southern kingdom of "
            "Judah. "
            "This history is studied for the way it shows a recurring biblical theme: a nation's fortunes "
            "rising and falling with its faithfulness to its covenant with God."
        ),
    },
    {
        "id": "crs_ss2_life_of_jesus",
        "subject": "Christian Religious Studies",
        "grade": "SS2",
        "topic": "The Life and Teachings of Jesus (Synoptic Gospels)",
        "content": (
            "The Synoptic Gospels (Matthew, Mark, and Luke) record the baptism and temptation of Jesus, "
            "events that mark the start of his public ministry and demonstrate his obedience and spiritual "
            "discipline. "
            "Jesus called disciples to follow him, teaching them the demands of discipleship, which called "
            "for total commitment and a willingness to put following him above other priorities. "
            "Jesus' teachings, including his moral teachings and parables, emphasized compassion, humility, "
            "and right relationship with God and neighbour, often delivered through everyday stories. "
            "His teaching on forgiveness — encouraging reconciliation rather than revenge — is one of the "
            "most studied moral lessons from his ministry."
        ),
    },
    {
        "id": "crs_ss2_passion_resurrection",
        "subject": "Christian Religious Studies",
        "grade": "SS2",
        "topic": "The Trial, Crucifixion, and Resurrection of Jesus",
        "content": (
            "The trials of Jesus began with his arrest at Gethsemane, followed by Peter's denial of knowing "
            "him and Jesus' condemnation before religious and Roman authorities. "
            "Jesus was crucified after these trials; the crucifixion is central to Christian teaching about "
            "atonement and sacrifice. "
            "The resurrection of Jesus from the dead is regarded as the central event of the Christian "
            "faith, providing the foundation for Christian hope and belief in life after death. "
            "These events are studied together as the Passion narrative, and are used to draw lessons about "
            "faithfulness under pressure, betrayal, and the possibility of restoration."
        ),
    },
    {
        "id": "crs_ss3_early_church",
        "subject": "Christian Religious Studies",
        "grade": "SS3",
        "topic": "The Early Church and the Acts of the Apostles",
        "content": (
            "After Jesus' resurrection, the Acts of the Apostles records the growth of the early church, "
            "beginning with the coming of the Holy Spirit at Pentecost, which empowered the apostles to "
            "preach boldly. "
            "The early church was marked by fellowship, unity, and the sharing of possessions among "
            "believers, presented as a model of community life built on shared faith. "
            "Missionary journeys, especially those of Paul, spread the Christian message to non-Jewish "
            "(Gentile) communities beyond Judea, despite facing opposition from religious and civil "
            "authorities. "
            "This expansion of the church beyond its Jewish origins is studied as the beginning of "
            "Christianity's growth into a wider, international faith."
        ),
    },
    {
        "id": "crs_ss3_epistles",
        "subject": "Christian Religious Studies",
        "grade": "SS3",
        "topic": "Teachings from the Epistles",
        "content": (
            "The Epistles are letters written by early Christian leaders to guide the young churches on "
            "matters of doctrine and conduct. "
            "The Epistle of James teaches that genuine faith must be shown through good works, and calls "
            "for impartiality (not favouring the rich over the poor) and effective, sincere prayer. "
            "The First Epistle of Peter teaches good citizenship, encouraging believers to live honourably "
            "among non-believers and to maintain good relationships within the Christian community. "
            "These epistles are studied for their practical moral guidance on how faith should shape daily "
            "conduct, social relationships, and community life."
        ),
    },

    # =========== BOOK KEEPING ===========
    {
        "id": "bk_ss1_meaning_functions",
        "subject": "Book Keeping",
        "grade": "SS1",
        "topic": "Meaning, Nature, and Importance of Book Keeping",
        "content": (
            "Book keeping is the systematic recording of a business's financial transactions, forming the "
            "foundation on which financial accounting is built. "
            "It differs from accounting in scope: book keeping focuses on recording transactions accurately, "
            "while accounting also involves summarizing, analysing, and interpreting the records book "
            "keeping produces. "
            "Book keeping matters because it helps a business owner track income and expenses, know the "
            "true financial position of the business, and provide records needed for tax and loan purposes. "
            "A good book keeper needs qualities such as accuracy, honesty, attention to detail, and "
            "confidentiality, since they handle sensitive financial information."
        ),
    },
    {
        "id": "bk_ss1_assets_liabilities_transactions",
        "subject": "Book Keeping",
        "grade": "SS1",
        "topic": "Assets, Liabilities, and Business Transactions",
        "content": (
            "An asset is anything of value owned by a business, such as cash, stock, or equipment, while a "
            "liability is an amount the business owes to others, such as a loan or amount owed to suppliers. "
            "Assets are classified as fixed assets (long-term items like buildings and machinery, kept for "
            "continued use) or current assets (short-term items like cash and stock, expected to be used or "
            "converted to cash within a year). "
            "A business transaction is any exchange involving money or money's worth, such as buying goods "
            "or paying an expense; transactions typically involve at least two parties, such as a buyer and "
            "a seller. "
            "Every transaction affects at least two accounts in the books — for example, buying goods for "
            "cash reduces the cash account and increases the stock or purchases account."
        ),
    },
    {
        "id": "bk_ss1_classification_accounts",
        "subject": "Book Keeping",
        "grade": "SS1",
        "topic": "Classification of Accounts and Source Documents",
        "content": (
            "Accounts are broadly classified as personal accounts (recording transactions with specific "
            "people or businesses, such as debtors who owe the business and creditors the business owes) "
            "and impersonal accounts (covering everything else). "
            "Impersonal accounts are further split into real accounts (recording tangible assets, e.g. "
            "equipment) and nominal accounts (recording incomes and expenses, e.g. rent or sales). "
            "Source documents are the original paperwork evidencing a transaction — including invoices, "
            "receipts, credit notes, and debit notes — and are used to first record a transaction before it "
            "is entered into the books. "
            "For example, an invoice is issued when goods are sold on credit, while a receipt confirms that "
            "payment has been made."
        ),
    },
    {
        "id": "bk_ss2_books_of_original_entry_ledger",
        "subject": "Book Keeping",
        "grade": "SS2",
        "topic": "Books of Original Entry and the Ledger",
        "content": (
            "Books of original entry (also called books of prime entry) are where transactions are first "
            "recorded from source documents before being transferred (posted) to the ledger; examples "
            "include the sales day book, purchases day book, and the cash book. "
            "The cash book records all cash and bank transactions and, unlike other books of original "
            "entry, also serves as a ledger account for cash and bank. "
            "The ledger is the principal book of accounts, made up of individual accounts (such as accounts "
            "for each customer, supplier, or expense type) organized under the classifications learned "
            "earlier — personal, real, and nominal. "
            "Entries follow the double-entry principle: every transaction is recorded as a debit in one "
            "account and a corresponding credit in another, keeping the books in balance."
        ),
    },
    {
        "id": "bk_ss2_trial_balance",
        "subject": "Book Keeping",
        "grade": "SS2",
        "topic": "The Trial Balance",
        "content": (
            "A trial balance is a list of all ledger account balances at a given date, showing debit "
            "balances in one column and credit balances in another. "
            "Its main purpose is to check the arithmetic accuracy of the ledger — if the two columns total "
            "the same figure, it suggests (though does not guarantee) that entries have been made correctly "
            "under the double-entry system. "
            "A trial balance can fail to balance due to errors such as a transaction being entered on only "
            "one side, or the wrong amount being entered on one side. "
            "However, some errors — such as recording a transaction completely correctly but in the wrong "
            "account, or omitting a transaction entirely from both sides — do not affect the trial balance "
            "totals and so remain undetected by it."
        ),
    },
    {
        "id": "bk_ss3_petty_cash_stock_valuation",
        "subject": "Book Keeping",
        "grade": "SS3",
        "topic": "Petty Cash Book and Stock Valuation",
        "content": (
            "A petty cash book records small, day-to-day cash expenses (such as postage or minor supplies) "
            "separately from the main cash book, usually using the imprest system. "
            "Under the imprest system, the petty cashier starts each period with a fixed float (a set amount "
            "of cash); at the end of the period, the amount spent is reimbursed to restore the float back to "
            "its original fixed level. "
            "Stock valuation determines the value of unsold goods at the end of a trading period, commonly "
            "using the cost price or the net realizable value, whichever is lower, to avoid overstating "
            "profit. "
            "Accurate stock valuation is essential because it directly affects the cost of goods sold and "
            "therefore the gross profit shown in the trading account."
        ),
    },
    {
        "id": "bk_ss3_ratios_final_accounts",
        "subject": "Book Keeping",
        "grade": "SS3",
        "topic": "Final Accounts and Basic Accounting Ratios",
        "content": (
            "Final accounts summarize a business's performance and position at the end of a trading period: "
            "the trading account shows gross profit, the profit and loss account shows net profit, and the "
            "balance sheet shows the business's assets, liabilities, and capital at that date. "
            "The gross profit margin (gross profit as a percentage of sales) shows how efficiently a "
            "business buys and sells goods before overhead costs are considered. "
            "The net profit margin (net profit as a percentage of sales) shows overall profitability after "
            "all expenses are deducted. "
            "Liquidity ratios such as the quick ratio (or acid test ratio) measure a business's ability to "
            "meet short-term debts using its most liquid assets, excluding stock, which may not be quickly "
            "convertible to cash."
        ),
    },

    # =========== ISLAMIC RELIGIOUS STUDIES ===========
    {
        "id": "irs_ss1_jahiliyyah_reforms",
        "subject": "Islamic Religious Studies",
        "grade": "SS1",
        "topic": "Arabia Before Islam and the Reforms of Islam",
        "content": (
            "The Jahiliyyah refers to the period in Arabia before Islam, marked by idol worship, tribal "
            "conflict, and social practices such as unregulated marriage, divorce, and inheritance customs. "
            "Political life before Islam had no central government, with power resting in individual tribes, "
            "while economic life relied mainly on trade caravans and pastoralism. "
            "Islam introduced reforms to Jahiliyyah practices, regulating marriage and inheritance, banning "
            "idol worship, and establishing clearer rules of social and family conduct rooted in monotheism "
            "(Tawhid). "
            "These reforms are studied to understand how Islam reshaped Arabian society's beliefs, family "
            "life, and governance."
        ),
    },
    {
        "id": "irs_ss1_prophet_muhammad",
        "subject": "Islamic Religious Studies",
        "grade": "SS1",
        "topic": "The Life and Mission of Prophet Muhammad",
        "content": (
            "Prophet Muhammad (S.A.W.) received his call to prophethood through revelations that began at "
            "the Cave of Hira, marking the start of his mission to preach monotheism in Makkah. "
            "Facing persecution in Makkah, Muhammad and his followers undertook the Hijrah (migration) to "
            "Madinah, an event that marks the start of the Islamic calendar. "
            "In Madinah, Muhammad organized the growing Muslim community (Ummah), and several battles "
            "followed between the Muslims and their Makkan opponents, including the battles of Badr, Uhud, "
            "and Khandaq, each with distinct causes, events, and outcomes. "
            "The Treaty of Hudaybiyyah and the later conquest of Makkah eventually secured peace, and "
            "Muhammad's Farewell Pilgrimage and sermon summarized key teachings shortly before his death."
        ),
    },
    {
        "id": "irs_ss1_tauhid",
        "subject": "Islamic Religious Studies",
        "grade": "SS1",
        "topic": "Concepts of Tauhid (Oneness of Allah)",
        "content": (
            "Tauhid is the foundational Islamic doctrine declaring the absolute oneness, uniqueness, and "
            "indivisibility of Allah, affirmed through the Kalimatush-Shahadah (the declaration of faith). "
            "It is commonly categorized into three dimensions: Tauhid ar-Rububiyyah (Allah alone as Creator, "
            "Sustainer, and Ruler of all existence), Tauhid al-Uluhiyyah (all worship directed exclusively "
            "to Allah, without partners), and Tauhid al-Asma was-Sifat (affirming Allah's names and "
            "attributes as He describes them). "
            "Shirk is the association of partners with Allah, considered the most severe violation of "
            "Tauhid in Islamic theology. "
            "This doctrine also connects to the wider articles of faith: belief in Allah's angels, revealed "
            "books, prophets (with special emphasis on the Ulu'l-'Azm — Ibrahim, Nuh, Musa, 'Isa, and "
            "Muhammad), the Day of Judgement, and destiny (Qada' and Qadar)."
        ),
    },
    {
        "id": "irs_ss2_pillars_salat_sawm",
        "subject": "Islamic Religious Studies",
        "grade": "SS2",
        "topic": "Pillars of Islam: Salat and Sawm",
        "content": (
            "Salat (ritual prayer) is one of the five pillars of Islam, performed five times daily; it is "
            "categorized as obligatory, non-obligatory, or occasional, and includes special provisions for "
            "travellers. "
            "Sawm (fasting) is compulsory during the month of Ramadan and can also be voluntary at other "
            "times; a valid fast has spiritual, social, and moral objectives, and certain groups (such as the "
            "sick or travellers) are exempted. "
            "Certain actions vitiate (invalidate) a fast, and understanding these is part of correctly "
            "observing Sawm. "
            "Both Salat and Sawm are studied not just as rituals but for the discipline, self-control, and "
            "community bonds they are meant to cultivate."
        ),
    },
    {
        "id": "irs_ss2_zakat_hajj",
        "subject": "Islamic Religious Studies",
        "grade": "SS2",
        "topic": "Pillars of Islam: Zakat and Hajj",
        "content": (
            "Zakat is an obligatory almsgiving, distinguished from Sadaqah (voluntary charity); it applies to "
            "specific categories of wealth, including money, livestock, and agricultural produce, once they "
            "reach a minimum threshold (Nisab). "
            "Zakat serves social and economic purposes: it redistributes wealth to defined categories of "
            "beneficiaries, purifies the giver's wealth, and helps reduce economic inequality in the "
            "community. "
            "Hajj (pilgrimage to Makkah) is obligatory once in a lifetime for Muslims who are physically and "
            "financially able, and its rites commemorate events from the lives of Ibrahim and his family. "
            "These two pillars are studied together for their combined socio-economic and spiritual "
            "objectives within the Muslim community."
        ),
    },
    {
        "id": "irs_ss3_quran_hadith",
        "subject": "Islamic Religious Studies",
        "grade": "SS3",
        "topic": "The Qur'an and Hadith as Sources of Guidance",
        "content": (
            "The Qur'an was revealed to Muhammad piecemeal over many years, beginning with the first "
            "revelation at Cave Hira, and was later compiled, arranged, and standardized with the help of the "
            "Prophet's companions. "
            "The Qur'an serves as the primary source of guidance in Islam for social, political, spiritual, "
            "and moral matters, and its distinction between Makki and Madani chapters reflects the different "
            "periods and contexts of revelation. "
            "Hadith (the recorded sayings and actions of the Prophet) complements the Qur'an, offering "
            "practical examples of how its teachings were applied in daily life; the Six Sound Collections "
            "(Sihah Sittah) are the most authoritative compilations. "
            "Together, the Qur'an and Hadith form the two central sources from which Islamic theology "
            "(Tawhid) and jurisprudence (Fiqh) are derived."
        ),
    },

    # =========== DATA PROCESSING ===========
    {
        "id": "dp_ss1_data_information",
        "subject": "Data Processing",
        "grade": "SS1",
        "topic": "Data, Information, and the History of Computing",
        "content": (
            "Data refers to raw, unorganized facts or figures, while information is data that has been "
            "processed and organized into a meaningful, useful form. "
            "Data can be handled in different ways, including manual processing, mechanical processing, and "
            "electronic data processing using computers, which is by far the fastest and most accurate. "
            "The history of computing devices runs from the abacus and other early counting tools through to "
            "modern digital computers, reflecting a steady move toward smaller size, greater speed, and "
            "greater storage capacity. "
            "Digitalization is the process of converting information into a digital (binary) format that "
            "computers can store, process, and transmit."
        ),
    },
    {
        "id": "dp_ss1_computer_components",
        "subject": "Data Processing",
        "grade": "SS1",
        "topic": "Computer Components and Information Processing",
        "content": (
            "A computer system includes input devices (which capture data, such as a keyboard or scanner), "
            "the system unit (which processes data), and output devices (which present results, such as a "
            "monitor or printer). "
            "Information processing is the sequence of capturing, storing, manipulating, and presenting data "
            "as useful information, typically following the stages of input, processing, storage, and output. "
            "ICT (Information and Communication Technology) is used in everyday activities such as banking, "
            "education, communication, and commerce, streamlining tasks that were previously done manually. "
            "Choosing appropriate input and output devices depends on the type of data being handled and the "
            "form in which the output is needed."
        ),
    },
    {
        "id": "dp_ss2_operating_systems",
        "subject": "Data Processing",
        "grade": "SS2",
        "topic": "Operating Systems",
        "content": (
            "An operating system is system software that manages a computer's hardware resources and "
            "provides common services for other programs to run on. "
            "Its functions include memory management, processor (task) scheduling, file system organization, "
            "and control of input/output devices. "
            "Operating systems are classified as single-user, multi-user, multitasking, or real-time, "
            "depending on how many users or tasks they can handle at once. "
            "Common examples include Microsoft Windows, Linux, macOS, and mobile operating systems like "
            "Android, each with a graphical user interface (GUI) or command-line interface (CLI) for user "
            "interaction."
        ),
    },
    {
        "id": "dp_ss2_networking_internet",
        "subject": "Data Processing",
        "grade": "SS2",
        "topic": "Networking and the Internet",
        "content": (
            "Networking connects computers so they can share data and resources; a network can be a local "
            "network restricted to an organization (an intranet) or the wider internet, a global network of "
            "interconnected computers. "
            "Data transmission media can be wired (such as cables) or wireless (such as radio and satellite "
            "signals), each with different speed, cost, and reliability trade-offs. "
            "Common internet services include electronic mail (e-mail), instant messaging, and the File "
            "Transfer Protocol (FTP), used to move files between computers over a network. "
            "A browser is software used to access websites, and HTTP is the protocol used to transfer web "
            "content between a server and a browser."
        ),
    },
    {
        "id": "dp_ss2_word_processing",
        "subject": "Data Processing",
        "grade": "SS2",
        "topic": "Word Processing",
        "content": (
            "Word processing is the use of software to create, edit, format, and print text documents, with "
            "examples including Microsoft Word and Open Office Writer. "
            "Basic word processing operations include creating a new document, saving it for future use, and "
            "retrieving (opening) a previously saved file. "
            "Formatting tools within a word processor allow control over font style and size, alignment, "
            "spacing, and page layout, helping produce a clear and professional-looking document. "
            "Word processors also include features such as spell check, find-and-replace, and mail merge, "
            "which speed up document creation and reduce errors."
        ),
    },
    {
        "id": "dp_ss3_spreadsheets_databases",
        "subject": "Data Processing",
        "grade": "SS3",
        "topic": "Spreadsheets and Database Applications",
        "content": (
            "Spreadsheet software (such as Microsoft Excel) organizes data into rows and columns of cells, "
            "allowing calculations, formulas, and charts to be built directly from the data. "
            "A database is an organized collection of related data, structured into tables made up of "
            "records (rows) and fields (columns), allowing efficient storage, search, and retrieval of "
            "information. "
            "Database applications (such as Microsoft Access) allow users to create tables, run queries to "
            "extract specific information, and generate reports summarizing the data. "
            "Presentation programs (such as Microsoft PowerPoint) allow users to combine text, images, and "
            "other media into slides for presenting information to an audience."
        ),
    },
    {
        "id": "dp_ss3_data_security",
        "subject": "Data Processing",
        "grade": "SS3",
        "topic": "Data Security and Access Control",
        "content": (
            "Data security refers to the protective measures used to guard files and databases from "
            "unauthorized access, alteration, or loss. "
            "Core security mechanisms include data encryption (encoding data so only someone with the right "
            "key can read it), firewalls (which filter network traffic), user authentication, and regular "
            "backups. "
            "Access control restricts who can enter a system, using methods such as passwords, biometric "
            "verification (e.g. fingerprints), or security tokens. "
            "Malicious software — including viruses, worms, and ransomware — poses an ongoing risk to stored "
            "data, making antivirus software and safe computing habits an essential part of data security."
        ),
    },

    # =========== MARKETING ===========
    {
        "id": "mkt_ss1_basic_concepts",
        "subject": "Marketing",
        "grade": "SS1",
        "topic": "Basic Concepts and Functions of Marketing",
        "content": (
            "Marketing involves basic terms such as needs (necessities), wants (specific desires shaped by "
            "personality and culture), demand (wants backed by ability to pay), and exchange (the act of "
            "obtaining something by offering something in return). "
            "Marketing differs from selling: selling focuses narrowly on converting a product into cash, "
            "while marketing takes a broader view, starting with identifying customer needs and ending with "
            "customer satisfaction. "
            "The functions of marketing include buying, selling, transportation, storage, financing, risk "
            "bearing, standardization and grading, and market information gathering. "
            "Marketing has evolved in Nigeria alongside the country's economic development, growing from "
            "simple trade and barter into a more structured, organized discipline."
        ),
    },
    {
        "id": "mkt_ss1_marketing_concepts",
        "subject": "Marketing",
        "grade": "SS1",
        "topic": "Marketing Concepts and Orientations",
        "content": (
            "The production concept assumes customers favour widely available, affordable products, so a "
            "business focuses on mass production and efficiency. "
            "The product concept assumes customers favour the highest quality or most innovative products, "
            "so a business focuses on continuous product improvement. "
            "The selling concept assumes customers must be persuaded to buy through aggressive selling and "
            "promotion, since they otherwise would not buy enough. "
            "The marketing concept, by contrast, starts by identifying target customers' needs and "
            "delivering satisfaction more effectively than competitors, while the societal marketing concept "
            "adds a further requirement: that this be done in a way that preserves consumer and societal "
            "well-being."
        ),
    },
    {
        "id": "mkt_ss2_marketing_mix",
        "subject": "Marketing",
        "grade": "SS2",
        "topic": "The Marketing Mix (4Ps)",
        "content": (
            "The marketing mix is the combination of controllable tools a business uses to achieve its "
            "marketing objectives, traditionally grouped as Product, Price, Place, and Promotion (the 4Ps). "
            "Product decisions cover the features, quality, branding, and packaging of what is offered, "
            "shaped by an understanding of customer needs. "
            "Price decisions cover how much customers are charged, using strategies such as cost-plus "
            "pricing (adding a profit margin to cost), competitive pricing, or penetration pricing. "
            "Place decisions cover how a product reaches the customer (distribution channels), while "
            "Promotion covers how a business communicates with and persuades its customers, using tools such "
            "as advertising, personal selling, and sales promotion."
        ),
    },
    {
        "id": "mkt_ss2_environment_consumer_behaviour",
        "subject": "Marketing",
        "grade": "SS2",
        "topic": "The Marketing Environment and Consumer Behaviour",
        "content": (
            "The marketing environment consists of factors outside a business's direct control that "
            "influence its marketing decisions, including political, economic, social/cultural, "
            "technological, and religious factors. "
            "Consumer behaviour is the study of how individuals decide what to buy, influenced by personal "
            "factors (such as age and income), psychological factors (such as motivation and perception), "
            "and social factors (such as family and reference groups). "
            "Market segmentation divides a broad market into smaller groups of consumers with similar needs "
            "or characteristics, allowing a business to target its marketing more precisely. "
            "Understanding both the environment and consumer behaviour helps a business adapt its marketing "
            "mix to fit the specific group of customers it is trying to reach."
        ),
    },
    {
        "id": "mkt_ss3_distribution_promotion_research",
        "subject": "Marketing",
        "grade": "SS3",
        "topic": "Distribution, Promotion, and Marketing Research",
        "content": (
            "Channels of distribution describe the path a product takes from producer to final consumer, "
            "which may be direct (producer to consumer) or involve intermediaries such as wholesalers and "
            "retailers. "
            "Promotion uses a mix of tools including advertising (paid, non-personal communication through "
            "mass media), personal selling (direct interaction with a salesperson), sales promotion "
            "(short-term incentives to boost sales), and publicity. "
            "Marketing research is the systematic gathering, recording, and analysis of data about a "
            "specific market, product, or promotion, helping a business make more informed decisions. "
            "The product life cycle — introduction, growth, maturity, and decline — describes how a "
            "product's sales and marketing needs typically change over time, guiding when to adjust price, "
            "promotion, or distribution strategy."
        ),
    },

    # =========== CATERING CRAFT PRACTICE ===========
    {
        "id": "catering_ss1_establishments_commodities",
        "subject": "Catering Craft Practice",
        "grade": "SS1",
        "topic": "Catering Establishments and Food Commodities",
        "content": (
            "Catering establishments vary by type, including hotels, restaurants, hospitality catering, "
            "outdoor catering, school catering, and mobile catering, each with different scale and service "
            "requirements. "
            "Food commodities used in catering include poultry, game, meat, fish, vegetables, fruits, dairy "
            "products, pulses, cereals, and herbs and flavourings, each requiring specific knowledge of "
            "quality, cost, and use. "
            "A caterer must understand standard and local measurements to accurately follow and scale "
            "recipes for different numbers of guests. "
            "Choosing the right commodities and understanding their qualities is essential to producing "
            "dishes that are both cost-effective and satisfying to customers."
        ),
    },
    {
        "id": "catering_ss1_cooking_methods",
        "subject": "Catering Craft Practice",
        "grade": "SS1",
        "topic": "Methods of Cooking",
        "content": (
            "Boiling is a moist-heat cooking method used for foods like stocks, soups, and sauces, cooking "
            "food in liquid at boiling point. "
            "Roasting and grilling are dry-heat methods commonly used for fish, beef, and poultry, applying "
            "direct or indirect heat to develop flavour and texture. "
            "Baking uses dry heat in an enclosed space (an oven) and is especially important for pastry and "
            "confectionery products. "
            "Each cooking method suits different foods and desired results, and a caterer must understand "
            "the principles behind each method to select the right one and demonstrate it correctly."
        ),
    },
    {
        "id": "catering_ss2_kitchen_equipment_hygiene",
        "subject": "Catering Craft Practice",
        "grade": "SS2",
        "topic": "Kitchen Equipment and Food Hygiene",
        "content": (
            "Kitchen equipment ranges from basic hand tools — such as a balloon whisk (for beating or "
            "whipping), a palette knife (for spreading icing), and a rolling pin (for flattening dough) — to "
            "larger equipment such as ovens and mixers. "
            "Choosing, caring for, and storing kitchen equipment properly extends its useful life and "
            "supports food safety in the kitchen. "
            "Hygienic practices in food handling include proper handwashing, keeping raw and cooked foods "
            "separate, maintaining correct storage temperatures, and keeping work surfaces clean to prevent "
            "contamination. "
            "Safety precautions in catering cover the safe use of sharp tools, hot equipment (such as deep "
            "fryers), and correct handling of hazards to prevent burns, cuts, and fires in the kitchen."
        ),
    },
    {
        "id": "catering_ss2_food_beverage_service",
        "subject": "Catering Craft Practice",
        "grade": "SS2",
        "topic": "Food and Beverage Service",
        "content": (
            "Food and beverage service personnel include waiters, hosts, and bartenders, each with defined "
            "roles in ensuring guests are served correctly and courteously. "
            "Different types of food service exist for different occasions, including waiter service, "
            "self-service or buffet service, and banquet service for large formal events. "
            "Correct table setting, including the placement of cutlery, crockery, and glassware, is an "
            "important part of professional food service and is often tested in practical assessment. "
            "Understanding the sequence of service — from greeting and seating guests to taking orders, "
            "serving, and clearing — helps ensure a smooth dining experience."
        ),
    },
    {
        "id": "catering_ss3_menu_planning_costing",
        "subject": "Catering Craft Practice",
        "grade": "SS3",
        "topic": "Menu Planning and Enterprise Skills",
        "content": (
            "Menu planning involves selecting dishes that balance variety, nutrition, cost, and the skills "
            "and equipment available in the kitchen, while also considering the occasion and guests' dietary "
            "needs. "
            "Dietary adequacy in menu planning means ensuring a menu provides a nutritionally balanced range "
            "of dishes, taking into account any special dietary requirements of guests. "
            "Menu costing calculates the cost of ingredients and preparation for a dish or event, forming "
            "the basis for setting a price that covers costs and provides a profit. "
            "Enterprise skills in catering include understanding how to plan, cost, and run a small catering "
            "business, preparing students for self-employment opportunities in the food service industry."
        ),
    },

    # =========== FASHION DESIGN AND GARMENT MAKING ===========
    {
        "id": "garment_ss1_sewing_tools_equipment",
        "subject": "Fashion Design and Garment Making",
        "grade": "SS1",
        "topic": "Sewing Tools and Equipment",
        "content": (
            "Sewing tools and equipment are classified by function: measuring tools (such as a long ruler), "
            "marking tools (such as tailor's chalk and a tracing wheel), cutting tools (such as cutting "
            "shears and paper scissors), and joining tools (such as sewing machines and needles). "
            "Pressing equipment, including a pressing iron and ironing board, is used to flatten seams and "
            "give garments a professional finish during and after construction. "
            "Fitting equipment, such as a dress form and standing mirror, allows a garment maker to check "
            "how a garment fits before it is completed. "
            "Proper selection, use, and maintenance of these tools is essential, since worn or poorly "
            "maintained equipment can damage fabric or produce inaccurate cuts and seams."
        ),
    },
    {
        "id": "garment_ss2_pattern_making_cutting",
        "subject": "Fashion Design and Garment Making",
        "grade": "SS2",
        "topic": "Pattern Making and Garment Cutting",
        "content": (
            "Pattern making creates a template used to cut fabric pieces that will be sewn together into a "
            "garment, and can be done using drafted measurements or by adapting an existing pattern. "
            "Freehand cutting is an alternative technique where fabric is cut directly without a paper "
            "pattern, requiring greater skill and experience from the garment maker. "
            "Factors that influence garment design include the wearer's age, figure type, and the intended "
            "occasion, all of which affect fabric choice, style, and fit. "
            "Accurate cutting is critical, since errors made at this stage are difficult to correct later "
            "and can lead to a poorly fitting finished garment."
        ),
    },
    {
        "id": "garment_ss3_construction_entrepreneurship",
        "subject": "Fashion Design and Garment Making",
        "grade": "SS3",
        "topic": "Garment Construction and Entrepreneurship",
        "content": (
            "Garment construction follows a general process: cutting fabric pieces from a pattern, joining "
            "them with appropriate seams, adding finishing details (such as buttons and hems), and pressing "
            "the completed garment. "
            "Adaptation techniques allow a garment maker to modify a basic pattern to create different "
            "outfits, such as gowns and jumpers, from the same foundational shapes. "
            "Setting up a garment-making enterprise requires appreciating the value of locally made fabrics, "
            "understanding basic costing and pricing, and recognizing entrepreneurship as a path to "
            "self-reliance and job creation. "
            "Practical assessment in garment making typically requires candidates to construct actual "
            "articles of clothing, testing both their technical sewing skills and their design decisions."
        ),
    },

    # =========== GSM MAINTENANCE AND REPAIRS ===========
    {
        "id": "gsm_ss1_mobile_phone_basics",
        "subject": "GSM Maintenance and Repairs",
        "grade": "SS1",
        "topic": "Introduction to Mobile Phones and Terminology",
        "content": (
            "Mobile phone terminology includes acronyms such as GSM (Global System for Mobile "
            "communications) and CDMA (Code Division Multiple Access), which describe different mobile "
            "network technologies. "
            "Other important terms include SMS (Short Message Service), MMS (Multimedia Messaging Service), "
            "call barring, and call forwarding, all common features on mobile handsets. "
            "The essential components of a mobile phone include hardware components (such as the CPU, SIM "
            "socket, earpiece, and keypad) and software components (both operating system and application "
            "software). "
            "A mobile phone's basic block diagram includes a power unit, memory unit, and radio unit, each "
            "responsible for a distinct function within the device."
        ),
    },
    {
        "id": "gsm_ss2_maintenance_repair",
        "subject": "GSM Maintenance and Repairs",
        "grade": "SS2",
        "topic": "Maintenance and Repair of Mobile Phones",
        "content": (
            "Mobile phones contain electronic components such as resistors, capacitors, diodes, transistors, "
            "and integrated circuits (ICs), which a repair technician must be able to identify and test. "
            "Preventive maintenance involves regular checks and cleaning to avoid faults before they occur, "
            "while corrective maintenance involves diagnosing and fixing a fault once it has occurred. "
            "Common tools and equipment for hardware repair include a multi-meter, oscilloscope, soldering "
            "iron, and precision screwdriver set, each used for specific diagnostic or repair tasks. "
            "Common tools for software repair include unlocking software and flashing software, used to fix "
            "issues such as firmware corruption or a locked device."
        ),
    },
    {
        "id": "gsm_ss3_troubleshooting_safety",
        "subject": "GSM Maintenance and Repairs",
        "grade": "SS3",
        "topic": "Troubleshooting, Safety, and Enterprise",
        "content": (
            "Hardware problems in mobile phones include a damaged screen, faulty charging port, or "
            "non-functioning earpiece, each requiring different disassembly and testing procedures to "
            "diagnose. "
            "Software problems include error messages such as 'contact service provider', an invalid SIM "
            "error, or a phone lock code issue, which are usually resolved through flashing or reinstalling "
            "firmware rather than physical repair. "
            "Safety in a mobile phone repair workshop requires following safety rules for using tools "
            "correctly and having basic safety facilities available, such as a first aid box and fire "
            "extinguisher. "
            "Setting up and running a mobile phone maintenance business requires knowledge of sourcing "
            "tools and spare parts, pricing repairs fairly, and building trust with customers through "
            "reliable service."
        ),
    },

    # =========== YORUBA LANGUAGE ===========
    {
        "id": "yoruba_ss1_sound_system_grammar",
        "subject": "Yoruba Language",
        "grade": "SS1",
        "topic": "Sound System and Grammar of Yoruba",
        "content": (
            "Yoruba sound processes include vowel harmony, assimilation, and elision, which describe how "
            "sounds change or combine when words are spoken together in the language. "
            "Yoruba grammar covers grammatical categories such as subject, object, complement, predicate, "
            "number, person, tense, aspect, and mood, which together determine how a sentence is correctly "
            "structured. "
            "Sentences in Yoruba are classified by structure and type, and learners study how phrases and "
            "clauses combine to form complete, grammatically correct sentences. "
            "A strong grasp of the sound system and grammar is tested directly through composition, "
            "translation, and comprehension exercises in the examination."
        ),
    },
    {
        "id": "yoruba_ss2_oral_written_literature",
        "subject": "Yoruba Language",
        "grade": "SS2",
        "topic": "Yoruba Oral and Written Literature",
        "content": (
            "Yoruba oral literature includes traditional genres such as prose (folktales), poetry (such as "
            "oriki, chants of praise), and drama, passed down and performed within the community. "
            "Written Yoruba literature covers set books in prose, poetry, and drama chosen for study, and "
            "candidates are examined on their understanding of plot, character, and theme in these texts. "
            "Basic principles of literary appreciation — including understanding of setting, characterization, "
            "and figures of speech such as proverbs (owe) and idioms — are needed to analyze both oral and "
            "written texts. "
            "Yoruba proverbs and idiomatic expressions are especially valued in both literature and everyday "
            "speech for their compact way of conveying wisdom and cultural values."
        ),
    },
    {
        "id": "yoruba_ss3_customs_institutions",
        "subject": "Yoruba Language",
        "grade": "SS3",
        "topic": "Yoruba Customs and Institutions",
        "content": (
            "Yoruba customs studied include naming ceremonies, marriage rites, and funeral practices, each "
            "governed by specific traditional procedures and social meaning. "
            "Traditional Yoruba political institutions include chieftaincy and Obaship (kingship), which "
            "continue to hold cultural and, in some contexts, administrative significance alongside modern "
            "government structures. "
            "Traditional Yoruba beliefs include belief in Olodumare (God) and various deities/divinities, "
            "alongside the more recently adopted religions of Islam and Christianity practiced widely today. "
            "Home training in Yoruba culture emphasizes values such as respect for elders, greetings "
            "appropriate to different occasions, and hard work, all of which are tested as part of the "
            "culture and institutions component of the examination."
        ),
    },
    {
        "id": "yoruba_ss1_ewi",
        "subject": "Yoruba Language",
        "grade": "SS1",
        "topic": "Ewi Alafunwogbe (Oral Poetry)",
        "content": (
            "Ewi alafunwogbe jẹ́ ọ̀nà kan pàtàkì tí a gbà láti sọ èrò ọkàn jáde nípa lílo èdè tó lọ́rinrin. "
            "Àwọn ewì rorùn láti kà, wọ́n sì máa ń ní ìró ohùn tó dọ́gba níparí gbólóhùn kọ̀ọ̀kan. "
            "Àwọn ewì yìí ń gbé àṣà, ìṣe, àti ìtàn ilẹ̀ Yorùbá lárugẹ láti ràn wọ́n lọ́wọ́ láti kọ́ ẹ̀kọ́ rere. "
            "Àwọn ohun èlò èdè bíi àmúpò, àwòpò, àti àpèjúwe máa ń mú kí ewì dùn-ún gbọ́ nínú kíláàsì. "
            "Olùwòran tàbí olùgbọ́ máa ń rí ẹ̀kọ́ ìwà rere kọ́ nínú ewì kọ̀ọ̀kan láìsí àní-àní."
        ),
    },

    # =========== HAUSA LANGUAGE ===========
    {
        "id": "hausa_ss1_sound_system_word_structure",
        "subject": "Hausa Language",
        "grade": "SS1",
        "topic": "Sound System and Word Structure of Hausa",
        "content": (
            "Hausa consonants and vowels combine according to specific syllable structure rules (kirar "
            "gaba), and their correct production involves attention to place and manner of articulation. "
            "Word structure and word formation in Hausa (ginin kalmomi) covers how roots combine with "
            "affixes and other processes to build new words. "
            "Hausa grammar covers word classes such as nouns, verbs, and pronouns, along with grammatical "
            "categories like tense and number that shape correct sentence construction. "
            "Mastery of the sound system and word structure underpins performance in composition, "
            "translation, and comprehension sections of the Hausa examination."
        ),
    },
    {
        "id": "hausa_ss2_oral_written_literature",
        "subject": "Hausa Language",
        "grade": "SS2",
        "topic": "Hausa Oral and Written Literature",
        "content": (
            "Hausa oral literature includes prose, poetry, and drama passed down through generations, "
            "reflecting the values and history of Hausa society. "
            "Written Hausa literature includes prescribed set books in prose, poetry, and drama, with "
            "candidates tested on their understanding of the content and its themes. "
            "Basic principles of literary appreciation are applied to both oral and written texts, requiring "
            "students to analyze plot, character, setting, and stylistic devices. "
            "Hausa literary works are often noted for their strong moral and social themes, connecting "
            "storytelling to lessons about community life and conduct."
        ),
    },
    {
        "id": "hausa_ss3_customs_institutions",
        "subject": "Hausa Language",
        "grade": "SS3",
        "topic": "Hausa Customs and Traditional Institutions",
        "content": (
            "Hausa traditional occupations (sana'o'in gargajiya) include crafts and trades passed down "
            "through families, forming part of the cultural knowledge tested in the examination. "
            "Traditional authority and office holding (sarautun gargajiya) describes the Hausa emirate "
            "system, including titled offices held under the authority of an Emir. "
            "Hausa customs also include beliefs and practices sometimes viewed as contrary to mainstream "
            "religion, such as traditional divination, alongside the predominant practice of Islam in Hausa "
            "society today. "
            "Traditional forms of recreation (wasannin dandali), such as communal games and gatherings, are "
            "studied as part of understanding everyday Hausa cultural life."
        ),
    },
    {
        "id": "hausa_ss1_grammar_native",
        "subject": "Hausa Language",
        "grade": "SS1",
        "topic": "Tsarin Gidaje (Grammar Structure)",
        "content": (
            "Tsarin ilimin nahawun hausa yana gina ne akan harafe-harafe da kalmomi masu ma'ana. "
            "Kalmomi sun kasu kashi daban-daban kamar suna, aikatau, siffa, da kuma canjin murya. "
            "Kowace jimla tana buƙatar mai yin aiki da abin da aka yi wa aiki domin ta cika ma'ana. "
            "A cikin karatun jami'a ko makarantun gaba da firamare, ana koya wa ɗalibai dabarun rubutu. "
            "Yin amfani da harafin da ya dace yana taimakawa wajen kauce wa kuskuren ma'ana a jarrabawa."
        ),
    },

    # =========== IGBO LANGUAGE ===========
    {
        "id": "igbo_ss1_phonemes_grammar",
        "subject": "Igbo Language",
        "grade": "SS1",
        "topic": "Igbo Phonemes and Grammar",
        "content": (
            "Igbo phonemes include vowels, consonants, and the syllabic nasal, each classified by how they "
            "are produced and how they function within a word. "
            "Sound processes in Igbo include vowel harmony, vowel assimilation, and vowel and consonant "
            "elision, which describe how sounds change when words are spoken in sequence. "
            "Igbo grammar covers word classes (such as noun, verb, pronoun, conjunction, and preposition) "
            "and grammatical categories such as tense, number, and person. "
            "Understanding phrases, clauses, and sentence types — including sentences containing direct and "
            "indirect speech — is essential for accurate composition and translation in Igbo."
        ),
    },
    {
        "id": "igbo_ss2_oral_written_literature",
        "subject": "Igbo Language",
        "grade": "SS2",
        "topic": "Igbo Oral and Written Literature",
        "content": (
            "Oral literature in Igbo includes prose (folktales), poetry, and drama traditionally performed "
            "and transmitted within the community rather than through writing. "
            "Written Igbo literature includes prescribed novels, plays, and poetry collections, with "
            "students expected to demonstrate detailed knowledge of these set texts. "
            "Basic principles of literary appreciation require students to identify and discuss elements "
            "such as characterization, setting, plot, and theme across both oral and written literature. "
            "Igbo literary and oral traditions place strong emphasis on proverbs and idiomatic expressions, "
            "which are valued for enriching language and conveying cultural wisdom concisely."
        ),
    },
    {
        "id": "igbo_ss3_customs_institutions",
        "subject": "Igbo Language",
        "grade": "SS3",
        "topic": "Igbo Customs and Institutions",
        "content": (
            "Igbo customs studied include naming ceremonies (ịgụ aha), marriage and inheritance practices, "
            "and funeral rites (akwamozu), each following specific traditional procedures. "
            "Traditional Igbo political structures include the family (ezinaụlọ), the age-grade system (otu "
            "ọgbọ), and the umunna (extended kinship group), which historically played roles in community "
            "governance alongside titled institutions such as nze na ọzọ. "
            "Traditional Igbo beliefs include concepts such as reincarnation (ịlọ ụwa) and ọgbanje (a "
            "traditional belief about a child believed to die and be reborn repeatedly), studied alongside "
            "the widespread practice of Christianity in Igbo society today. "
            "Traditional Igbo festivals, such as the New Yam Festival (ịwa ji), mark important points in the "
            "agricultural calendar and hold significant social and religious meaning."
        ),
    },
    {
        "id": "igbo_ss1_culture_native",
        "subject": "Igbo Language",
        "grade": "SS1",
        "topic": "Omenala na Agumagu (Culture and Literature)",
        "content": (
            "Omenala ndi Igbo gụnyere ejiji, nri, emume dị iche iche, na usoro nkwanyere ugwu n'ala anyị. "
            "Agumagu na-enyere aka idebe akụkọ mgbe ochie na amamihe ndị nna nna anyị hapụrụ anyị. "
            "E nwere agumagu ọnụ na agumagu edere ede nke na-akụziri ụmụ akwụkwaku ezi omume. "
            "Iji asụsụ Igbo dịka nka na-eme ka ọdịnala anyị ghara ịnwụ anwụ n'etiti ndị na-eto eto. "
            "Ụmụ akwụkwọ na-amụ asụsụ a na-enwe nghọta miri emi gbasara mmekọrịta mmadụ na ibe ya."
        ),
    },

    # =========== ANIMAL HUSBANDRY ===========
    {
        "id": "anhus_ss1_introduction",
        "subject": "Animal Husbandry",
        "grade": "SS1",
        "topic": "Introduction to Animal Husbandry",
        "content": (
            "Animal husbandry is the science and practice of breeding, feeding, and managing farm animals "
            "for food, income, and other products. "
            "Farm animals are classified as monogastrics — animals with a simple, single-chambered stomach, "
            "such as poultry, pigs, and rabbits — or ruminants — animals with a four-chambered stomach that "
            "can digest fibrous plant material, such as cattle, goats, and sheep. "
            "Animal husbandry contributes to the economy through protein supply, employment, and foreign "
            "exchange from exported animal products. "
            "Common management systems include the intensive system (animals fully confined and managed), "
            "the extensive system (animals allowed to range freely), and the semi-intensive system, which "
            "combines both."
        ),
    },
    {
        "id": "anhus_ss2_nutrition",
        "subject": "Animal Husbandry",
        "grade": "SS2",
        "topic": "Animal Nutrition",
        "content": (
            "A balanced ration supplies an animal with the right proportions of carbohydrates, proteins, "
            "fats, vitamins, minerals, and water needed for growth, maintenance, and production. "
            "Feeds are classified as roughages (bulky, high-fibre feeds like grass and hay) or concentrates "
            "(energy- or protein-dense feeds like maize and soybean meal). "
            "Poor nutrition in farm animals leads to reduced growth rate, lower milk or egg yield, and "
            "greater susceptibility to disease. "
            "Feed formulation combines different feed ingredients in the correct ratio to meet a particular "
            "animal's nutritional requirements at its specific stage of growth or production."
        ),
    },
    {
        "id": "anhus_ss2_health",
        "subject": "Animal Husbandry",
        "grade": "SS2",
        "topic": "Animal Health and Disease Control",
        "content": (
            "Farm animal diseases are caused by bacteria, viruses, parasites, or nutritional deficiencies, "
            "and can spread rapidly in poorly managed, overcrowded housing. "
            "Common diseases include Newcastle disease and coccidiosis in poultry, and foot-and-mouth "
            "disease in cattle, each requiring specific prevention and treatment approaches. "
            "Disease prevention relies on vaccination/immunization, quarantine of new or sick animals, "
            "regular deworming, and maintaining clean housing and feeding equipment. "
            "Signs of a healthy animal include a good appetite, alertness, a shiny coat or plumage, and "
            "normal body temperature; a sick animal typically shows the opposite of these signs."
        ),
    },

    # =========== FOODS AND NUTRITION ===========
    {
        "id": "foodnut_ss1_nutrients",
        "subject": "Foods and Nutrition",
        "grade": "SS1",
        "topic": "Basic Food Nutrients",
        "content": (
            "The six major nutrient classes are carbohydrates, proteins, fats and oils, vitamins, minerals, "
            "and water, each with distinct functions in the body. "
            "Carbohydrates and fats mainly supply energy; proteins are needed for growth and tissue repair; "
            "vitamins and minerals regulate body processes and prevent deficiency diseases. "
            "A deficiency disease results from a prolonged lack of a specific nutrient, e.g. kwashiorkor "
            "from protein deficiency, or scurvy from vitamin C deficiency. "
            "Simple food tests can detect the presence of nutrients in a food sample — for example, iodine "
            "solution turns blue-black in the presence of starch, and Biuret solution turns purple/violet "
            "in the presence of protein."
        ),
    },
    {
        "id": "foodnut_ss2_meal_planning_kitchen",
        "subject": "Foods and Nutrition",
        "grade": "SS2",
        "topic": "Meal Planning and Kitchen Management",
        "content": (
            "Meal planning considers the nutritional needs of the people being fed, the occasion, the "
            "budget available, and the season for food availability. "
            "Nutritional needs differ by group — for example, pregnant and lactating mothers, infants, "
            "adolescents, and the elderly all have different nutrient requirements. "
            "An efficient, safe kitchen is planned with attention to work flow, storage, ventilation, and "
            "the correct selection, use, and care of equipment such as refrigerators and cooking appliances. "
            "Kitchen and food hygiene practices — handwashing, safe food storage temperatures, and proper "
            "waste disposal — prevent foodborne illness and pest infestation."
        ),
    },

    # =========== HEALTH EDUCATION ===========
    {
        "id": "healthed_ss1_diseases",
        "subject": "Health Education",
        "grade": "SS1",
        "topic": "Communicable and Non-Communicable Diseases",
        "content": (
            "A communicable disease can spread from one person to another, e.g. through water/food "
            "(cholera, typhoid fever), insects (malaria, yellow fever), or direct contact (measles, "
            "tuberculosis). "
            "A non-communicable disease, such as hypertension or diabetes, does not spread between people "
            "and is often linked to lifestyle, diet, or genetics. "
            "Prevention of communicable diseases relies on immunization, safe water and sanitation, vector "
            "(e.g. mosquito) control, and personal hygiene. "
            "Environmental health measures — including proper waste disposal, clean water supply, and "
            "pollution control — reduce disease transmission at the community level."
        ),
    },
    {
        "id": "healthed_ss2_drugs_firstaid",
        "subject": "Health Education",
        "grade": "SS2",
        "topic": "Drug Education and First Aid",
        "content": (
            "Drug abuse is the use of a substance in a way not intended or prescribed, which can lead to "
            "drug dependence (a physical or psychological need for the drug) and addiction. "
            "Substances of concern include alcohol, tobacco, and drugs taken orally, by injection, by "
            "inhalation, or topically; each has specific health risks and requires different prevention "
            "approaches such as counselling and rehabilitation. "
            "First aid is the immediate, temporary care given to an injured or suddenly ill person before "
            "full medical treatment is available, aimed at preserving life and preventing the condition "
            "from worsening. "
            "Basic first aid includes controlling bleeding with direct pressure, keeping an unconscious "
            "but breathing casualty in the recovery position, and knowing when to call for professional "
            "medical help."
        ),
    },

    # =========== PHYSICAL EDUCATION ===========
    {
        "id": "pe_ss1_fitness_body_systems",
        "subject": "Physical Education",
        "grade": "SS1",
        "topic": "Physical Fitness and Body Systems",
        "content": (
            "Physical fitness has several components: cardiovascular endurance, muscular strength, "
            "muscular endurance, flexibility, and body composition. "
            "Regular exercise strengthens the cardiovascular system (heart and blood vessels) and the "
            "musculoskeletal system (bones, joints, and muscles), improving overall health and reducing "
            "disease risk. "
            "A warm-up before exercise gradually raises heart rate and loosens muscles to prevent injury; "
            "a cool-down afterward gradually lowers heart rate and aids recovery. "
            "Nutrition, adequate rest, and avoiding harmful substances such as performance-enhancing drugs "
            "all support an athlete's fitness and long-term health."
        ),
    },
    {
        "id": "pe_ss2_games_officiating",
        "subject": "Physical Education",
        "grade": "SS2",
        "topic": "Rules and Officiating of Games and Sports",
        "content": (
            "Each sport has its own set of playing rules governing the size of the field or court, number "
            "of players, scoring method, and fouls — for example, football, athletics, and volleyball each "
            "have distinct rules candidates are expected to know. "
            "Officials such as referees, umpires, and judges enforce these rules during play and ensure "
            "fair competition. "
            "Common fouls and violations include offside in football, a double dribble in basketball, and "
            "a foot fault in athletics, each carrying specific penalties. "
            "Sports administration involves organizing competitions, scheduling fixtures, and managing "
            "facilities and equipment for schools and communities."
        ),
    },

    # =========== TECHNICAL DRAWING ===========
    {
        "id": "techdraw_ss1_geometric_construction",
        "subject": "Technical Drawing",
        "grade": "SS1",
        "topic": "Geometric Construction",
        "content": (
            "Technical drawing uses standard instruments — a T-square, set squares, compasses, and a "
            "scale rule — to produce accurate, to-scale drawings of objects. "
            "Geometric construction covers bisecting lines and angles, constructing regular polygons, and "
            "drawing tangents to circles, all using only a compass and straightedge. "
            "A scale relates the size of a drawing to the actual size of the object, expressed as a ratio "
            "(e.g. 1:50 means 1 unit on the drawing represents 50 units in real life). "
            "Different line types carry specific meanings on a technical drawing — for example, a "
            "continuous thick line shows a visible outline, while a dashed line shows a hidden edge."
        ),
    },
    {
        "id": "techdraw_ss2_orthographic_projection",
        "subject": "Technical Drawing",
        "grade": "SS2",
        "topic": "Orthographic and Auxiliary Projection",
        "content": (
            "Orthographic projection represents a three-dimensional object using multiple two-dimensional "
            "views — typically the front view, top view (plan), and side view (end view). "
            "First-angle projection (used in most of Africa, Europe, and Asia) and third-angle projection "
            "(used mainly in the US) arrange these views differently relative to the object, and candidates "
            "must know which convention a question expects. "
            "Auxiliary projection creates an additional view from an angle other than the standard three, "
            "used to show the true shape of a sloped or inclined surface. "
            "Sectional views show the internal detail of an object by imagining it cut through along a "
            "plane, revealing features that would otherwise be hidden in a normal outside view."
        ),
    },

    # =========== FINE ART ===========
    {
        "id": "fineart_ss1_rationale_tools",
        "subject": "Fine Art",
        "grade": "SS1",
        "topic": "Rationale for Visual Arts and Basic Drawing Tools",
        "content": (
            "WAEC's Fine Art syllabus (examined as Visual Art) opens with the rationale for visual arts: "
            "the concept and scope of visual arts, the vocations it leads to, and the role of art in "
            "national development. "
            "Basic drawing tools, equipment, and materials — pencils, charcoal, ink, brushes, and "
            "supports — are studied for their definition, technique, type, and purpose, alongside how to "
            "prepare, use, care for, and maintain drawing media. "
            "Candidates are examined on their perceptual, analytical, and expressive skills developed "
            "through art activities relating to their environment, and on their knowledge and skill in "
            "using and maintaining art tools and equipment. "
            "The examination has three papers: Paper 1 (40 multiple-choice objective questions, 50 "
            "minutes), Paper 2 (five essay-type questions, of which candidates answer three, 1 hour 30 "
            "minutes), and Paper 3, a two-section practical (drawing/painting, plus lettering/calligraphy "
            "or product design) issued to candidates a fortnight in advance."
        ),
    },
    {
        "id": "fineart_ss1_design_composition_colour",
        "subject": "Fine Art",
        "grade": "SS1",
        "topic": "Basic Design, Composition, and Colour",
        "content": (
            "Basic design and composition covers perspective (definition and types), idea development from "
            "natural and man-made objects, analytical drawing for communication, the design process, "
            "product designing, and two- and three-dimensional drawing/designing. "
            "The elements, principles, and organization of design are examined alongside perception and "
            "colour: colour's definition, the twelve-point colour wheel, sources of colour, colour "
            "terminologies, colour mixing (tints, shades, and gradation), colour harmony, colour philosophy, "
            "colour psychology, colour relationships, and colour perspective. "
            "Colour symbolism — how particular colours carry cultural or emotional meaning — and the "
            "computer as a tool in art (identifying its parts and uses) are also part of this section, "
            "alongside portfolio building and its importance."
        ),
    },
    {
        "id": "fineart_ss2_printmaking_lettering",
        "subject": "Fine Art",
        "grade": "SS2",
        "topic": "Printmaking and Lettering",
        "content": (
            "Printmaking (printing) is examined on its definitions, the tools/materials/equipment used, and "
            "the basic printing processes — direct and indirect methods such as relief printing, intaglio, "
            "lithography, serigraphy, and photographic screen printing — including printing from natural "
            "and artificial surfaces and printing as a means of communication. "
            "Lettering covers the types of lettering, e.g. block lettering (construction of block letters), "
            "calligraphy, upper- and lower-case letters, and the parts of a letter; Gothic (sans serif) "
            "lettering and Roman (serif) lettering are studied for their distinct characteristics, "
            "significance, and functions. "
            "Paper 3's Section B tests lettering/calligraphy or product design, with candidates answering "
            "one of the two within 3 hours for 50 marks."
        ),
    },
    {
        "id": "fineart_ss2_art_history",
        "subject": "Fine Art",
        "grade": "SS2",
        "topic": "Art History: Prehistoric, Ancient, and African Art",
        "content": (
            "Prehistoric art (Paleolithic, Mesolithic, Neolithic) is studied for its beginnings, the "
            "location and development of cave art through the ages, its use in promoting activities like "
            "hunting through sympathetic magic, and the techniques, tools, and materials the caveman used. "
            "Ancient Egyptian art is examined for its purpose (eternity), its characteristic conventions or "
            "canons, and its relevance and influence on other cultures; Greek, Renaissance, Oriental, and "
            "Oceanic art are studied for their distinct periods, major contributions, art forms, and "
            "influence, e.g. Greek art across the Archaic, Classical, and Hellenistic periods, and the "
            "Renaissance as a 'period of rebirth.' "
            "African art is studied through the influence of religious beliefs (animism, magic, myth, "
            "rituals), its functionality, its visual/performing/verbal forms, the main characteristics of "
            "indigenous forms across major West African ethnic groups, and how religion, education, trade, "
            "and politics have acted as agents of change in African art."
        ),
    },
    {
        "id": "fineart_ss3_appreciation_entrepreneurship",
        "subject": "Fine Art",
        "grade": "SS3",
        "topic": "Art Appreciation, Modern Art, and Entrepreneurship",
        "content": (
            "Art appreciation covers the concept of appreciation and its procedure — identification, "
            "inventory, technical qualities, and interpretation — alongside creativity, aesthetics, "
            "criticism, and judgment. "
            "Modern art movements studied include Cubism, Impressionism, Post-Impressionism, "
            "Neo-Impressionism, Fauvism, Expressionism, and Surrealism, each examined for its philosophy, "
            "style, artists, and impact. "
            "Entrepreneurship in visual arts covers setting up and managing an enterprise (financial and "
            "technical assistance, costing and pricing, marketing/selling strategies, business risk, and "
            "exhibition planning), professional ethics (developing a business plan, an artist's statement, "
            "and a business brochure/card), and museum and gallery studies — the definition, history, "
            "functions, administrative structure, and authenticity of museums."
        ),
    },

    # =========== MUSIC ===========
    {
        "id": "music_ss1_rudiments",
        "subject": "Music",
        "grade": "SS1",
        "topic": "Rudiments of Music",
        "content": (
            "Music notation uses a five-line staff, with notes placed on lines and spaces to represent "
            "pitch, and note shapes (e.g. minim, crotchet, quaver) to represent duration. "
            "A scale is a sequence of notes in ascending or descending pitch order; the major scale follows "
            "a fixed pattern of tones and semitones (whole and half steps). "
            "Time signatures (e.g. 4/4, 3/4) show how many beats are in each bar and which note value "
            "represents one beat, establishing the music's rhythm. "
            "Dynamics (such as piano for soft, forte for loud) and tempo markings (such as allegro for "
            "fast, adagio for slow) instruct a performer on how loudly and quickly to play a piece."
        ),
    },
    {
        "id": "music_ss3_african_music",
        "subject": "Music",
        "grade": "SS3",
        "topic": "Traditional and Contemporary African Music",
        "content": (
            "Traditional African vocal music includes genres such as cradle songs/lullabies, ritual songs, "
            "folk songs, praise songs, and satirical songs, each serving a specific social function. "
            "Traditional African instruments are grouped by how they produce sound: membranophones "
            "(drums), idiophones (e.g. xylophones, rattles), aerophones (e.g. flutes, horns), and "
            "chordophones (e.g. the West African kora). "
            "Popular African and Black diaspora music genres studied include highlife, jazz, blues, "
            "gospel, reggae, and Afrobeat, alongside the historical and social conditions that shaped them. "
            "Music is studied in relation to other art forms — its role in dance, drama, and festival "
            "contexts across West African cultures."
        ),
    },

    # =========== OFFICE PRACTICE ===========
    {
        "id": "officeprac_ss1_duties_equipment",
        "subject": "Office Practice",
        "grade": "SS1",
        "topic": "Office Duties and Equipment",
        "content": (
            "An office is the administrative centre of an organization, where records are kept, "
            "correspondence is handled, and business activities are coordinated. "
            "Common office duties include receiving visitors, answering telephone calls, typing "
            "documents, filing records, and handling incoming and outgoing mail. "
            "Office equipment includes the computer, printer, photocopier, telephone, and shredder, each "
            "requiring proper care and safe operating procedures. "
            "A good office worker needs qualities such as punctuality, confidentiality, accuracy, and "
            "good communication skills, since they routinely handle sensitive information and interact "
            "with the public."
        ),
    },
    {
        "id": "officeprac_ss2_filing_correspondence",
        "subject": "Office Practice",
        "grade": "SS2",
        "topic": "Filing, Correspondence, and Reception Duties",
        "content": (
            "Filing systems organize documents so they can be stored and retrieved efficiently — common "
            "methods include alphabetical, numerical, and subject-based filing. "
            "Business correspondence follows set conventions for letters, memos, and emails, including a "
            "clear subject line, formal salutation, and organized body text. "
            "A receptionist's duties include greeting visitors, directing them appropriately, maintaining "
            "a visitors' log, and managing appointments for staff. "
            "Telephone etiquette in an office setting includes answering promptly, speaking clearly, "
            "taking accurate messages, and transferring calls correctly to the right person or department."
        ),
    },

    # =========== STORE MANAGEMENT ===========
    {
        "id": "storemgt_ss1_introduction",
        "subject": "Store Management",
        "grade": "SS1",
        "topic": "Introduction to Store Management",
        "content": (
            "WAEC's Store Management syllabus aims to build understanding of the rudiments of running a "
            "store and entrepreneurial skills, the concepts of wholesaling and retailing, basic business "
            "documents, handling business finance, and the ability to control stock, keep records, and "
            "manage business risk. "
            "Store management covers the meaning and importance of the role, the functions and "
            "characteristics of a store manager, and customer services split into pre-sale and after-sale "
            "services; management itself is examined through its core functions — planning, organization, "
            "leading, staffing, and controlling. "
            "Factors to consider when establishing a store include the market, finance, types of stock, "
            "transport, accessibility, security, government regulation, and personnel. "
            "The examination has two papers combined into one sitting: Paper 1 (50 multiple-choice "
            "questions, 1 hour, 50 marks) and Paper 2 (seven essay questions, of which candidates answer "
            "five, 2 hours, 100 marks)."
        ),
    },
    {
        "id": "storemgt_ss1_retailing_wholesaling_transport",
        "subject": "Store Management",
        "grade": "SS1",
        "topic": "Retailing, Wholesaling, Warehousing, and Transportation",
        "content": (
            "Retailing is examined on its definition and the functions of a retailer, while wholesaling "
            "covers the definition and functions of a wholesaler — the roles that connect producers to the "
            "final consumer. "
            "Warehousing is studied for its meaning, types, and importance in storing goods between "
            "production and sale. "
            "Transportation covers its definition, the means of transportation available, the advantages "
            "and disadvantages of each means, and the factors that determine the choice of transport for a "
            "given store — such as cost, distance, and the nature of the goods being moved."
        ),
    },
    {
        "id": "storemgt_ss2_stock_control",
        "subject": "Store Management",
        "grade": "SS2",
        "topic": "Stock Control and Pricing",
        "content": (
            "Stock control covers the meaning and importance of the practice, and the types of stock "
            "records used, including the stock list, the bin card/store card, the store requisition form, "
            "and delivery notes. "
            "Methods of stock control include the manual method — periodic, perpetual, and annual "
            "stocktaking — and the computerized method; stock is managed against three defined levels, the "
            "maximum level, minimum level, and reorder level, and issued from the store using FIFO "
            "(first-in, first-out) or LIFO (last-in, first-out). "
            "Pricing is studied through its definition and its types: skimming, mark-up, mark-down, "
            "penetration, and below- or above-market pricing, each suiting a different stock or market "
            "situation."
        ),
    },
    {
        "id": "storemgt_ss2_organizational_policy_communication",
        "subject": "Store Management",
        "grade": "SS2",
        "topic": "Organizational Policy, Standards, and Business Communication",
        "content": (
            "Organizational policy covers the definition of policy, employment policy, and decisions on "
            "customer service and public relations; organizational standards define productivity standards "
            "and the standard expected for customer satisfaction; organizational culture defines the shared "
            "attitude to customers, relationships with co-workers and the boss, and dress code within a "
            "store. "
            "Business communication is examined through its definition and types — oral, written, and "
            "non-verbal — and the business documents used, such as letters, memos, reports, and circulars. "
            "Electronic communication covers the means used in a modern store — fax, telephone, email, and "
            "radio messages — and word processing, i.e. using a computer to write business letters."
        ),
    },
    {
        "id": "storemgt_ss3_business_law_record_keeping",
        "subject": "Store Management",
        "grade": "SS3",
        "topic": "Business Law and Record Keeping",
        "content": (
            "Basic business law for a store covers the elements of a contract and the rights and "
            "obligations of employer and employee; agency covers the types of agents, how an agency is "
            "created, and the rights and obligations of principals and agents; the Sale of Goods Act covers "
            "the contract of sale and its formalities. "
            "Government regulation of business covers the meaning and uses of patent right, copyright, and "
            "trademark, the Health and Safety at Work Act, consumer protection agencies, licensing, and "
            "regulatory bodies such as NAFDAC, NDLEA, and SON. "
            "Record keeping covers documentation (filing and indexing definitions, rules, and methods), "
            "source documents (invoices, receipts, cheques, vouchers), and the trade documents used in "
            "foreign trade (e.g. bills of lading, letters of credit) versus home trade (e.g. orders, "
            "waybills, consignment notes)."
        ),
    },
    {
        "id": "storemgt_ss3_bookkeeping_risk_finance",
        "subject": "Store Management",
        "grade": "SS3",
        "topic": "Book Keeping, Risk Management, and Handling Store Finances",
        "content": (
            "Book keeping for store management covers subsidiary books (the purchase and sales day books, "
            "returns inwards/outwards books, and cash books), the imprest system for petty cash, final "
            "accounts (a simple trading, profit and loss account, and balance sheet), and calculating the "
            "rate of sales turnover. "
            "Risk management covers its definition and methods — sound management practices, reducing risk "
            "through an optimum stock level, hedging, and transferring risk through insurance. "
            "Handling the finances of a store covers investments, including capital investment (the "
            "capital market, functions of the Stock Exchange, and advantages of shareholding) and money "
            "market instruments (treasury bills, commercial papers, bonds), and taxation — the meaning and "
            "importance of tax and its types, including income tax, import duties, excise duties, and VAT."
        ),
    },

    # =========== FRENCH ===========
    {
        "id": "french_ss1_grammar_basics",
        "subject": "French",
        "grade": "SS1",
        "topic": "Basic French Grammar (Structure)",
        "content": (
            "WAEC's French syllabus tests structure within communicative contexts, covering articles "
            "(definite, indefinite, and partitive, with gender and number agreement where applicable), "
            "verbs (regular and irregular types, common moods and tenses, and standard expressions such as "
            "'avoir + noun', e.g. avoir faim, and 'venir de + infinitive'), and nouns (their complements, "
            "gender, and number). "
            "Pronouns tested include personal, possessive, indefinite, demonstrative, relative, and "
            "impersonal pronouns; adjectives tested include possessive, demonstrative, indefinite, and "
            "interrogative adjectives, examined for their agreement and position. "
            "Adverbs are tested for their formation and position, including special adverbs such as mal, "
            "vite, fort, and tout; negative expressions (ne...pas, ne...rien, ne...jamais) and common "
            "conjunctions (et, mais, donc, ou, parce que) and prepositions (à, de, sur, en, devant) are "
            "also examined."
        ),
    },
    {
        "id": "french_ss2_paper1_comprehension_structure",
        "subject": "French",
        "grade": "SS2",
        "topic": "Paper 1: Comprehension and Structure",
        "content": (
            "Paper 1 (1 hour, 40 marks, 40 multiple-choice questions) has two sections. "
            "Section A, Comprehension, tests candidates' ability to read and understand standard written "
            "documents in French: two passages of about 150 words each are provided, with five short "
            "multiple-choice questions set on each passage. "
            "Section B, Structure, tests candidates' ability to use French words, expressions, and "
            "structural patterns correctly in appropriate communicative contexts, through thirty short "
            "questions that candidates must all attempt. "
            "Sentence patterns tested include declarative, interrogative, and exclamative forms; active and "
            "passive voice; direct and reported speech; compound and complex sentences; and idiomatic "
            "expressions and proverbs."
        ),
    },
    {
        "id": "french_ss2_paper2_paper3_essay_oral",
        "subject": "French",
        "grade": "SS2",
        "topic": "Paper 2 (Essay/Letter) and Paper 3 (Oral)",
        "content": (
            "Paper 2 (1 hour 15 minutes, 40 marks) has two sections — an essay and a letter — testing "
            "candidates' ability to write freely and correctly on topics of general interest, using "
            "appropriate structure, register, and tense; three questions are set for each section, and "
            "candidates answer one from each, at about 100 words per composition. "
            "Paper 3 (50 marks) tests listening comprehension, reading, and conversation. The listening "
            "test is based on a roughly 200-word passage read aloud twice by the examiner, with 10 "
            "questions to answer afterward; the reading test asks candidates to read aloud a roughly "
            "100-word passage with appropriate pronunciation and fluency; the conversation test lasts about "
            "10 minutes per candidate and has two parts — a dialogue section (responding to a minimum of 10 "
            "questions) and an exposition section (speaking freely on a given topic in at least 5 "
            "sentences)."
        ),
    },
    {
        "id": "french_ss3_vocabulary_communication",
        "subject": "French",
        "grade": "SS3",
        "topic": "Everyday Vocabulary and Communicative Skills",
        "content": (
            "Common everyday vocabulary themes tested include greetings (bonjour, comment ça va?), family "
            "members (la famille, le frère, la sœur), numbers, days of the week, and telling the time. "
            "Candidates are also expected to master common figures of speech (e.g. similes, metaphors, "
            "hyperboles), context and meaning (e.g. conveying politeness, disgust, disappointment), forms "
            "of writing (formal versus informal), and the structures of major 'Actes de Parole' such as "
            "expressing deception, disapproval, disgust, surprise, pleasure, or regret. "
            "The WAEC syllabus recommends extracts from simple modern literary and other texts — magazines, "
            "newspapers, brochures — dealing with contemporary issues to build comprehension skills for the "
            "exam."
        ),
    },

    # =========== ARABIC ===========
    # NOTE: unlike Fine Art, Store Management, French, Edo, Efik, and Ibibio
    # above, Arabic could NOT be cross-checked in the July 2026 pass —
    # waecsyllabus.com does not currently publish an Arabic syllabus page
    # (it is absent from the site's full subject index, even though it
    # appears in some third-party "merged language texts 2026-2030" lists).
    # These entries remain written from general subject knowledge, not a
    # directly sourced WAEC syllabus document, and still need review against
    # an official WAEC Arabic syllabus PDF if/when one can be located.
    {
        "id": "arabic_ss1_grammar_basics",
        "subject": "Arabic",
        "grade": "SS1",
        "topic": "Basic Arabic Grammar",
        "content": (
            "Arabic words are traditionally classified into three types: ism (noun), fi'l (verb), and "
            "harf (particle, e.g. a preposition or conjunction). "
            "Arabic is written and read from right to left, and most letters change shape slightly "
            "depending on their position within a word (initial, medial, final, or isolated). "
            "Arabic nouns and adjectives carry grammatical gender (masculine or feminine) and number "
            "(singular, dual, or plural), with the adjective agreeing with the noun it describes. "
            "A basic Arabic sentence can be a nominal sentence (starting with a noun, e.g. 'the book is "
            "new') or a verbal sentence (starting with a verb, e.g. 'the student wrote')."
        ),
    },
    {
        "id": "arabic_ss2_comprehension_composition",
        "subject": "Arabic",
        "grade": "SS2",
        "topic": "Arabic Comprehension and Composition",
        "content": (
            "Comprehension exercises test a candidate's ability to read a short Arabic passage and answer "
            "questions on its meaning, main ideas, and specific details. "
            "Composition (insha') tests the ability to write connected, grammatically correct Arabic "
            "prose on a given topic, often drawing on everyday or Islamic cultural themes. "
            "Translation exercises move between Arabic and English (or a local language), testing both "
            "vocabulary knowledge and correct grammatical structure in the target language. "
            "Arabic literature studied at this level often includes short prose extracts and poetry, "
            "requiring candidates to identify theme and basic literary features, similar to literature "
            "study in other languages."
        ),
    },

    # =========== EDO LANGUAGE ===========
    {
        "id": "edo_ss1_sound_grammar",
        "subject": "Edo Language",
        "grade": "SS1",
        "topic": "Sound System and Grammar of Edo",
        "content": (
            "WAEC's Edo sound system component covers vowels, consonants, and the syllabic nasal, their "
            "production in terms of place and manner of articulation, and their basic phonetic and "
            "phonemic classification, alongside syllable structure — how consonants and vowels combine. "
            "Sound processes tested include vowel harmony, assimilation, and elision, together with the "
            "sound-system aspects of the Edo orthography and tone/tone notation. "
            "Edo grammar covers word structure and word formation, basic and derived numerals, word "
            "classes (nouns, verbs, adverbs, pronouns, adjectives), grammatical categories (subject, "
            "object, complement, predicate, number, person, tense, aspect, mood), and the structure of "
            "phrases, clauses, and sentence types. "
            "In the WAEC exam, this Language section carries 30 of Paper 1's 60 objective items and forms "
            "three of the six essay questions candidates answer in Paper 2."
        ),
    },
    {
        "id": "edo_ss2_literature",
        "subject": "Edo Language",
        "grade": "SS2",
        "topic": "Edo Oral and Written Literature",
        "content": (
            "Edo oral literature is examined through three set books covering prose, poetry, and drama — "
            "for 2026-2030 these are Okha Edo (prose, by Emovon & Osemwegie), Poems in Bini (poetry, by "
            "Ikponmwonsa & Osemwegie), and Eseikho (drama, by Ikponmwosa & Osemwegie) — with one question "
            "set per set book. "
            "Written Edo literature likewise has three set books for 2026-2030: Izelogha (prose) and "
            "Meokpaghare (drama), both by Osayomwanbo Osemwegie-Ero, and Asikoko Ekharha O ghe E do "
            "(poetry) by Obazee Gabriel et al. "
            "Candidates also study Basic Principles of Literary Appreciation, examined through 4 objective "
            "items in Paper 1 alongside the 9 oral-literature and 9 written-literature items (3 each for "
            "prose, poetry, and drama)."
        ),
    },
    {
        "id": "edo_ss3_culture",
        "subject": "Edo Language",
        "grade": "SS3",
        "topic": "Edo Customs and Institutions",
        "content": (
            "Edo customs tested include make-up and adornments, indoor and outdoor games, pregnancy and "
            "its care, names and naming ceremonies, home training (greetings, respect for superiors, "
            "cleanliness, tolerance, integrity, hard work), Edo foods, non-verbal communication, and "
            "traditional versus modern funeral and inheritance methods. "
            "Edo institutions tested include traditional occupations, marriage, the political structure "
            "(family structure, age grades, chieftaincy, and the Obaship), child care, ancestors, Edo "
            "beliefs about Osalobua/Osanobua (God) and other deities, modern religions such as Islam and "
            "Christianity, and the economy (adverts, money lending, cooperative efforts). "
            "Culture questions form 8 of Paper 1's 60 objective items (4 on customs, 4 on institutions) and "
            "one of the six essay questions in Paper 2, which is answered entirely in Edo using the "
            "official Edo orthography and metalanguage."
        ),
    },

    # =========== EFIK LANGUAGE ===========
    {
        "id": "efik_ss1_sound_grammar",
        "subject": "Efik Language",
        "grade": "SS1",
        "topic": "Sound System and Grammar of Efik",
        "content": (
            "WAEC's Efik Language section is tested through comprehension (2 short passages), "
            "composition/letter writing, sound system, word and sentence structure, and translation, "
            "together making up 30 of Paper 1's 60 objective items. "
            "Composition/letter writing in Paper 2 draws on essay types such as narrative, descriptive, "
            "argumentative, expository, dialogue, debate, and letter writing, with candidates advised to "
            "write about 300 words in no more than 45 minutes. "
            "Both Paper 1 and Paper 2 use the standard Efik orthography and metalanguage, and all rubrics "
            "and answers must be written in Efik."
        ),
    },
    {
        "id": "efik_ss2_literature",
        "subject": "Efik Language",
        "grade": "SS2",
        "topic": "Efik Oral and Written Literature",
        "content": (
            "Efik oral literature is examined through three genres — prose (folktales, legends, proverbs, "
            "riddles), poetry (songs, ballads), and drama (traditional drama) — with set books for "
            "2026-2030 including Mutanda oyom Namondo (prose) by E. E. Nkana, Nkpon udan (poetry) by "
            "Essien-Eyo et al., and Inyan Abasi Ndem (drama) by E. N. Amaku. "
            "Written Efik literature likewise has three set books covering the same genres: Edikot nwed "
            "mbuk 6 (prose) by E. N. Amaku, Nkpasip nkpo kiet (poetry) by Essien-Eyo et al., and Sidibe "
            "(drama) by E. A. Edyang. "
            "Candidates answer two of six possible literature questions in Paper 2 — one on Oral Literature "
            "and one on Written Literature — and Section B contributes 22 of Paper 1's 60 objective items, "
            "including 4 on Basic Principles of Literary Appreciation."
        ),
    },
    {
        "id": "efik_ss3_culture",
        "subject": "Efik Language",
        "grade": "SS3",
        "topic": "Efik Customs and Institutions",
        "content": (
            "Efik customs (Edu Uwem) tested include traditional occupations, traditional food and its "
            "preparation (such as fufu and efere), funeral practices (ikpo), and the practice of libation "
            "(uduọk mmịn). "
            "Efik institutions tested include the family/kinship structure (ubon/ekpuk), religious "
            "institutions and worship (of Abasi, Ndem, Ibọk, and Mbukpo), Efik proverbs, and secret "
            "societies unique to Efik culture (mme ndedịbe nka ke Efịk). "
            "Culture questions make up 8 of Paper 1's 60 objective items (4 on customs, 4 on institutions) "
            "and one of the six essay questions candidates answer in Paper 2, entirely in Efik using the "
            "standard orthography and metalanguage."
        ),
    },

    # =========== IBIBIO LANGUAGE ===========
    {
        "id": "ibibio_ss1_sound_grammar",
        "subject": "Ibibio Language",
        "grade": "SS1",
        "topic": "Sound System and Grammar of Ibibio",
        "content": (
            "WAEC's Ibibio sound system component covers vowels, consonants, and the syllabic nasal — "
            "their place and manner of articulation and basic phonetic/phonemic classification — syllable "
            "structure, sound processes such as vowel harmony and the assimilation of loan words, and tone "
            "and tone intonation (high, low, falling, and rising tone). "
            "Ibibio grammar covers word structure and formation (root, affixes, suffixes, prefixes, "
            "compounding, borrowing, reduplication), word classes (noun, verb, adverb, pronoun, adjective, "
            "conjunction, preposition), grammatical categories (number, person, tense, negation), and "
            "phrase, clause, and sentence structure — including complex, compound, and simple sentences and "
            "their function (interrogative, declarative, negative). "
            "In the exam, Language makes up 30 of Paper 1's 60 objective items, and candidates attempt "
            "essay/letter writing plus one question each on sound system and grammar in Paper 2."
        ),
    },
    {
        "id": "ibibio_ss2_literature",
        "subject": "Ibibio Language",
        "grade": "SS2",
        "topic": "Ibibio Oral and Written Literature",
        "content": (
            "Ibibio oral literature covers prose (folktales, legends, proverbs, riddles), poetry (songs, "
            "ballads), and drama (traditional drama); set texts for 2026-2030 include Mbak anyan-idaha "
            "(prose) by Udonkwak, Kap Toiyo: Mme uto Ibibio (poetry) by Udoh & Etim, and Mbre ke Ibibio: Ma "
            "nkpo mfo (drama) by Umo. "
            "Written Ibibio literature covers the same three genres, with set texts including Ufoknwed idon "
            "(prose) by Udonkwak, Mben idim anie adion (poetry) by Ekpo, Solomon & Benson, and Uwa (drama) "
            "by Andy. "
            "Literature makes up 22 of Paper 1's 60 objective items (including 4 on Basic Principles of "
            "Literary Appreciation), and candidates must answer questions on both Oral and Written "
            "Literature within Paper 2's thirteen available essay questions."
        ),
    },
    {
        "id": "ibibio_ss3_culture",
        "subject": "Ibibio Language",
        "grade": "SS3",
        "topic": "Ibibio Customs and Institutions",
        "content": (
            "Ibibio customs and institutions tested include family structure (ubon/ekpuk), religious "
            "institutions and worship (of Abasi, Ndem, Ibọk, Ndukpo), traditional food (ndidia/fufu/efere), "
            "funerals (ikpo), and named traditional festivals (mme usọrọ/Mbre Ibibio) tied to the farming "
            "and religious calendar. "
            "Also tested are taboos (ibed), traditional education (edu uwem/ukpeep), coronation (uyad "
            "ntinya), maiden fattening (mboppo), traditional rites (ndutọm idọ), traditional societies (mme "
            "ọka Ibibio), the Ibibio worldview, and naming practices (enyọng ke Ibibio). "
            "This section forms 8 of Paper 1's 60 objective items (4 on customs, 4 on institutions), and "
            "one Culture question out of the six candidates must answer in Paper 2."
        ),
    },
    {
        "id": "automech_ss1_safety_tools_vehicle_layout",
        "subject": "Auto Mechanics",
        "grade": "SS1",
        "topic": "Workshop Safety, Tools, and Vehicle Layout",
        "content": (
            "Workshop safety covers the causes of workshop accidents and accident prevention "
            "techniques and safety devices, such as sand buckets and fire extinguishers. "
            "Tools and equipment are studied by type and use — marking, measuring, holding, and "
            "cutting tools, plus equipment such as hand valves and grinding tools — alongside "
            "their proper maintenance. "
            "Vehicle layout covers the types of motor vehicle chassis, the principal components "
            "of a vehicle (engine, transmission system, chassis) and their identification and "
            "functions, and chassis maintenance. "
            "WAEC's scheme of examination has three papers: Paper 1 (40 multiple-choice questions, "
            "45 minutes, 40 marks), Paper 2 (10 short-structured questions plus 5 essay questions "
            "of which candidates answer 4, 2 hours 15 minutes, 80 marks total), and Paper 3, a "
            "practical test (2 hours 30 minutes, two compulsory questions, 80 marks), with an "
            "alternative-to-practical theory paper available if materials cannot be sourced."
        ),
    },
    {
        "id": "automech_ss2_engine_transmission_systems",
        "subject": "Auto Mechanics",
        "grade": "SS2",
        "topic": "Engine, Transmission, and Support Systems",
        "content": (
            "The automobile engine topic covers types of engine design, identification of main "
            "engine components, two-stroke versus four-stroke cycles (spark ignition and "
            "compression ignition engines), and the advantages of a four-stroke cycle over a "
            "two-stroke engine. "
            "The transmission system covers the layout, types of drives, and components such as "
            "clutches and gearboxes, including the operation of a simple plate clutch and an "
            "introduction to automatic transmission systems. "
            "The suspension system covers types and functions of suspension, plus fault-finding, "
            "maintenance, and repair; the steering system covers components, types of steering "
            "gearbox, manual steering faults and repairs, power-assisted steering, and steering "
            "geometry. "
            "The engine lubrication system covers the purpose and types of lubrication, friction "
            "and its disadvantages, and the quality, viscosity, and additives used in lubricants; "
            "the cooling system covers the function and types of water and air cooling systems."
        ),
    },
    {
        "id": "automech_ss3_fuel_braking_workshop_management",
        "subject": "Auto Mechanics",
        "grade": "SS3",
        "topic": "Fuel Systems, Braking, Wheels, and Workshop Management",
        "content": (
            "Fuels and combustion covers the layout and working principle of the fuel supply "
            "system, types of carburetors and pumps and their maintenance, types and properties "
            "of fuel, and the manifold, air cleaner, and muffler. "
            "The braking system covers the concept of friction and operating principles of braking "
            "systems, faults and maintenance of mechanical and hydraulic brakes, and the "
            "functions and advantages of the anti-lock braking system (ABS). "
            "Wheels and tyres cover the types and functions of rims and tyres, vulcanizing, "
            "regulations for tyre interchange and pressure, and road wheel alignment and "
            "balancing. "
            "Workshop management and enterprise covers the basic concepts of management "
            "(planning, organizing, controlling, staffing, directing), managing resources, and "
            "the advantages and disadvantages of different types of enterprise in the automobile "
            "trade."
        ),
    },
 
    # =========== BASKETRY ===========
    # Source: https://waecsyllabus.com/basketry/
    {
        "id": "basketry_ss1_meaning_materials_tools",
        "subject": "Basketry",
        "grade": "SS1",
        "topic": "Meaning, Materials, and Tools of Basketry",
        "content": (
            "Basketry covers areas such as coiled work, woven articles, frameworks, and macrame, "
            "used to make articles such as baskets, hats, mats, nets, and footwear using "
            "techniques of weaving, plaiting, coiling, stitching, and knotting. "
            "The rationale for studying basketry includes the creative use of materials for "
            "articles of cultural, functional, and aesthetic value, skills acquisition for "
            "employment and further study, and tourism promotion. "
            "Preparation of materials covers techniques such as drying and wetting, storage and "
            "care of materials by chemical and non-chemical methods, and preservation of material "
            "sources such as protecting against bush burning. "
            "Tools and their uses are studied by category, description, and use, including "
            "drawing and labelling tools, improvisation of tools, and their care, maintenance, "
            "and safety precautions."
        ),
    },
    {
        "id": "basketry_ss2_design_decoration",
        "subject": "Basketry",
        "grade": "SS2",
        "topic": "Design, Decoration, and Finishing in Basketry",
        "content": (
            "The elements of design in basketry — dot, line, shape, and others — are identified in "
            "the environment and created using techniques such as knotting and weaving, alongside "
            "study of the twelve-point colour wheel. "
            "The principles of design (unity, balance, proportion, repetition) are identified and "
            "created using techniques such as spraying, scorching, and weaving. "
            "Designing articles to suit specific needs covers designing by hand or computer to "
            "satisfy specific needs, and criteria for appreciation and evaluation such as "
            "appropriate material, colour, technique, and finishing. "
            "Decoration and finishing cover processes such as the use of coloured and uncoloured "
            "weavers, weave variations, scorching, and spraying for decoration, and wrapping, "
            "binding, singeing, tying, trimming, sanding, and varnishing for finishing."
        ),
    },
    {
        "id": "basketry_ss3_sustainability_entrepreneurship",
        "subject": "Basketry",
        "grade": "SS3",
        "topic": "Sustainable Development and Entrepreneurship in Basketry",
        "content": (
            "Sustainable development of basketry covers strategies for sustainable sourcing of "
            "raw materials, such as re-afforestation and waste management, and challenges facing "
            "the industry, such as competition from plastic products. "
            "Entrepreneurial skills in practice cover building a portfolio (prints, photos, CDs), "
            "writing a business plan, and steps toward business organization such as registration "
            "and market survey. "
            "The business topic covers sources of capital such as bank loans and cooperatives, "
            "types of exhibition, and business promotion methods such as billboards, internet, "
            "and print media. "
            "Costing and pricing cover variable cost, fixed cost, and profit, and the factors that "
            "determine price; WAEC's scheme of examination has three papers — Paper 1 (40 "
            "objective questions, 50 minutes, 40 marks), Paper 2 (six essay questions, answer "
            "four, 2 hours, 60 marks), and Paper 3, two practical projects of which one is "
            "executed over five days for 80 marks, plus 20 marks for design sketches prepared in "
            "advance."
        ),
    },
 
    # =========== BUSINESS MANAGEMENT ===========
    # Source: https://waecsyllabus.com/business-management/
    {
        "id": "busmgt_ss1_nature_functions_of_management",
        "subject": "Business Management",
        "grade": "SS1",
        "topic": "Nature and Functions of Management",
        "content": (
            "The nature of management covers the meaning of management and administration, the "
            "basic functions and levels of management, and the major forms of business "
            "organization — sole proprietorship, partnership, limited liability company, public "
            "corporations, and cooperative society. "
            "Business and society covers the meaning of the business environment, the forces "
            "within it, and the ethical, legal, and social responsibilities of businesses toward "
            "primary and secondary stakeholders. "
            "The functions of management cover planning and decision-making (steps in planning, "
            "types of decisions), organizing (organizational structure, centralization versus "
            "decentralization, delegation), directing (motivation, Maslow's Hierarchy of Needs, "
            "leadership styles, communication), and controlling (steps and tools for control). "
            "WAEC's scheme of examination has two composite papers taken in one sitting: Paper 1 "
            "(50 compulsory multiple-choice questions, 1 hour, 30 marks) and Paper 2 (a compulsory "
            "200-250 word case study worth 25 marks plus three of seven essay questions worth 15 "
            "marks each, totalling 70 marks)."
        ),
    },
    {
        "id": "busmgt_ss2_legal_environment_finance",
        "subject": "Business Management",
        "grade": "SS2",
        "topic": "Legal Environment, Finance, and Government's Role in Business",
        "content": (
            "The legal environment of business covers the meaning and elements of a contract, "
            "classification of contracts, vitiating factors, the principles of agency, and "
            "negotiable instruments such as cheques, bills of exchange, and promissory notes. "
            "Finance and financial institutions cover the meaning and functions of money, causes "
            "of inflation, types and functions of banks, tools of monetary control, and risk "
            "management and the principles and types of insurance. "
            "The role of government in the economy covers sources and types of government "
            "revenue, the purpose of taxation, types of taxes, and types of government "
            "expenditure. "
            "International trade and economic integration cover the difference between domestic "
            "and international trade, theories of absolute and comparative cost advantage, "
            "balance of payments, and the roles of ECOWAS, the African Union, and the European "
            "Union in economic integration."
        ),
    },
    {
        "id": "busmgt_ss3_functional_management_entrepreneurship",
        "subject": "Business Management",
        "grade": "SS3",
        "topic": "Functional Management and Entrepreneurship",
        "content": (
            "Human resource management covers the steps in recruitment and selection, types of "
            "training, job analysis, and performance appraisal, while labour relations covers "
            "trade unions, employers' associations, and the collective bargaining process. "
            "Production management covers the forms of production (extractive, manufacturing, "
            "construction, commercial, personal services), the factors of production, and types "
            "of production process (job, batch, flow), while the principles of marketing cover "
            "market segmentation, the marketing mix, and the stages of the product life cycle. "
            "Electronic commerce and business finance cover the meaning and importance of "
            "e-commerce and the short-term and long-term sources of business finance, including "
            "government lending programmes and venture capital funds. "
            "Entrepreneurship and small business covers the characteristics of an entrepreneur, "
            "the content of a business plan, reasons for business success and failure, and the "
            "role of government in promoting and sustaining small businesses."
        ),
    },
 
    # =========== FISHERY ===========
    # Source: https://waecsyllabus.com/fisheries-alt-b/
    # NOTE: source page/PDF title is "Fisheries" (plural) - see caveat in
    # module docstring above; verify exact subject name string before use.
    {
        "id": "fishery_ss1_basic_concepts_production",
        "subject": "Fishery",
        "grade": "SS1",
        "topic": "Basic Concepts and Processes of Fish Production",
        "content": (
            "Basic concepts in fisheries cover the meaning of fisheries and its sub-divisions, "
            "and its importance to the socio-economic development of West Africa. "
            "Processes of fish production are divided into capture fisheries, which covers "
            "different methods and materials for catching wild fish, and culture fisheries, which "
            "covers identifying culturable fish species and the facilities used to farm them. "
            "Types of fish culture facilities cover the types and components of fish ponds and "
            "the types and management systems of aquaculture. "
            "Water quality control and monitoring covers the definition and parameters of water "
            "quality, methods of monitoring it, and the effects of water pollution on fishery "
            "resources — one of WAEC's stated aims for the subject."
        ),
    },
    {
        "id": "fishery_ss2_feeding_pond_management",
        "subject": "Fishery",
        "grade": "SS2",
        "topic": "Fish Feeding and Pond Management",
        "content": (
            "Fish feeds and feeding covers identification of different fish feed materials and "
            "their nutritive value, the feeding regime and ideal feeding periods for fish, and "
            "methods of feeding. "
            "Fish pond preparation and management covers pond construction, the tools required "
            "for pond preparation, preparing ponds for stocking, and ongoing pond management "
            "practices. "
            "Fish seed production covers brood stock selection and handling, the differences "
            "between male and female sexually mature fish, and the meaning, steps, and equipment "
            "of artificial breeding. "
            "Schools offering the subject are required to have at least a small aquarium and a "
            "fish pond or concrete tank, and are recommended to keep practical notebooks and take "
            "field trips to fish farms and fisheries research institutions."
        ),
    },
    {
        "id": "fishery_ss3_harvesting_processing_exam",
        "subject": "Fishery",
        "grade": "SS3",
        "topic": "Fish Harvesting, Processing, and Examination Structure",
        "content": (
            "Fish harvesting and post-harvesting covers fishing gear, its construction and "
            "mending, methods of fish harvesting, and fishing crafts, followed by post-harvest "
            "handling — methods of fish preservation, packaging materials, and marketing "
            "channels. "
            "Practical fisheries covers fish culture (environmental conditions, tools, common "
            "culturable species), fishing gear and craft, and fish processing and preservation, "
            "including the equipment used and the resulting products and by-products. "
            "WAEC's scheme of examination has three papers: Paper 1 (40 multiple-choice "
            "questions, 40 minutes, 40 marks), Paper 2 (six essay questions, answer four, 2 hours, "
            "80 marks), and Paper 3, a practical paper for school candidates or an "
            "alternative-to-practical paper for private candidates, each with four questions to "
            "be answered in 1.5 hours for 60 marks. "
            "Stated aims of the subject include building basic entrepreneurial skills in "
            "fisheries-related vocations alongside the technical skills in fish farming."
        ),
    },
 
    # =========== HOME MANAGEMENT ===========
    # Source: https://waecsyllabus.com/home-management/
    {
        "id": "homemgt_ss1_principles_family_living",
        "subject": "Home Management",
        "grade": "SS1",
        "topic": "Principles of Management and Family Living",
        "content": (
            "The management process in the home covers planning, organization, implementation, "
            "and evaluation, applied to specific household tasks, and is motivated by personal "
            "characteristics, values, goals, standards, and needs. "
            "Family resources are classified as human (time, energy, skill), non-human/material, "
            "and community resources, and decision-making is studied through its definition and "
            "process, alongside the management of time and energy. "
            "Family living covers types of family (nuclear, monogamous, polygamous, extended) "
            "with their advantages and disadvantages, the family life cycle, the roles and "
            "responsibilities of family members, and factors affecting family relationships such "
            "as communication and family values, including conflict and conflict resolution. "
            "Courtship, marriage, and parenthood cover factors to consider when choosing a life "
            "partner (such as blood group, genotype, and HIV status), preparation for marriage, "
            "and preparation for parenthood including antenatal care, childbirth, and immunization."
        ),
    },
    {
        "id": "homemgt_ss2_feeding_clothing_housing",
        "subject": "Home Management",
        "grade": "SS2",
        "topic": "Feeding, Clothing, and Housing the Family",
        "content": (
            "Feeding the family covers the classes of food nutrients, the effect of heat on "
            "nutrients, the special nutritional needs of groups such as infants, pregnant women, "
            "and the aged, and food storage, purchasing, preparation, and serving. "
            "Clothing the family covers the meaning, types, and functions of clothing, the origin "
            "and classification of fibres and fabrics, wardrobe planning, and maintenance topics "
            "such as laundry agents, stain removal, and simple garment repairs. "
            "Housing the family covers the definition and types of houses, ways of acquiring a "
            "house (renting, mortgage, building, buying), and the economic, social, and "
            "psychological factors influencing the choice of a family house. "
            "Setting up a home covers the difference between a home and a house, types of "
            "equipment and furnishing, and home improvement/interior decoration, including the "
            "elements and principles of art and design such as colour, texture, and proportion."
        ),
    },
    {
        "id": "homemgt_ss3_utilities_wealth_consumer_education",
        "subject": "Home Management",
        "grade": "SS3",
        "topic": "Home Utilities, Wealth Creation, and Consumer Education",
        "content": (
            "Utilities in the home cover the sources, uses, purification, and storage of water; "
            "electricity, including meter reading and electric bills; and fuels such as cooking "
            "gas, kerosene, and firewood, with their uses, storage, and advantages/disadvantages. "
            "Safety measures in the home cover common accidents and their prevention, the use of "
            "first aid, sanitation and waste disposal methods, and the control of household pests. "
            "Wealth creation and management covers creativity and entrepreneurship (with example "
            "enterprises such as fashion designing, hairdressing, and fast foods), money "
            "management and family budgeting, and capital market investment opportunities such as "
            "stocks, shares, and treasury bills. "
            "Consumer education covers the rights and responsibilities of a consumer, sources and "
            "uses of consumer information, consumer legislation and agencies, and wise purchasing "
            "practices such as conducting a market survey; WAEC's scheme has three papers — Paper "
            "1 (50 objective questions, 1 hour, 50 marks), Paper 2 (six essay questions, answer "
            "four, 1 hour 15 minutes, 50 marks), and Paper 3, a 3-hour practical test worth 100 "
            "marks conducted by a visiting WAEC-appointed examiner."
        ),
    },
 
    # =========== PAINTING AND DECORATING ===========
    # Source: https://waecsyllabus.com/painting-decorating/
    {
        "id": "paintdec_ss1_introduction_colour_theory",
        "subject": "Painting and Decorating",
        "grade": "SS1",
        "topic": "Introduction to Painting and Colour Theory",
        "content": (
            "Painting and Decorating distinguishes pictorial painting (representational, "
            "picture-based work) from decorative painting, and covers the tools, equipment, and "
            "elements and principles of design used in both. "
            "Colour theory covers the meaning of colour, the classes of colour (primary, "
            "secondary, tertiary), the properties of colour (hue, tone, intensity), colour "
            "schemes such as analogous, complementary, and monochrome, and the improvisation of "
            "colours from local sources. "
            "Techniques in pictorial painting include dry painting, wet painting, glazing, "
            "impasto, fresco, and tempera, while techniques in decorative painting include flat "
            "painting, rag rolling, scumbling or combing, spraying, mural, and mosaic. "
            "WAEC's stated aims include developing skill in painting and decorating, "
            "understanding of modern trends in the field, and knowledge of job and wealth creation "
            "through painting and decorating."
        ),
    },
    {
        "id": "paintdec_ss2_types_functions_perspective",
        "subject": "Painting and Decorating",
        "grade": "SS2",
        "topic": "Types of Painting, Perspective, and Prospects",
        "content": (
            "Types and functions of pictorial painting include still life, nature painting, and "
            "figure/life painting, distinguished as observatory (drawn from direct observation) "
            "versus imaginative painting compositions. "
            "Types and functions of decorative painting include body decoration — comparing "
            "traditional and modern body decoration, its motifs, materials, and functions — and "
            "wall/interior decoration, comparing traditional and modern wall decoration, its "
            "motifs, patterns, and materials. "
            "Perspective covers its meaning, types, and importance in a pictorial painting "
            "composition. "
            "Prospects in painting cover the socio-economic value of pictorial and decorative "
            "painting and the careers available in the field."
        ),
    },
    {
        "id": "paintdec_ss3_costing_marketing_exam",
        "subject": "Painting and Decorating",
        "grade": "SS3",
        "topic": "Costing, Marketing, and Examination Structure",
        "content": (
            "Costing of pictorial and decorative painting is based on the location and size of "
            "the work, materials and equipment involved, time invested, and quantity and quality "
            "of the piece. "
            "Exhibiting paintings covers planning, processes, and funding, while marketing covers "
            "pricing, negotiation, communication (advertising and publicity), and outlets for "
            "sale. "
            "WAEC's scheme of examination has three papers: Papers 1 and 2 form a composite paper "
            "taken in 3 hours — Paper 1 has 40 multiple-choice questions for 40 marks, and Paper 2 "
            "has six essay questions of which candidates answer four for 60 marks; Paper 3, "
            "'Decorative Painting,' gives candidates two alternative tasks of which they attempt "
            "one, rendered in poster or acrylic colours, over 3 hours for 100 marks. "
            "The practical paper's requirements are released to candidates at least two weeks in "
            "advance, but the actual work must be executed under WAEC supervision in the "
            "examination hall."
        ),
    },
 
    # =========== REFRIGERATION AND AIR CONDITIONING ===========
    # Source: https://waecsyllabus.com/refrigeration-air-conditioning/
    {
        "id": "rac_ss1_safety_temperature_pressure",
        "subject": "Refrigeration and Air Conditioning",
        "grade": "SS1",
        "topic": "Workshop Safety, Temperature, and Pressure",
        "content": (
            "Safety and first aid in the workshop cover workshop rules and regulations, safety "
            "devices such as helmets, goggles, and fire extinguishers, and the causes and "
            "prevention of accidents. "
            "Temperature is studied through different types of thermometers (gas, resistance, "
            "liquid, thermocouple) and temperature scale conversions between Celsius, Fahrenheit, "
            "and Kelvin, including reference points such as the triple point of water at 0.01°C. "
            "Pressure is studied through pressure-measuring devices such as barometers, "
            "manometers, and bourdon tube gauges, and the use of suction and high-pressure gauges "
            "to determine a refrigerant's performance. "
            "The effects of temperature, pressure, and volume in refrigeration systems are "
            "examined through the gas laws — Boyle's law, Charles' law, and Dalton's law — and "
            "calculations using the general gas law formula P1V1/T1 = P2V2/T2."
        ),
    },
    {
        "id": "rac_ss2_refrigeration_cycle_components",
        "subject": "Refrigeration and Air Conditioning",
        "grade": "SS2",
        "topic": "The Refrigeration Cycle and System Components",
        "content": (
            "The refrigeration cycle consists of evaporation, compression, condensation, and "
            "expansion, and candidates study the layout diagrams, types, and operating principles "
            "of refrigeration systems, along with the functions of components such as relays, "
            "solenoid valves, capacitors, and thermostats. "
            "Refrigerants are studied by definition, type, identification by cylinder colour, "
            "chemical names and formulae, and properties, alongside refrigerant flow controls such "
            "as the thermostatic expansion valve (TEV), automatic expansion valve (AEV), and "
            "capillary tube. "
            "Air conditioning processes cover the psychrometric properties of air, heating and "
            "cooling processes, and the difference between latent and sensible heat. "
            "Compressors, condensers, and evaporators are studied by type, construction, and "
            "working principle, including how to calculate the heat load on condensers and "
            "evaporators and how to service each component."
        ),
    },
    {
        "id": "rac_ss3_installation_troubleshooting_entrepreneurship",
        "subject": "Refrigeration and Air Conditioning",
        "grade": "SS3",
        "topic": "Installation, Troubleshooting, and Entrepreneurship",
        "content": (
            "Workshop practices cover diagnosing faults systematically or by observation, common "
            "faults such as leakage and poor cooling, and testing for leakage, polarity, "
            "insulation continuity, pressure, and efficiency. "
            "Installation processes cover piping a condenser and evaporator, ducting and trunking "
            "for air conditioners, installation of split air conditioners, and the working "
            "principles and installation procedures for a cold room. "
            "Insulation processes cover the importance of insulating refrigeration systems, types "
            "of insulating materials such as glass wool and polystyrene foam, and the procedure "
            "for insulating a system. "
            "WAEC's scheme of examination has three papers: Paper 1 (40 compulsory multiple-choice "
            "questions, 1 hour, 40 marks), Paper 2 (five essay questions, answer four, 1 hour 30 "
            "minutes, 60 marks), and Paper 3, a practical paper with two questions of which "
            "candidates answer one within 2 hours for 100 marks, with a materials list released to "
            "schools at least two weeks in advance."
        ),
    },
 
    # =========== TYPEWRITING ===========
    # Source: https://waecsyllabus.com/typewriting/
    {
        "id": "typewriting_ss1_correspondence_manuscript",
        "subject": "Typewriting",
        "grade": "SS1",
        "topic": "Correspondence and Manuscript Work",
        "content": (
            "Correspondence covers typing on pre-printed A4 and A5 headed paper, letters and "
            "memoranda with insets, continuation sheets, subject headings, and enclosures, "
            "including private, personal, and confidential markings and distribution of carbon "
            "copies. "
            "Candidates are also tested on form letters, circular letters with or without "
            "tear-off portions, and correct envelope addressing, including envelopes with special "
            "marks. "
            "Manuscript work covers typing from manuscript with or without inset matter, requiring "
            "accurate transcription of handwritten or marked-up copy. "
            "Business forms and cards test the completion of pre-printed forms such as application "
            "forms, invoices, order forms, delivery notes, invitation cards, and postcards."
        ),
    },
    {
        "id": "typewriting_ss2_display_work_tabulation",
        "subject": "Typewriting",
        "grade": "SS2",
        "topic": "Display Work and Tabulation",
        "content": (
            "Display work covers headings (main, sub-heading, shoulder, paragraph, and marginal), "
            "paragraphing styles (blocked, indented, hanging), and paragraph numbering systems "
            "(Arabic, Roman, decimal, alphabetical). "
            "Further display work covers producing a menu, advertisement, or itinerary, while "
            "meetings and reports test typing a notice of meeting with or without an agenda, a "
            "chairman's agenda, minutes, and reports. "
            "Tabulation tests candidates' ability to produce ruled tables with or without leader "
            "dots, arranged chronologically or alphabetically. "
            "Literary work covers typing short plays, poems, and articles including footnotes, "
            "and a financial statement task tests typing a simple statement of accounts."
        ),
    },
    {
        "id": "typewriting_ss3_speed_accuracy_exam",
        "subject": "Typewriting",
        "grade": "SS3",
        "topic": "Speed, Accuracy, and Examination Structure",
        "content": (
            "The full examination lasts 2 hours 45 minutes: 5 minutes for warming up on supplied "
            "material, 5 minutes for a speed and accuracy test, 10 minutes for reading through the "
            "paper, and 2 hours 30 minutes for the production tasks. "
            "The speed and accuracy test is set at 40 words per minute with a syllabic intensity "
            "between 1.35 and 1.40, and carries 10 percent of the total marks, with no corrections "
            "permitted on this section. "
            "The production test consists of a maximum of five tasks, and across the whole "
            "examination (tasks plus accuracy test) the total standard words range between 1,350 "
            "and 1,450, with 40 to 50 instructions attracting penalties if not followed. "
            "WAEC recommends institutions provide enough typewriters for at least five 40-minute "
            "periods per week, and an Alternative B paper is available for schools that cannot "
            "accommodate all candidates on the scheduled exam day."
        ),
    },
 
    # =========== WELDING AND FABRICATION ===========
    # Source: https://waecsyllabus.com/welding/
    # NOTE: source PDF filename is "WELDING AND FABRICATION ENGINEERING
    # CRAFT PRACTICE.pdf" - see caveat in module docstring above; verify
    # exact subject name string before use.
    {
        "id": "welding_ss1_safety_metals_tools",
        "subject": "Welding and Fabrication",
        "grade": "SS1",
        "topic": "Workshop Safety, Metal Properties, and Tools",
        "content": (
            "Safety precautions in welding and fabrication workshops cover the types and causes of "
            "accidents (fire, explosion, sharp objects, hazardous gases), accident prevention "
            "measures, environmental pollution and its prevention, and safety facilities and "
            "protective wear. "
            "Properties of metals and their selection covers ferrous and non-ferrous metals (steel, "
            "aluminium, cast iron, copper, zinc), properties such as ductility, hardness, and "
            "malleability, and heat treatment methods including hardening, annealing, and "
            "tempering. "
            "Tools and equipment cover identification of tools for fabrication and welding, "
            "equipment set-up for gas and arc welding, job-holding devices, measuring and marking-out "
            "tools, and the types, gauges, and selection of electrodes for a specific job. "
            "Practical work at this stage includes setting up oxy-acetylene equipment and "
            "demonstrating the use of measuring, marking-out, and cutting tools."
        ),
    },
    {
        "id": "welding_ss2_welding_techniques_fasteners_forging",
        "subject": "Welding and Fabrication",
        "grade": "SS2",
        "topic": "Welding Techniques, Fasteners, and Forging",
        "content": (
            "Operations and techniques in welding cover the types and principles of gas and arc "
            "welding, a typical fabrication process, types of joints and joint methods, "
            "marking-out techniques, and welding techniques and their application, including "
            "leftward and rightward welding methods. "
            "Fasteners are classified and studied through rivets and their application, bolts and "
            "nuts, and screws, with practical work producing riveted joints and bolt-and-nut "
            "assemblies. "
            "Forging covers its definition, the tools and equipment used (furnace, swages, "
            "fullers, flatters, tongs), and forging processes such as upsetting, drawing down, "
            "twisting, bending, and forging an eye. "
            "Preparation of welding surfaces covers cleaning methods (wire brush, emery cloth, "
            "grinding), preparation of edges such as single V and double V joints, post-surface "
            "preparation to prevent corrosion, and common defects in welding surfaces and their "
            "remedies."
        ),
    },
    {
        "id": "welding_ss3_practical_projects_entrepreneurship",
        "subject": "Welding and Fabrication",
        "grade": "SS3",
        "topic": "Practical Projects and Business Entrepreneurship",
        "content": (
            "Practical work/project topics include marking, cutting, and bending shapes such as "
            "triangles, squares, and rectangles; soldering sheet metals; and welding steel using "
            "both arc and gas welding methods, with suggested projects such as a trinket box, "
            "funnel, kitchen stool, and charcoal stove. "
            "Business entrepreneurship opportunity covers the definitions of entrepreneurship, "
            "employer, and employee, and the classification of enterprises as small-, medium-, or "
            "large-scale. "
            "Factors for setting up a workshop include cost, site, weather, materials, manpower, "
            "market, source of power, and transportation, and candidates are expected to make site "
            "visits to existing enterprises. "
            "WAEC's scheme of examination has three papers: Paper 1 (40 multiple-choice questions, "
            "1 hour, 40 marks), Paper 2 (five essay questions, answer four, 1.5 hours, 60 marks), "
            "and Paper 3, a single compulsory practical question over 3 hours 10 minutes for 100 "
            "marks, with a materials list released to schools at least two weeks in advance."
        ),
    },
    {
        "id": "cosmetology_ss1_hair_care_barbering",
        "subject": "Beauty and Cosmetology",
        "grade": "SS1",
        "topic": "Hair Care and Barbering",
        "content": (
            "Barbering covers common hair diseases associated with the trade, the risks and "
            "safety measures involved, and barbering tools, materials, and their maintenance. "
            "Hair shampooing and conditioning covers the reasons for and techniques of shampooing "
            "and conditioning, along with the safety precautions to observe during the process. "
            "The subject covers chemical hair treatments such as relaxing and texturizing, as well "
            "as styling methods including weaving, cutting, trimming, and fixing wigs. "
            "WAEC's scheme of examination has three papers: Paper 1 (40 multiple-choice questions, "
            "40 minutes, 40 marks), Paper 2 (a compulsory question plus three of several further "
            "questions of which candidates answer two, 1 hour 20 minutes, 80 marks total), and "
            "Paper 3, a practical test with three compulsory questions, 1 hour, 80 marks."
        ),
    },
    {
        "id": "cosmetology_ss2_skincare_makeup",
        "subject": "Beauty and Cosmetology",
        "grade": "SS2",
        "topic": "Skin Care and Facial Makeup",
        "content": (
            "Skin care covers identifying skin types, common skin problems and their treatments, "
            "and the types and correct usage of skincare products, including how they can be "
            "abused. "
            "Facial makeup covers the colour wheel/chart for choosing complementary tones, applying "
            "foundation, powder, and eye makeup, and safety precautions to follow when applying "
            "facial makeup. "
            "The subject also covers identifying and treating facial defects, and the types and "
            "correct application technique for lipsticks and lip colour, as well as the shaping of "
            "eyebrows. "
            "Maintenance of makeup implements is examined as its own topic, covering how tools such "
            "as brushes and applicators should be cleaned and cared for between uses."
        ),
    },
    {
        "id": "cosmetology_ss3_nail_foot_care_business",
        "subject": "Beauty and Cosmetology",
        "grade": "SS3",
        "topic": "Nail and Foot Care, and Business Aspects",
        "content": (
            "Foot care covers the effects of footwear on the feet, while hand care covers "
            "massaging, applying oil, trimming nails, and recognizing common nail disorders. "
            "General professional ethics are examined, requiring candidates to correctly outline "
            "expected standards of conduct across the different areas of cosmetology practice. "
            "The subject's equipment list — including dressing chairs, shampoo bowls, curling "
            "tongs, steamers, and cream relaxers — reflects the practical, salon-based nature of "
            "the training. "
            "WAEC groups the subject's content areas into labelled sections (A through G) across "
            "the syllabus, with Paper 2 drawing a compulsory question from Sections A, B, and G, "
            "and further questions from Sections C, D, E, and F."
        ),
    },
 
    # =========== DYEING AND BLEACHING ===========
    # Source: https://studentship.com.ng/waec-dyeing-syllabus/
    {
        "id": "dyeing_ss1_tie_dye_colour_safety",
        "subject": "Dyeing and Bleaching",
        "grade": "SS1",
        "topic": "Tie-Dye, Colour Manipulation, and Safety",
        "content": (
            "The introduction to tie-dye covers its meaning, types of tie-dye designs, and the "
            "materials and tools used to produce them. "
            "Colour manipulation and motif formation covers the definition and classes of colour, "
            "forming motifs for designs, and creating patterns such as repeat, mirror, half-drop, "
            "and block patterns. "
            "Safety and precautions cover the materials to use when dyeing — such as nose and mouth "
            "masks, rubber gloves, and aprons — the proper storage of chemicals, and the safe "
            "handling of electrical appliances. "
            "WAEC's stated aims include testing candidates' practical skill in manipulating dyes and "
            "chemicals on fabric, creative ingenuity in visual representation, and understanding of "
            "safety measures in dyeing and bleaching."
        ),
    },
    {
        "id": "dyeing_ss2_dye_preparation_batik",
        "subject": "Dyeing and Bleaching",
        "grade": "SS2",
        "topic": "Dye Preparation, Dyeing Processes, and Batik",
        "content": (
            "Preparation of dye covers the meaning and types of dyes — such as synthetic and "
            "natural dyes, cold-water reactive dyes, and warm/hot-water dyes — and how to prepare a "
            "dye bath. "
            "Dyeing processes cover plain dyeing, pattern dyeing techniques such as tying and "
            "marbling, and finishing steps including oxidation, washing, starching, and ironing. "
            "Batik is introduced through its meaning, types (freehand, splashing, cracking, "
            "blocking), and the materials and tools used, such as wax, a tjanting tool, and starch. "
            "Two batik methods are studied in detail: the wax resist method (preparing fabric and "
            "wax, waxing techniques, oxidation, and de-waxing) and the starch resist method "
            "(preparing paste, and techniques such as stencilling, freehand drawing, and stamping)."
        ),
    },
    {
        "id": "dyeing_ss3_printing_bleaching_exam",
        "subject": "Dyeing and Bleaching",
        "grade": "SS3",
        "topic": "Fabric Printing, Bleaching, and Examination Structure",
        "content": (
            "Fabric printing covers its meaning, techniques such as relief (lino), intaglio, and "
            "silkscreen printing, and the full production process from motif formation to "
            "finishing. "
            "Tie-dye and printing combines the two, covering techniques such as direct printing, "
            "discharge printing, resist printing, and transfer printing. "
            "Bleaching covers its meaning, the two main types (chlorine bleaching and oxygen "
            "bleaching), the materials used such as caustic soda and hydrosulphite, and how bleach "
            "is applied to fabric. "
            "WAEC's scheme of examination has three papers: Paper 1 (40 multiple-choice questions, "
            "45 minutes, 40 marks), Paper 2 (six essay questions, answer four, 1 hour 40 minutes, 60 "
            "marks), and Paper 3, a 4-hour practical test where candidates choose one of three "
            "alternatives — tie-dye, batik, or printing — rendered on fabric and assessed on the "
            "spot by a visiting WAEC examiner, for 100 marks."
        ),
    },
 
    # =========== ELECTRICAL INSTALLATION AND MAINTENANCE ===========
    # (WAEC's official name is "Electrical Installation and Maintenance
    # Work" - see caveat in module docstring above)
    # Source: https://studentship.com.ng/waec-electrical-installation-syllabus/
    {
        "id": "electinstall_ss1_safety_tools",
        "subject": "Electrical Installation and Maintenance",
        "grade": "SS1",
        "topic": "Workshop Safety and Electrical Tools",
        "content": (
            "Workshop safety rules and regulations cover the hazards and dangers present in an "
            "electrical workshop, precautions for handling electrical tools and materials, "
            "first-aid for electrical accidents, and the statutory regulations governing the trade. "
            "Electrical installation tools, materials, and accessories cover measuring, marking, "
            "and striking tools, the types and preparation of cables, and various electrical "
            "accessories and cells. "
            "WAEC's stated aims include testing candidates' knowledge of safety rules, tools and "
            "materials, the wiring of buildings, the installation and repair of electrical "
            "machines, and rewinding of electrical machines. "
            "The scheme of examination has two composite papers: Paper 1 (40 multiple-choice "
            "questions, 45 minutes, 40 marks) and Paper 2, an essay and practical-work paper in two "
            "sections — Section A (two of three essay questions, 1 hour, 50 marks) and Section B "
            "(two compulsory practical questions, 1 hour 15 minutes, 50 marks)."
        ),
    },
    {
        "id": "electinstall_ss2_wiring_installation",
        "subject": "Electrical Installation and Maintenance",
        "grade": "SS2",
        "topic": "Wiring and Installation Practice",
        "content": (
            "Workshop practice covers working drawings, generation, transmission, and distribution "
            "systems, surface wiring, conduit wiring, and illumination. "
            "Cable work covers soldering, and the joints and termination of cables, followed by "
            "installation topics such as underground cable installation, overhead wire "
            "installation, and inspection and testing of domestic installations. "
            "Machine-related installation covers both D.C. and A.C. machines and their "
            "installation, while rewinding topics cover the tools and equipment for rewinding jobs, "
            "winding drawings, and the rewinding of single-phase electric motors. "
            "Rewinding also covers the armature, commutator, and slip rings of an electric motor, "
            "which candidates must be able to identify and work with during practical rewinding "
            "tasks."
        ),
    },
    {
        "id": "electinstall_ss3_protective_devices_entrepreneurship",
        "subject": "Electrical Installation and Maintenance",
        "grade": "SS3",
        "topic": "Protective Devices, Maintenance, and Entrepreneurship",
        "content": (
            "Protective devices and maintenance covers the installation of protective devices, "
            "maintenance of electrical equipment, and the dismantling and assembling of machines. "
            "This section also covers the repair of electrical machines, equipment, and "
            "installations — bringing together the safety, wiring, and machine-handling skills "
            "taught earlier in the syllabus. "
            "Entrepreneurship in electrical installation is a named syllabus topic in its own "
            "right, reflecting WAEC's stated aim of testing candidates' knowledge of setting up and "
            "managing a small-scale electrical installation and maintenance business. "
            "Key workshop equipment for the subject includes a multimeter, tester, megger "
            "(insulation resistance tester), fishing tape, bending machine, and a single-phase "
            "electric motor for practical rewinding work."
        ),
    },
 
    # =========== FURNITURE MAKING ===========
    # Source: WAEC Furniture Making syllabus, as mirrored by chrisrico.com,
    # ic2engineers.com, and tutor.obiaks.com (consistent detail across
    # mirrors, matching WAEC's standard syllabus document structure)
    {
        "id": "furnituremaking_ss1_tools_materials",
        "subject": "Furniture Making",
        "grade": "SS1",
        "topic": "Woodworking Tools and Materials",
        "content": (
            "Woodworking tools covers hand tools such as try squares, mitre squares, sliding "
            "bevels, marking and mortise gauges, and planes (jack, smooth, trying, block, rebate, "
            "and plough planes), alongside portable power tools and their operations. "
            "Timber preparation covers cutting timber to size, marking, and planing it to final "
            "sizes, as a foundation for later construction work. "
            "Maintenance of furniture tools and equipment is examined as its own topic, requiring "
            "candidates to know how to keep hand tools and machines in good working condition. "
            "WAEC's scheme of examination has three papers: Paper 1 (40 multiple-choice questions, "
            "45 minutes, 40 marks), Paper 2, in two sections — Section A (ten compulsory "
            "short-structured questions, 30 minutes, 20 marks) and Section B (design and drawing "
            "questions, one compulsory) — and Paper 3, a practical test worth 100 marks."
        ),
    },
    {
        "id": "furnituremaking_ss2_design_construction",
        "subject": "Furniture Making",
        "grade": "SS2",
        "topic": "Furniture Design and Construction",
        "content": (
            "Furniture design and construction covers common woodwork joints by type, "
            "classification, and use, and construction methods such as frame and box construction. "
            "Candidates practice free-hand sketching of common household furniture items, applying "
            "design fundamentals and the elements and principles of design. "
            "The design process moves through stages — preliminary sketches, working drawings, and "
            "planning, including a working rod, selection of materials, and a cutting list. "
            "Construction of finished furniture items follows a set procedure: preparation of "
            "materials, setting out of joints, cutting of joints, assembling, and finishing."
        ),
    },
    {
        "id": "furnituremaking_ss3_upholstery_entrepreneurship",
        "subject": "Furniture Making",
        "grade": "SS3",
        "topic": "Upholstery Work and Entrepreneurship in Furniture",
        "content": (
            "Upholstery work within the furniture making syllabus covers traditional and modern "
            "padding materials, the design and construction of upholstery frames, padding and "
            "stuffing techniques, and fixing sewn covering materials. "
            "Entrepreneurship in furniture covers the factors to consider when starting a furniture "
            "business, and the practical management of a furniture workshop, including estimating "
            "and costing furniture items. "
            "Business opportunities in furniture making are examined as a distinct topic, "
            "reflecting the syllabus's emphasis on preparing candidates for self-employment as well "
            "as technical skill. "
            "Recommended texts for the subject include Woodwork for G.C.E and C.S.E by J.N. Green, "
            "Woodwork in Theory and Practice by John A. Walton, and Modern Woodworking by Willis H. "
            "Wagner."
        ),
    },
 
    # =========== PLUMBING AND PIPE FITTING ===========
    # Source: https://studentship.com.ng/waec-plumbing-syllabus/
    {
        "id": "plumbing_ss1_safety_tools_pipes",
        "subject": "Plumbing and Pipe Fitting",
        "grade": "SS1",
        "topic": "Safety, Tools, and Types of Pipe",
        "content": (
            "Safety rules and regulations cover the definition of safety, hazards in the workshop "
            "and on site, the causes and prevention of accidents, and safety signs and symbols. "
            "Hand tools and equipment maintenance covers the classification, types, and uses of "
            "tools, alongside their proper maintenance. "
            "Pipe fitting materials and types of pipe cover the classification of pipes by material "
            "and size, their properties and uses, and the factors that determine the choice of pipe "
            "for a given job. "
            "Pipe jointing covers the definition of jointing, the types of joints used in plumbing "
            "work, the materials used to make them, and applications such as changing direction or "
            "installing fittings."
        ),
    },
    {
        "id": "plumbing_ss2_water_drainage_sanitary",
        "subject": "Plumbing and Pipe Fitting",
        "grade": "SS2",
        "topic": "Water Supply, Drainage, and Sanitary Systems",
        "content": (
            "Sources of water cover rain, surface, and underground water, their characteristics "
            "(tasteless, odourless, colourless), and the classification of water as hard or soft; "
            "water treatment covers methods such as sedimentation, filtration, and chlorination. "
            "The water distribution system covers direct and indirect cold water supply systems, "
            "types of storage tanks, hot water supply systems, and common defects in supply systems. "
            "The drainage system covers the definition and types of drainage, installation "
            "procedures such as trenching and laying, and types of drainage fittings such as bends "
            "and Y-joints. "
            "Sanitary appliances cover the classification of soil and waste appliances and their "
            "installation, while the sewage system covers types of sewage (storm, domestic, "
            "industrial) and sewage collection points such as soakaways, septic tanks, and public "
            "sewers."
        ),
    },
    {
        "id": "plumbing_ss3_business_entrepreneurship",
        "subject": "Plumbing and Pipe Fitting",
        "grade": "SS3",
        "topic": "Business Organization and Contract Work",
        "content": (
            "Business organization covers its definition and types, sources of capital for a "
            "plumbing business, and the distinction between fixed and working capital. "
            "Book-keeping for the trade covers the types of books and records needed for daily "
            "business transactions, such as profit and loss accounts, ledgers, receipts, and "
            "invoices. "
            "Contract works cover the definition and types of contract (fixed price/lump sum and "
            "unit price), the documents involved (bill of quantity, quotation, drawing, "
            "specification), and the parties typically involved, such as the client, contractor, "
            "and consultant. "
            "WAEC's scheme of examination has three papers: Paper 1 (40 multiple-choice questions, "
            "1 hour, 40 marks), Paper 2 (five short-structured essay questions with one compulsory, "
            "answer the compulsory question plus three others, 1 hour, 60 marks), and Paper 3, a "
            "practical test with three questions of which candidates answer two, 1 hour 30 minutes, "
            "100 marks."
        ),
    },
 
    # =========== PRINTING CRAFT PRACTICE ===========
    # Source: https://studentship.com.ng/waec-printing-craft-syllabus/
    {
        "id": "printingcraft_ss1_intro_letter_assembly",
        "subject": "Printing Craft Practice",
        "grade": "SS1",
        "topic": "Introduction to Printing and Letter Assembly",
        "content": (
            "The introduction to the art of printing covers its definition, importance, and "
            "printing processes — letterpress/relief printing, offset/lithography, gravure/intaglio, "
            "and screen/stencil printing — along with the history of printing in Nigeria and "
            "figures such as Johann Gutenberg. "
            "Workshop safety and maintenance covers types of technical printing workshops, safety "
            "precautions around air-conditioning, electrical and lighting hazards, darkrooms, and "
            "machine rooms, and the maintenance of machines, tools, and equipment. "
            "Letter assembly covers hand composition, design for printing, mechanical composition, "
            "and photo-composition, including identifying tools, typefaces, and typography, and "
            "distinguishing monotype from linotype composition. "
            "WAEC's scheme of examination has three papers: Paper 1 (40 multiple-choice questions, "
            "45 minutes, 40 marks), Paper 2 (five essay questions, answer four, 1.5 hours, 60 "
            "marks), and Paper 3, a 1-hour practical test with two questions of which candidates "
            "answer one, for 100 marks."
        ),
    },
    {
        "id": "printingcraft_ss2_print_finishing_screen_printing",
        "subject": "Printing Craft Practice",
        "grade": "SS2",
        "topic": "Print Finishing, Binding, and Screen Printing",
        "content": (
            "Print finishing and binding cover the meaning and types of binding processes — edition "
            "case binding, pamphlet binding, perfect binding, and loose-sheet binding — along with "
            "binding materials such as thread, leather, bone-folders, and a guillotine. "
            "Warehouse topics within print finishing cover identifying types of printing materials "
            "such as paper, board, ink, and chemicals, along with stock and inventory control. "
            "Screen printing covers the origin of the technique, preparing a frame and stencil "
            "(wooden frame, mesh, hand-made or block-out stencils), and stretching mesh onto a "
            "frame. "
            "Photographic screen making covers coating the screen with a sensitized solution, "
            "exposing it to light, and developing it with water, followed by image reproduction — "
            "transferring the image from the mesh or stencil onto a substrate such as paper, "
            "sticker, or plastic."
        ),
    },
    {
        "id": "printingcraft_ss3_lithography_machine_printing",
        "subject": "Printing Craft Practice",
        "grade": "SS3",
        "topic": "Lithography, Machine Printing, and Legal Aspects",
        "content": (
            "Lithography process camera work covers work-ticket and layout planning, film making "
            "and process camera plate making (including types of film such as panchromatic and "
            "orthochromatic film, and chemicals such as developer and fixative), and the darkroom "
            "safety rules that govern this work. "
            "Machine printing covers offset machine printing (techniques, spare parts and "
            "maintenance, and the major units of a lithographic printing machine), as well as "
            "relief printing, gravure (intaglio) printing, and flexographic printing, including "
            "flexography's importance to the packaging industry. "
            "Legal aspects of the printing industry cover the trade houses and professional bodies "
            "active in the sector, and copyright law as it applies to printed material. "
            "Facilities required for the subject include a vacuum frame, screen mesh stretcher, "
            "guillotine, light table, register scope, and a small offset machine, reflecting the "
            "practical, equipment-heavy nature of the trade."
        ),
    },
    {
        "id": "photography_ss1_intro_history_light",
        "subject": "Photo Technology",
        "grade": "SS1",
        "topic": "Introduction, History, and Light in Photography",
        "content": (
            "Photography is examined for its meaning, its functions such as recording events and "
            "visual communication, and its many branches — fashion, photojournalism, forensic, "
            "sports, architectural, and portraiture photography among others. "
            "The history of photography covers the origin of the camera, the development of "
            "photography in Nigeria, and pioneers of the medium, both international figures such "
            "as Louis Daguerre and Nigerian figures such as J.D. Okhai Ojeikere and Peter Obe. "
            "Light in photography covers natural and artificial light sources and the properties "
            "of light — absorption, reflection, transmission, refraction, and dispersion — that "
            "govern how a photograph is exposed. "
            "Terminologies such as exposure, aperture, shutter speed, and perspective are examined "
            "as their own topic, giving candidates the vocabulary needed for the rest of the "
            "syllabus."
        ),
    },
    {
        "id": "photography_ss2_camera_film_darkroom",
        "subject": "Photo Technology",
        "grade": "SS2",
        "topic": "The Camera, Film, and the Darkroom",
        "content": (
            "The camera topic covers the basic principles underlying its design (a light-tight "
            "body, a light inlet, a viewing system, and image formation), the parts of an SLR "
            "camera, and camera types such as compact, rangefinder, SLR, and large format. "
            "Lenses are covered through the principles of refraction and reflection, the "
            "difference between concave and convex lenses, focal length, and lens types such as "
            "wide-angle, telephoto, and zoom. "
            "Film is studied through its light-sensitive chemical composition, types (black and "
            "white versus colour) and formats, and film speed (ISO), which determines whether a "
            "film is slow, medium, or fast. "
            "The darkroom and film development process covers the required layout and equipment "
            "(developing tanks, safe light, enlarger), the chemicals used (developer, fixer, stop "
            "bath), the step-by-step development process, and safety measures such as wearing "
            "rubber gloves and proper chemical storage."
        ),
    },
    {
        "id": "photography_ss3_digital_exhibition_exam",
        "subject": "Photo Technology",
        "grade": "SS3",
        "topic": "Printing, Digital Photography, and Examination Structure",
        "content": (
            "Printing photographs covers the equipment involved (enlarger, printing paper, "
            "printing frame), the printing process from exposure through developing and fixing, "
            "and methods of drying and storing negatives, photographs, and chemicals. "
            "Digital photography covers the differences between analogue and digital methods, the "
            "equipment involved (digital camera, computer, printer), common editing software such "
            "as Adobe Photoshop, and input/output devices such as scanners and printers. "
            "Exhibition of photographs covers the procedure for mounting and framing images, "
            "acquiring exhibition space, publicity, and display. "
            "WAEC's scheme of examination has three papers: Paper 1 (40 multiple-choice questions, "
            "1 hour, 40 marks), Paper 2 (six essay questions, answer four, 2 hours, 60 marks), and "
            "Paper 3, an alternative-to-practical paper called Photo Analysis and Processes, with "
            "a compulsory Section A analysing two black-and-white photographs (50 marks) and a "
            "Section B of three compulsory questions on photographic processes and equipment (50 "
            "marks), for 2 hours and 100 marks total."
        ),
    },
    {
        "id": "sculpture_ss1_vocation_tools_materials",
        "subject": "Sculpture",
        "grade": "SS1",
        "topic": "Sculpture as a Vocation, Tools, and Materials",
        "content": (
            "Sculpture as a vocation covers its definition, the history and rationale for "
            "studying it, career opportunities, and the main methods of producing sculpture: "
            "carving, modelling, casting, and construction/assemblage. "
            "Tools and equipment are studied by method — carving tools such as gouges, mallets, "
            "and chisels; modelling tools such as spatulas and callipers; casting tools and "
            "equipment such as crucibles and safety gear; and construction tools such as hacksaws "
            "and welding equipment — along with their identification, use, and maintenance. "
            "Materials for carving (wood, stone, ivory), modelling (clay), and casting (plaster of "
            "Paris, cement, wax) are studied by source and by how they should be stored to prevent "
            "damage. "
            "Safety measures are specific to each method — for example, wearing protective "
            "clothing and carving away from the body for carving, or avoiding naked flame near "
            "welding equipment for construction and assemblage."
        ),
    },
    {
        "id": "sculpture_ss2_production_lettering_finishing",
        "subject": "Sculpture",
        "grade": "SS2",
        "topic": "Preliminary Design, Production Methods, Lettering, and Finishing",
        "content": (
            "Preliminary design covers its meaning and importance — guiding the end product and "
            "preventing wasted material and time — through sketching, drawing, and idea "
            "development, whether done manually or with computer-aided design. "
            "Methods of production cover direct and indirect processes for each technique: carving "
            "(relief and in-the-round, engraving, chiselling), modelling (pinching, coiling, "
            "slabbing), casting (lost-wax casting, sand casting), and construction/assemblage "
            "(welding, riveting, filigree). "
            "Lettering covers types such as block, Gothic, and Roman lettering, methods of "
            "execution such as carving, embossing, and etching, and applications such as plaques, "
            "tombstones, and medals. "
            "Decoration and finishing cover techniques such as engraving, scorching, painting, and "
            "sandblasting, and the importance of finishing for durability, aesthetics, and "
            "socio-economic value such as tourism promotion and export earnings."
        ),
    },
    {
        "id": "sculpture_ss3_industry_appreciation_exam",
        "subject": "Sculpture",
        "grade": "SS3",
        "topic": "Establishing a Sculpture Enterprise and Examination Structure",
        "content": (
            "Establishing a small-scale sculpture industry covers factors such as raw materials, "
            "labour, and market location, alongside quality-control ethics such as avoiding "
            "indecent themes and maintaining a clean studio. "
            "Packaging and handling cover the types of packaging (primary, secondary, tertiary), "
            "the tools and materials used, and the importance of preventing damage during "
            "transport, while costing, pricing, and marketing cover exhibition planning and basic "
            "advertising strategies. "
            "Appreciation and criticism in sculpture cover the terms used to evaluate "
            "three-dimensional works — content, form, subject matter, symbolism, and style — "
            "alongside portfolio compilation and professional practices such as writing a business "
            "plan and an artist's statement. "
            "WAEC's scheme of examination has three papers: Paper 1 (40 multiple-choice questions, "
            "50 minutes, 40 marks), Paper 2 (six essay questions, answer four, 2 hours, 60 marks), "
            "and Paper 3, two practical projects of which candidates execute one over five days "
            "(six hours per day) for 80 marks, plus 20 marks for preliminary sketches and notes "
            "prepared in the two weeks before the project, for a total of 100 marks."
        ),
    },
 
    # =========== LEATHER GOODS MANUFACTURING ===========
    # Source: https://infoguidenigeria.com/waec-syllabus-for-leather-goods-manufacturing/
    {
        "id": "leathergoods_ss1_intro_footwear",
        "subject": "Leather Goods Manufacturing",
        "grade": "SS1",
        "topic": "Introduction to Leather Craft and Footwear Manufacturing",
        "content": (
            "The introduction to leather craft covers its meaning and importance, how leather is "
            "prepared, and the different types of leather goods or products that can be made from "
            "it. "
            "Footwear manufacturing covers the components of footwear, the differences between "
            "men's and ladies' shoe construction, and the process from pattern cutting through "
            "clicking, skiving, and folding. "
            "Materials, tools, and equipment cover leather, fabric, rubber, and adhesives; tools "
            "such as knives, shears, mallets, and awls; and equipment such as sewing machines, sole "
            "trimmers, and splitters, alongside their description, use, and care. "
            "Safety measures in leather goods production are examined as their own topic, "
            "reflecting the workshop-heavy, tool-intensive nature of the trade."
        ),
    },
]