"""
Nigerian secondary school curriculum corpus.

40 short passages across the WAEC core subjects: Math, Physics, Chemistry,
Biology, and English. Covers JSS3 through SS3.

Format kept tight — short, fact-dense passages. Better retrieval comes from
many narrow chunks than few wide ones.
"""

CURRICULUM = [
    # =========== BIOLOGY ===========
    {
        "id": "bio_jss3_digestion",
        "subject": "Biology",
        "grade": "JSS3",
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

    # =========== MATHEMATICS ===========
    {
        "id": "math_jss3_algebra_basics",
        "subject": "Mathematics",
        "grade": "JSS3",
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

    # =========== ENGLISH ===========
    {
        "id": "eng_jss3_parts_of_speech",
        "subject": "English",
        "grade": "JSS3",
        "topic": "Parts of Speech",
        "content": (
            "The eight parts of speech are: noun (person, place, thing), pronoun (he, she, it), "
            "verb (action or state), adjective (describes a noun), adverb (describes a verb or adjective), "
            "preposition (in, on, under), conjunction (and, but, because), and interjection (wow, oh)."
        ),
    },
    {
        "id": "eng_ss1_tenses",
        "subject": "English",
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
        "subject": "English",
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
        "subject": "English",
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
        "subject": "English",
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
        "subject": "English",
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
        "subject": "English",
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
]