"""
Concurrent Subprocess Access Test
==================================
m_flow.tests.test_concurrent_subprocess_access

Validates concurrent database access from multiple subprocesses:
- Parallel read/write operations via separate Python processes
- Concurrent memorize operations across different datasets
- Database locking and consistency under parallel access
"""

import pathlib
import subprocess
import asyncio
import sys

import m_flow
from m_flow.shared.logging_utils import get_logger

_logger = get_logger()


async def run_concurrent_access_tests():
    """
    Main test execution for concurrent subprocess access patterns.

    Tests both basic read/write and concurrent memorize scenarios.
    """
    # Configure storage paths
    test_root = pathlib.Path(__file__).parent
    data_dir = (test_root / ".data_storage" / "concurrent_tasks").resolve()
    system_dir = (test_root / ".mflow/system" / "concurrent_tasks").resolve()
    subprocess_dir = test_root / "subprocesses"

    m_flow.config.data_root_directory(str(data_dir))
    m_flow.config.system_root_directory(str(system_dir))

    # Initialize clean state
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # =========================================
    # Test 1: Basic concurrent read/write
    # =========================================
    _logger.info("Testing basic concurrent read/write access")

    writer_script = subprocess_dir / "writer.py"
    reader_script = subprocess_dir / "reader.py"

    writer_proc = subprocess.Popen([sys.executable, str(writer_script)])
    reader_proc = subprocess.Popen([sys.executable, str(reader_script)])

    # Wait for both processes to complete
    writer_proc.wait()
    reader_proc.wait()

    _logger.info("Basic read/write subprocess test completed")

    # =========================================
    # Test 2: Concurrent memorize operations
    # =========================================
    _logger.info("Testing concurrent memorize operations")

    # Reset state
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # Prepare datasets for concurrent processing
    content_a = """
    This is the text of the first memorize subprocess
    """
    content_b = """
    This is the text of the second memorize subprocess
    """

    await m_flow.add(content_a, dataset_name="first_memorize_dataset")
    await m_flow.add(content_b, dataset_name="second_memorize_dataset")

    memorize_script_1 = subprocess_dir / "simple_memorize_1.py"
    memorize_script_2 = subprocess_dir / "simple_memorize_2.py"

    proc_1 = subprocess.Popen([sys.executable, str(memorize_script_1)])
    proc_2 = subprocess.Popen([sys.executable, str(memorize_script_2)])

    # Wait for concurrent memorize to complete
    proc_1.wait()
    proc_2.wait()

    _logger.info("Concurrent memorize subprocess test completed")


if __name__ == "__main__":
    asyncio.run(run_concurrent_access_tests())
