Below are failed conversations of a product-advice assistant for a small
online electronics shop. For each one a person wrote a critique saying what
went wrong. Group them into failure modes.

Rules:

- Name a failure mode after what went wrong, not after the question.
- Use as few modes as describe the critiques well. A conversation can have
  more than one mode.
- Every conversation listed must be mapped to at least one mode.
- Use only the case ids listed below.

Answer with one JSON object and nothing else:

{
  "modes": [{"id": "short-kebab-id", "name": "Short name", "description": "One sentence."}],
  "mapping": {"<case id>": ["<mode id>", "..."]}
}

The failed conversations:

[[failures]]
