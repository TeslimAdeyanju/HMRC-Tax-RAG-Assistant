from __future__ import annotations


TAX_INSTRUCTIONS = """
Your task is to answer tax questions using only the provided tax manual excerpts.

Use the context to find relevant information and provide accurate answers.
If the answer is not found in the context, respond with "I don't know."
""".strip()


TAX_PROMPT_TEMPLATE = """
QUESTION: {question}

CONTEXT:
{context}
""".strip()


class TaxKnowledgeAgent:
    def __init__(
        self,
        index,
        llm_client,
        instructions=TAX_INSTRUCTIONS,
        prompt_template=TAX_PROMPT_TEMPLATE,
        manual="company-taxation-manual",
        model="gpt-5.4-mini",
    ):
        self.index = index
        self.llm_client = llm_client
        self.instructions = instructions
        self.prompt_template = prompt_template
        self.manual = manual
        self.model = model

    def search(self, query, num_results=5):
        """Search the index for the most relevant tax manual excerpts."""
        boost_dict = {"title": 1.5, "text": 2.5}
        filter_dict = {"manual": self.manual}

        return self.index.search(
            query,
            num_results=num_results,
            boost_dict=boost_dict,
            filter_dict=filter_dict,
        )

    def build_context(self, search_results):
        """Format the retrieved tax docs into a readable context block."""
        lines = []

        for doc in search_results:
            title = doc.get("title", "Untitled section")
            text = doc.get("text", "")
            url = doc.get("url", "")

            lines.append(f"Title: {title}")
            if url:
                lines.append(f"URL: {url}")
            lines.append(f"Text: {text}")
            lines.append("")

        return "\n".join(lines).strip()

    def build_prompt(self, query, search_results):
        """Combine the question and relevant excerpts into a final prompt."""
        context = self.build_context(search_results)
        return self.prompt_template.format(question=query, context=context)

    def llm(self, prompt):
        """Send the user prompt to the model with developer instructions."""
        messages = [
            {"role": "developer", "content": self.instructions},
            {"role": "user", "content": prompt},
        ]

        response = self.llm_client.responses.create(
            model=self.model,
            input=messages,
        )

        return response.output_text

    def rag(self, query, num_results=5):
        """Run the full RAG pipeline: search -> build prompt -> answer."""
        search_results = self.search(query, num_results=num_results)
        prompt = self.build_prompt(query, search_results)
        return self.llm(prompt)


if __name__ == "__main__":
    # Example usage:
    # from openai import OpenAI
    # from your_index import index
    #
    # client = OpenAI()
    # agent = TaxKnowledgeAgent(index=index, llm_client=client)
    # answer = agent.rag("What counts as capital expenditure for capital allowances purposes?")
    # print(answer)

    print("TaxKnowledgeAgent is ready.")
