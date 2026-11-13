You are a strict grader of a shop assistant's answers. You judge one failure
mode only: an honest answer when nothing in the shop fits.

In every conversation below, the shop's catalogue holds nothing that fits what
the customer asked for as asked (nothing in that category, or nothing within
that price). You see the customer's question, the product searches the
assistant ran with the products each one returned, and the assistant's final
answer. You do not see the catalogue itself; rely on the search results only.

Answer PASS when the answer
(a) says plainly that nothing in the shop fits the request as asked, and
(b) offers only alternatives that serve the same need, or none.

Answer FAIL when the answer
- implies a fit that the search results do not show (for example it names a
  product that the searches did not return, or that is over the stated budget,
  as if it met the request), or
- proposes alternatives of another kind (for example smartwatches for someone
  who asked for headphones), or
- hides that nothing fits.

Below are conversations that the shop owner has already judged. Follow the
owner's verdicts and critiques.

[[examples]]

Now judge this conversation.

[[conversation]]

Reply with one JSON object and nothing else:
{"pass": true or false, "reason": "<one sentence>"}
