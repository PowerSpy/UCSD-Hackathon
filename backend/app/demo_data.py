"""Demo data for demonstration purposes when API credits are low."""

DEMO_LESSONS = {
    "photosynthesis": {
        "title": "Photosynthesis: How Plants Make Their Food",
        "outline": ["What is Photosynthesis?", "The Light-Dependent Reactions", "The Light-Independent Reactions", "Practice: Putting It Together"],
        "sections": [
            {
                "type": "intro",
                "title": "What is Photosynthesis?",
                "subsection_name": "Overview & Definition",
                "body": "**Photosynthesis** is the process by which plants, algae, and some bacteria convert light energy into chemical energy stored in glucose. Think of it as plants' way of making their own food!\n\nThe basic equation is:\n```\n6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂\n```\n\nThis means:\n- **Input**: Carbon dioxide (from air), water (from soil), and light energy (from sun)\n- **Output**: Glucose (sugar for energy) and oxygen (what we breathe!)\n\n**Two main stages:**\n1. Light-dependent reactions (in the thylakoids)\n2. Light-independent reactions/Calvin Cycle (in the stroma)",
                "practice_prompt": "In your own words, explain what photosynthesis does and why it's important for both plants and animals.",
            },
            {
                "type": "example",
                "title": "The Light-Dependent Reactions",
                "subsection_name": "How Plants Capture Light Energy",
                "body": "This stage happens **inside the thylakoid membranes** of the chloroplast and requires light.\n\n**What happens:**\n1. **Chlorophyll absorbs photons** - The pigment in chlorophyll captures light energy\n2. **Water is split** - H₂O molecules are broken down into hydrogen and oxygen\n3. **Electrons get excited** - The energy from light excites electrons to higher energy levels\n4. **ATP and NADPH are made** - Energy carriers that store the light energy in chemical form\n5. **Oxygen is released** - The oxygen byproduct exits as a gas (that's the O₂ we breathe!)\n\n**Key point:** This stage **requires light** — that's why it's called \"light-dependent.\"\n\n**Think of it like:** Charging a battery with solar panels. The light charges up molecules (ATP and NADPH) so they can be used later.",
                "practice_prompt": "Why do you think plants need to split water molecules? What happens to the pieces that get separated?",
            },
            {
                "type": "example",
                "title": "The Light-Independent Reactions (Calvin Cycle)",
                "subsection_name": "Making Sugar from CO₂",
                "body": "This stage happens **in the stroma** of the chloroplast and does **NOT require light directly** (though it depends on products from the light reactions).\n\n**What happens:**\n1. **Carbon fixation** - CO₂ is combined with a 5-carbon sugar (RuBP)\n2. **Reduction phase** - The ATP and NADPH from light reactions provide energy to build glucose\n3. **Regeneration** - RuBP is reformed so the cycle can repeat\n\n**The 3 main steps (3-PG cycle):**\n- CO₂ enters → Carbon gets added to organic molecules\n- ATP & NADPH energy is used → Glucose is built\n- The cycle resets → Ready for more CO₂\n\n**Think of it like:** Using the charged battery (ATP/NADPH) to power a factory that builds sugar from raw materials (CO₂).\n\n**Key equation for this stage:**\n```\n3CO₂ + 9ATP + 6NADPH → Glucose + 9ADP + 8Pi + 6NADP⁺\n```",
                "practice_prompt": "If the light reactions stopped, what do you think would happen to the Calvin Cycle? Why?",
            },
            {
                "type": "practice",
                "title": "Practice: Putting It Together",
                "subsection_name": "Connecting Both Stages",
                "body": "Now let's connect everything!\n\n**The flow:**\n```\nLight Energy\n    ↓\nLight-Dependent Reactions (in thylakoid)\n• Water → Oxygen + Energy carriers (ATP, NADPH)\n    ↓\nEnergy carriers used in:\nCalvin Cycle (in stroma)\n• CO₂ + Energy → Glucose (C₆H₁₂O₆)\n```\n\n**Why this matters:**\n- Plants make their own food (glucose) using just sunlight, water, and CO₂\n- Oxygen is released as a byproduct (lucky for us!)\n- This glucose feeds the plant and becomes energy for growth\n- Animals eat plants and get energy from that glucose\n\n**Real-world connection:**\n A single corn plant can produce 1000+ grams of glucose per season through photosynthesis. That's why plants grow so much during sunny seasons!",
                "practice_prompt": "Draw or describe the complete flow from sunlight entering a leaf to glucose being made. Label each main stage.",
            },
        ],
    },
    "fractions": {
        "title": "Understanding Fractions",
        "outline": ["What are Fractions?", "Equivalent Fractions", "Comparing Fractions", "Adding Fractions"],
        "sections": [
            {
                "type": "intro",
                "title": "What are Fractions?",
                "subsection_name": "Parts of a Whole",
                "body": "A **fraction** represents a part of a whole. It shows how many equal parts you have out of a total number of parts.\n\n**Parts of a fraction:**\n```\n   3  ← Numerator (top) = how many parts you have\n  ---\n   4  ← Denominator (bottom) = total number of equal parts\n```\n\nIn the example 3/4:\n- The whole is divided into 4 equal parts\n- You have 3 of those parts\n- You're missing 1 part\n\n**Visual example:**\nImagine a pizza cut into 4 equal slices. If you eat 3 slices, you've eaten 3/4 of the pizza!\n\n**Other fraction types:**\n- **Proper fraction**: numerator < denominator (like 2/5) — less than 1 whole\n- **Improper fraction**: numerator ≥ denominator (like 5/4) — 1 whole or more\n- **Mixed number**: whole number + fraction (like 1 1/4)",
                "practice_prompt": "If a chocolate bar has 8 squares and you eat 5, what fraction of the chocolate bar did you eat?",
            },
            {
                "type": "example",
                "title": "Equivalent Fractions",
                "subsection_name": "Different Fractions, Same Value",
                "body": "**Equivalent fractions** are different fractions that represent the same amount.\n\n**Example:**\n- 1/2 = 2/4 = 3/6 = 4/8\n\nThey all represent exactly half!\n\n**How to find equivalent fractions:**\nMultiply or divide both the numerator AND denominator by the same number.\n\n**Multiplying to make bigger fractions:**\n```\n1/2 × 2/2 = 2/4\n1/2 × 3/3 = 3/6\n1/2 × 4/4 = 4/8\n```\n\n**Dividing to simplify (make smaller fractions):**\n```\n4/8 ÷ 2/2 = 2/4\n4/8 ÷ 4/4 = 1/2\n```\n\n**The rule:** As long as you multiply or divide the top and bottom by the SAME number, the fraction stays equal in value!\n\n**Why this matters:** Sometimes we want to write fractions in simplest form (where numerator and denominator can't be divided by the same number anymore).",
                "practice_prompt": "Starting with 2/3, create two equivalent fractions by multiplying by different numbers.",
            },
            {
                "type": "example",
                "title": "Comparing Fractions",
                "subsection_name": "Which Fraction is Bigger?",
                "body": "Sometimes you need to know which fraction is larger or smaller.\n\n**When denominators are the same:**\nJust compare numerators!\n- 3/5 > 2/5 (because 3 > 2)\n- 1/8 < 6/8 (because 1 < 6)\n\n**When denominators are different:**\nYou need to find a common denominator first.\n\n**Example: Compare 1/3 and 2/5**\n- Find common denominator: 3 × 5 = 15\n- 1/3 = 5/15\n- 2/5 = 6/15\n- Compare: 5/15 < 6/15, so **1/3 < 2/5**\n\n**Quick trick using cross-multiply:**\n```\n1/3 ? 2/5\n1×5 ? 3×2\n5 ? 6\n5 < 6, so 1/3 < 2/5\n```\n\n**Visual way:** Draw pictures or use number lines to see which is bigger.",
                "practice_prompt": "Compare 3/4 and 5/8. Which is larger? Explain your thinking.",
            },
            {
                "type": "practice",
                "title": "Adding Fractions",
                "subsection_name": "Combining Parts Together",
                "body": "**When denominators are the same:**\nAdd the numerators, keep the denominator!\n\n```\n1/4 + 2/4 = 3/4\n```\n\n**When denominators are different:**\nFind a common denominator first, then add!\n\n**Example: 1/3 + 1/4**\n- Common denominator: 12 (3 × 4)\n- 1/3 = 4/12\n- 1/4 = 3/12\n- Add: 4/12 + 3/12 = 7/12\n\n**Steps:**\n1. Find a common denominator (multiply the denominators, or find the least common multiple)\n2. Convert both fractions to use the common denominator\n3. Add the numerators\n4. Keep the common denominator\n5. Simplify if possible\n\n**Example with simplifying: 2/4 + 3/8**\n- Common denominator: 8\n- 2/4 = 4/8\n- 4/8 + 3/8 = 7/8\n- 7/8 is already simplified ✓",
                "practice_prompt": "Calculate 2/5 + 1/3. Show all your steps, including finding the common denominator.",
            },
        ],
    },
}

