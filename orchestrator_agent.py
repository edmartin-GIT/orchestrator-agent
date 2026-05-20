import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

MAX_CONTEXT_CHARS = 3000  # Limit passed context to avoid 413 errors


def truncate(text: str, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[Truncated for context length]"


def run_agent(system_prompt: str, user_message: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


def problem_agent(user_input: str) -> str:
    system = (
        "You are the Problem Agent. You must ALWAYS use web search.\n\n"
        "Process:\n"
        "1. Search the web using the user's question.\n"
        "2. Use ONLY search results + the user's text to define the problem clearly.\n\n"
        "Rules:\n"
        "* Do not guess or assume anything outside search evidence or user text.\n"
        "* Do not produce solutions, options, risks, or recommendations.\n"
        "* If search does not provide relevant context, state the limitation.\n\n"
        "Output: A clear factual definition of the problem."
    )
    return run_agent(system, user_input)


def options_agent(user_input: str, problem: str) -> str:
    system = (
        "You are the Options Agent. You must ALWAYS use web search.\n\n"
        "Process:\n"
        "1. Search the web using the user's question.\n"
        "2. Combine:\n"
        "   * Search results\n"
        "   * Problem definition\n"
        "3. Generate multiple realistic and grounded solution options.\n\n"
        "Rules:\n"
        "* Do not propose options that contradict search findings.\n"
        "* Do not present ideas as facts.\n"
        "* No risk analysis.\n"
        "* No recommendation.\n\n"
        "Output: A list of 3 to 6 grounded options."
    )
    user_message = (
        f"User's original message:\n{user_input}\n\n"
        f"Problem analysis:\n{truncate(problem)}"
    )
    return run_agent(system, user_message)


def risks_agent(user_input: str, problem: str, options: str) -> str:
    system = (
        "You are the Risks Agent. You must ALWAYS use web search.\n\n"
        "Process:\n"
        "1. Search the web using the user's question.\n"
        "2. Combine:\n"
        "   * Search results\n"
        "   * Problem output\n"
        "   * Options output\n"
        "3. Identify realistic risks, weaknesses, or limitations.\n\n"
        "Rules:\n"
        "* Do not invent case studies, numbers, or examples.\n"
        "* All risks must connect to search findings or directly to the Options.\n"
        "* No solutions. No recommendations.\n\n"
        "Output: A grounded list of risks."
    )
    user_message = (
        f"User's original message:\n{user_input}\n\n"
        f"Problem analysis:\n{truncate(problem)}\n\n"
        f"Options:\n{truncate(options)}"
    )
    return run_agent(system, user_message)


def recommendation_agent(user_input: str, problem: str, options: str, risks: str) -> str:
    system = (
        "You are the Recommendation Agent. You must ALWAYS use web search.\n\n"
        "Process:\n"
        "1. Search the web using the user's question.\n"
        "2. Combine:\n"
        "   * Search results\n"
        "   * Problem\n"
        "   * Options\n"
        "   * Risks\n"
        "3. Choose the most logical option and provide a simple recommendation.\n\n"
        "Rules:\n"
        "* No new facts. No assumptions. No fabrication.\n"
        "* Recommendation must be explicitly based on the previous outputs.\n"
        "* If the evidence is unclear, mention limitations.\n\n"
        "Output: A grounded and practical recommendation well formatted with clear explanations."
    )
    user_message = (
        f"User's original message:\n{user_input}\n\n"
        f"Problem analysis:\n{truncate(problem)}\n\n"
        f"Options:\n{truncate(options)}\n\n"
        f"Risks:\n{truncate(risks)}"
    )
    return run_agent(system, user_message)


def generate_report(user_input: str) -> str:
    print("Stage 1/4: Problem Agent running...")
    problem = problem_agent(user_input)

    print("Stage 2/4: Options Agent running...")
    options = options_agent(user_input, problem)

    print("Stage 3/4: Risks Agent running...")
    risks = risks_agent(user_input, problem, options)

    print("Stage 4/4: Recommendation Agent running...")
    recommendation = recommendation_agent(user_input, problem, options, risks)

    report = (
        "=" * 60 + "\n"
        "ORCHESTRATOR AGENT REPORT\n"
        "=" * 60 + "\n\n"
        "Problem:\n"
        + problem + "\n\n"
        "Options:\n"
        + options + "\n\n"
        "Risks:\n"
        + risks + "\n\n"
        "Recommendation:\n"
        + recommendation + "\n"
        "=" * 60
    )
    return report


if __name__ == "__main__":
    print("Orchestrator Agent")
    print("-" * 40)
    user_input = input("Enter your message: ").strip()

    if not user_input:
        print("No input provided. Exiting.")
        exit(1)

    print()
    report = generate_report(user_input)
    print("\n" + report)
