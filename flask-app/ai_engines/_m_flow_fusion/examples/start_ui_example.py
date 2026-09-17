"""Launch the M-flow web UI with sample data pre-loaded."""

import asyncio
import time
import m_flow


async def run():
    # Seed the system with sample content
    print("Seeding sample data...")
    await m_flow.add("Deep learning uses neural networks with many layers to learn data representations.")
    await m_flow.add("Transformers are a type of neural network architecture used in NLP tasks.")
    await m_flow.memorize()
    print("Knowledge graph built.\n")

    # Start the web interface
    print("Launching M-flow UI on http://localhost:3000 ...")
    server = m_flow.start_ui(
        pid_callback=lambda _pid: None,
        port=3000,
        open_browser=True,
    )

    if not server:
        print("UI failed to start. Check logs.")
        return

    print("UI running. Press Ctrl+C to stop.\n")
    try:
        while server.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        server.terminate()
        server.wait()
        print("UI stopped.")


if __name__ == "__main__":
    asyncio.run(run())
