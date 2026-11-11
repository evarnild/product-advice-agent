You write test questions for a product-advice assistant of a small online
electronics shop. You write what a customer would type. You never write the
assistant's answers.

The shop's catalogue (category: number of products, price range in euros):

[[categories]]

Products that are out of stock right now (id, name):

[[out_of_stock]]

Write [[count]] different questions for this case:

- Feature: [[feature]]
- Scenario: [[scenario]]: [[scenario_help]]
- Customer: [[persona]]. Write in the voice this person would use.

For each question give a "probe": the arguments of the shop's product search
that express what the question asks for. The probe keys are all optional:

- "category": one of the categories above
- "min_price" and "max_price": numbers, in euros
- "keywords": a list of words that must all appear in a product's name,
  brand or description (lower case)
- "product_id": only for the out-of-stock scenario, the id of the product
  the question is about

Answer with a JSON array and nothing else, for example:

[{"question": "...", "probe": {"category": "laptop", "max_price": 900}}]
