import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-opus-4-7"


TOOLS = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]


def run_agent(system_prompt: str, user_message: str) -> str:
    messages = [{"role": "user", "content": user_message}]
    response = None

    for _ in range(10):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            break

        # Append assistant turn; Anthropic executes web_search server-side
        # and injects results automatically on the next request.
        messages.append({"role": "assistant", "content": response.content})

    text_blocks = [b.text for b in response.content if hasattr(b, "type") and b.type == "text"]
    return "\n".join(text_blocks).strip()


def problem_agent(user_input: str) -> str:
    system = (
        "You are the Problem Agent. You must ALWAYS call the Claude Search tool if available.\n\n"
        "Process:\n"
        "1. Call Claude Search using the user's question.\n"
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
        "You are the Options Agent. You must ALWAYS call the Claude Search tool if available.\n\n"
        "Process:\n"
        "1. Call Claude Search using the user's question.\n"
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
        f"Problem analysis:\n{problem}"
    )
    return run_agent(system, user_message)


def risks_agent(user_input: str, problem: str, options: str) -> str:
    system = (
        "You are the Risks Agent. You must ALWAYS call the Claude Search tool if available.\n\n"
        "Process:\n"
        "1. Call Claude Search using the user's question.\n"
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
        f"Problem analysis:\n{problem}\n\n"
        f"Options:\n{options}"
    )
    return run_agent(system, user_message)


def recommendation_agent(user_input: str, problem: str, options: str, risks: str) -> str:
    system = (
        "You are the Recommendation Agent. You must ALWAYS call the Claude Search tool if available.\n\n"
        "Process:\n"
        "1. Call Claude Search using the user's question.\n"
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
        "Output: A grounded and practical recommendation well formatted with clear explanations and in a PDF format."
    )
    user_message = (
        f"User's original message:\n{user_input}\n\n"
        f"Problem analysis:\n{problem}\n\n"
        f"Options:\n{options}\n\n"
        f"Risks:\n{risks}"
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
