import asyncio
import m_flow
import os

from pprint import pprint

# By default m_flow uses OpenAI's gpt-5-mini LLM model
# Provide your OpenAI LLM API KEY
os.environ["LLM_API_KEY"] = ""


async def m_flow_demo():
    # Get file path to document to process
    from pathlib import Path

    current_directory = Path(__file__).resolve().parent.parent
    file_path = os.path.join(current_directory, "data", "alice_in_wonderland.txt")

    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # Call Mflow to process document
    await m_flow.add(file_path)
    await m_flow.memorize()

    # Query Mflow for information from provided document
    answer = await m_flow.search("List me all the important characters in Alice in Wonderland.")
    pprint(answer)

    answer = await m_flow.search("How did Alice end up in Wonderland?")
    pprint(answer)

    answer = await m_flow.search("Tell me about Alice's personality.")
    pprint(answer)


# Mflow is an async library, it has to be called in an async context
asyncio.run(m_flow_demo())