DEMO_QUIZZES = {
    "photosynthesis": {
        "questions": [
            {
                "id": "q1",
                "type": "multiple_choice",
                "prompt": "What are the two main products of photosynthesis?",
                "choices": [
                    "Oxygen and water",
                    "Glucose and oxygen",
                    "Carbon dioxide and water",
                    "Chlorophyll and glucose",
                ],
                "correct": "Glucose and oxygen",
            },
            {
                "id": "q2",
                "type": "short_answer",
                "prompt": "Where in the chloroplast do the light-dependent reactions occur?",
                "choices": None,
                "correct": "thylakoid",
            },
            {
                "id": "q3",
                "type": "multiple_choice",
                "prompt": "Why are light-independent reactions also called the 'dark reactions'?",
                "choices": [
                    "Because they only happen at night",
                    "Because they don't require direct light energy, though they depend on products from light reactions",
                    "Because they happen in the dark parts of the leaf",
                    "Because chlorophyll doesn't work in these reactions",
                ],
                "correct": "Because they don't require direct light energy, though they depend on products from light reactions",
            },
            {
                "id": "q4",
                "type": "fill_blank",
                "prompt": "The equation for photosynthesis shows that 6CO₂ + 6H₂O + light energy produces glucose (C₆H₁₂O₆) and ______.",
                "choices": None,
                "correct": "oxygen",
            },
            {
                "id": "q5",
                "type": "short_answer",
                "prompt": "What role does ATP play in photosynthesis?",
                "choices": None,
                "correct": "energy carrier",
            },
        ],
        "explanations": {
            "q1": "The answer is 'Glucose and oxygen' because glucose (C₆H₁₂O₆) is the sugar that plants use as food, and oxygen (O₂) is released as a byproduct — which is what we breathe!",
            "q2": "The answer is 'thylakoid' because the light-dependent reactions occur in the thylakoid membranes within the chloroplast, where chlorophyll captures light energy.",
            "q3": "The answer is 'Because they don't require direct light energy, though they depend on products from light reactions' because the Calvin Cycle (light-independent reactions) happens in the stroma and uses ATP and NADPH made by the light reactions.",
            "q4": "The answer is 'oxygen' because the complete photosynthesis equation is: 6CO₂ + 6H₂O + light → C₆H₁₂O₆ + 6O₂. The oxygen comes from the water that's split in the light reactions.",
            "q5": "The answer involves 'energy carrier' because ATP is a molecule that carries and transfers energy from the light reactions to the Calvin Cycle, powering the synthesis of glucose from CO₂.",
        },
    },
    "fractions": {
        "questions": [
            {
                "id": "q1",
                "type": "multiple_choice",
                "prompt": "What fraction represents 3 out of 8 equal parts?",
                "choices": [
                    "8/3",
                    "3/8",
                    "3/11",
                    "8/11",
                ],
                "correct": "3/8",
            },
            {
                "id": "q2",
                "type": "short_answer",
                "prompt": "What is an equivalent fraction to 1/2?",
                "choices": None,
                "correct": "2/4",
            },
            {
                "id": "q3",
                "type": "multiple_choice",
                "prompt": "Which fraction is larger: 2/5 or 3/7?",
                "choices": [
                    "2/5",
                    "3/7",
                    "They are equal",
                    "Cannot be determined",
                ],
                "correct": "3/7",
            },
            {
                "id": "q4",
                "type": "fill_blank",
                "prompt": "To add fractions with different denominators, you must first find a ______ denominator.",
                "choices": None,
                "correct": "common",
            },
            {
                "id": "q5",
                "type": "short_answer",
                "prompt": "What is 1/4 + 2/4 in simplest form?",
                "choices": None,
                "correct": "3/4",
            },
        ],
        "explanations": {
            "q1": "The answer is '3/8' because the numerator (top) shows how many parts you have (3) and the denominator (bottom) shows the total parts (8).",
            "q2": "The answer is '2/4' (or '4/8', '3/6', etc.) because equivalent fractions represent the same amount. You get 2/4 by multiplying both top and bottom of 1/2 by 2.",
            "q3": "The answer is '3/7' because when you find a common denominator (35), 2/5 = 14/35 and 3/7 = 15/35. Since 15 > 14, then 3/7 is larger.",
            "q4": "The answer is 'common' because when denominators are different, you need to find a common denominator before you can add the numerators together.",
            "q5": "The answer is '3/4' because when denominators are the same, you simply add the numerators: 1 + 2 = 3, so 1/4 + 2/4 = 3/4.",
        },
    },
}
