# Advanced Skill Writing Principles

These principles go beyond basic formatting. They're the difference between a skill that works in the happy path and one that's robust across diverse real-world inputs.

Read this reference when you need to deeply optimize a skill's description, reduce context bloat, avoid common design mistakes, or structure instructions for maximum attention.

## Description Writing

The description is the skill's trigger mechanism. A skill that doesn't fire when it should is worse than useless — it's invisible. Write descriptions that are deliberately "pushy" about when to trigger:

**Bad descriptions** (undertriggering):
- "Create charts from data" — too vague, misses users who say "visualize", "plot", "graph"
- "Convert PDF to text" — misses users who say "extract", "read", "parse this document"
- "Help with Excel files" — misses users who say "spreadsheet", "xlsx", "workbook"

**Good descriptions** (appropriately pushy):
- "Create charts, graphs, and data visualizations from spreadsheets and data files. Use this skill whenever the user wants to visualize data, plot a chart, create a graph, or display data visually — even if they don't use the word 'chart.'"
- "Extract, read, and convert PDF documents. Use this whenever the user mentions PDFs, needs to read a document, extract text from a file, or work with any PDF content."
- "Process and analyze Excel spreadsheets (.xlsx, .xls, .csv). Use this skill whenever the user works with spreadsheet data, mentions Excel, needs to process tabular data, or asks about cells, columns, or formulas in a spreadsheet."

Key tips for descriptions:
- Include synonyms, alternative terms, and common misspellings
- Explicitly state "Use this skill when..." with concrete scenarios
- Cover the *intent* behind the user's request, not just the literal words
- Mention file types, formats, and domain-specific terminology users might use
- Don't forget to also say what the skill *doesn't* cover — this prevents false positives

## Context Efficiency

Every token in SKILL.md competes for the model's attention. Be ruthless about earning your lines:

1. **Earn each line.** Before writing a line, ask: "If I cut this, would the model still do the right thing?" If yes, cut it.
2. **Avoid redundancy.** Don't repeat the same instruction in different sections. State it once, clearly, in the most relevant place.
3. **Use structured formats.** A numbered list is more followable than a paragraph. A table is more scannable than prose. Decision trees ("If X, do Y; if Z, do W") are more reliable than conditional prose.
4. **Cut ceremonial language.** "Please make sure to..." "It's important to note that..." "Don't forget to..." — these filler phrases don't change behavior. The model doesn't need encouragement. Just state the instruction.
5. **Examples over explanations.** A concrete example of the desired output is worth more than a paragraph describing it.
6. **Explain the "why," not just the "what."** "Sort the results by date" is OK. "Sort the results by date so the user sees the most recent items first" is better — it tells the model the goal, so it can adapt if the specific instruction doesn't apply.

## Common Anti-Patterns

These are mistakes that make skills worse:

- **The Kitchen Sink:** Including every possible instruction, edge case, and example "just in case." This bloats context and drowns the important instructions in noise. Use progressive disclosure instead.

- **The MUST/NEVER Wall:** Writing dozens of ALWAYS/NEVER/MUST instructions. These create a rigid framework where the model optimizes for satisfying constraints rather than producing good output. Replace with explanations of why something matters, and the model will make better judgment calls.

- **The Monolith:** A single 800-line SKILL.md that covers everything. The model will only follow the first and last ~200 lines reliably. Break it into SKILL.md (core) + reference files (details).

- **The Generic Description:** "Helps with various tasks" or "AI assistant for productivity." These descriptions never trigger because they match everything and nothing simultaneously. Be specific.

- **The Unconditional Load:** Loading all reference files regardless of the task. If a skill supports Python and JavaScript but the user is only working with Python, the JavaScript reference just wastes context. Use conditional loading.

- **The Prose Instruction Where Code Should Be:** Telling the model "Step 1: Install pandas. Step 2: Read the CSV. Step 3: Filter rows where..." when a 10-line Python script would be faster, more reliable, and cost zero context tokens when not needed. Scripts are the ultimate progressive disclosure — they only occupy context when explicitly called.

- **The Forward Declaration:** "See the troubleshooting section below" when "below" is 400 lines away. The model may never get there. Either inline the critical info or use a concrete file reference with a conditional trigger.

- **The Tautological Instruction:** "Always follow best practices" or "Write clean, maintainable code." These are vague and cannot be followed programmatically. Replace with specific, actionable rules: "Use `Annotated` for all parameter declarations" instead of "Use best practices for parameters."

- **Nested Conditionals:** "If using Python 3.10+, use X syntax, unless also using Pydantic v1, in which case use Y, but only if the field is optional, otherwise Z." The model follows simple, flat instructions far more reliably than deeply nested conditionals. Flatten these into separate sections or move the branching logic into a reference file.

- **The Kitchen Skill:** One skill that tries to cover everything — "Full-Stack Python" covering FastAPI, SQLAlchemy, Pydantic, and pytest. This bloats the body and makes trigger conditions vague. Better to split into separate skills with precise triggers.

## Instruction Hierarchy

Not all instructions are equally important. Signal priority through structure:

1. **Critical instructions** (things that must be done or the task fails): Put these first, make them prominent, explain why they matter.
2. **Default behaviors** (what to do when the user doesn't specify): State these clearly but they don't need emphasis.
3. **Optional enhancements** (nice-to-have if time/conditions allow): Put these last or in references.

This matches how the model processes context — it attends most to the beginning. Front-load what matters most.