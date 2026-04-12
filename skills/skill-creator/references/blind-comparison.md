# Blind Comparison

Read this reference when you want a more rigorous comparison between two versions of a skill (e.g., the user asks "is the new version actually better?").

The basic idea: give two outputs to an independent agent without telling it which is which, and let it judge quality. Then analyze why the winner won.

For detailed instructions, read `agents/comparator.md` and `agents/analyzer.md`.

This is optional, requires subagents, and most users won't need it. The human review loop in the main workflow is usually sufficient.