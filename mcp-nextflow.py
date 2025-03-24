import logging
import traceback
from fastmcp import FastMCP, Context
import subprocess
import os
import re
from typing import List

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("nextflow-dev-mcp")

# Create FastMCP instance with appropriate dependencies
mcp = FastMCP(
    "Nextflow Developer Tools",
    description="Tools for Nextflow development and testing",
    dependencies=["pytest"],
)

# Default Nextflow directory path
NEXTFLOW_DIR = os.environ.get("NEXTFLOW_DIR", os.path.expanduser("~/nextflow"))


def get_makefile_targets() -> List[str]:
    """
    Parse the Makefile in the Nextflow directory to extract available targets.

    Returns:
        List of available make targets
    """
    targets = []
    makefile_path = os.path.join(NEXTFLOW_DIR, "Makefile")

    if not os.path.isfile(makefile_path):
        logger.error(f"Makefile not found at {makefile_path}")
        return []

    try:
        with open(makefile_path, "r") as f:
            content = f.read()

        # Find target definitions (lines ending with a colon that aren't part of conditionals or variables)
        target_pattern = r"^([a-zA-Z0-9_-]+):\s*(?:#.*)?$"
        targets = re.findall(target_pattern, content, re.MULTILINE)
        logger.info(f"Found {len(targets)} make targets in {makefile_path}")
        return targets
    except Exception as e:
        logger.error(f"Error parsing Makefile: {str(e)}")
        logger.debug(traceback.format_exc())
        return []


@mcp.tool()
def list_make_targets() -> str:
    """
    List all available make targets in the Nextflow repository.

    Returns:
        List of available make targets
    """
    targets = get_makefile_targets()

    if not targets:
        error_msg = f"Could not find any make targets in {NEXTFLOW_DIR}/Makefile. Please check if the Nextflow directory is set correctly."
        logger.error(error_msg)
        return error_msg

    success_msg = "Available make targets:\n" + "\n".join(
        f"- {target}" for target in sorted(targets)
    )
    logger.info(f"Listed {len(targets)} make targets")
    return success_msg


@mcp.tool()
def set_nextflow_directory(path: str) -> str:
    """
    Set the Nextflow development directory path.

    Args:
        path: The path to the Nextflow development directory

    Returns:
        Confirmation message
    """
    global NEXTFLOW_DIR

    logger.info(f"Attempting to set Nextflow directory to: {path}")

    # Expand user directory if needed
    expanded_path = os.path.expanduser(path)

    # Verify the path exists
    if not os.path.isdir(expanded_path):
        error_msg = f"Error: Directory '{expanded_path}' does not exist."
        logger.error(error_msg)
        return error_msg

    # Check if it looks like a Nextflow repository (contains Makefile or build.gradle)
    if not (
        os.path.isfile(os.path.join(expanded_path, "Makefile"))
        or os.path.isfile(os.path.join(expanded_path, "build.gradle"))
    ):
        warning_msg = f"Warning: '{expanded_path}' might not be a Nextflow repository. Setting anyway."
        logger.warning(warning_msg)
        NEXTFLOW_DIR = expanded_path
        return warning_msg

    NEXTFLOW_DIR = expanded_path
    success_msg = f"Nextflow directory set to: {NEXTFLOW_DIR}"
    logger.info(success_msg)
    return success_msg


@mcp.tool()
def get_nextflow_directory() -> str:
    """
    Get the current Nextflow development directory path.

    Returns:
        The path to the Nextflow development directory
    """
    msg = f"Current Nextflow directory: {NEXTFLOW_DIR}"
    logger.info(msg)
    return msg


@mcp.tool()
def run_make_command(command: str, ctx: Context) -> str:
    """
    Run a make command in the Nextflow repository.

    Args:
        command: The make command to run (e.g., "test", "compile", "clean")

    Returns:
        The output of the make command
    """
    # Validate the command against available targets
    logger.info(f"Attempting to run make command: {command}")
    available_targets = get_makefile_targets()

    if not available_targets:
        error_msg = f"Could not read Makefile targets from {NEXTFLOW_DIR}/Makefile. Please check if the Nextflow directory is set correctly."
        ctx.error(error_msg)
        logger.error(error_msg)
        return error_msg

    if command not in available_targets:
        error_msg = (
            f"Error: '{command}' is not a valid make target. Available targets are:\n"
            + "\n".join(f"- {target}" for target in sorted(available_targets))
        )
        ctx.error(f"Invalid make target: {command}")
        logger.error(f"Invalid make target: {command}")
        return error_msg

    ctx.info(f"Running make {command} in {NEXTFLOW_DIR}")
    logger.info(f"Running make {command} in {NEXTFLOW_DIR}")

    try:
        process = subprocess.run(
            ["make", command],
            capture_output=True,
            text=True,
            cwd=NEXTFLOW_DIR,
        )

        if process.returncode != 0:
            error_msg = f"Command 'make {command}' failed with exit code {process.returncode}:\nStdout: {process.stdout}\nStderr: {process.stderr}"
            ctx.error(error_msg)
            logger.error(f"make {command} failed with exit code {process.returncode}")
            logger.debug(f"Stdout: {process.stdout}")
            logger.debug(f"Stderr: {process.stderr}")
            return error_msg

        success_msg = f"Command 'make {command}' succeeded:\n{process.stdout}"
        ctx.info(f"make {command} completed successfully")
        logger.info(f"make {command} completed successfully")
        return success_msg
    except Exception as e:
        error_msg = f"Exception running make {command}: {str(e)}"
        ctx.error(error_msg)
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        return error_msg


@mcp.tool()
def run_specific_test(test_path: str, ctx: Context) -> str:
    """
    Run a specific Nextflow test.

    Args:
        test_path: Path to the test (e.g., "validation_test.nf")

    Returns:
        The test results
    """
    ctx.info(f"Running specific test: {test_path} in {NEXTFLOW_DIR}")
    logger.info(f"Running specific test: {test_path} in {NEXTFLOW_DIR}")

    try:
        process = subprocess.run(
            ["./gradlew", "test", "--tests", test_path],
            capture_output=True,
            text=True,
            cwd=NEXTFLOW_DIR,
        )

        if process.returncode != 0:
            error_msg = f"Test failed with exit code {process.returncode}:\nStdout: {process.stdout}\nStderr: {process.stderr}"
            ctx.error(error_msg)
            logger.error(f"Test {test_path} failed with exit code {process.returncode}")
            logger.debug(f"Stdout: {process.stdout}")
            logger.debug(f"Stderr: {process.stderr}")
            return error_msg

        success_msg = f"Test completed successfully:\n{process.stdout}"
        ctx.info(f"Test {test_path} completed successfully")
        logger.info(f"Test {test_path} completed successfully")
        return success_msg
    except Exception as e:
        error_msg = f"Exception running test {test_path}: {str(e)}"
        ctx.error(error_msg)
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        return error_msg


@mcp.tool()
def build_nextflow(ctx: Context) -> str:
    """
    Build Nextflow from source.

    Returns:
        Build output
    """
    # Check if 'compile' is a valid target
    available_targets = get_makefile_targets()
    build_target = "compile"

    ctx.info(f"Attempting to build Nextflow in {NEXTFLOW_DIR}")
    logger.info(f"Attempting to build Nextflow in {NEXTFLOW_DIR}")

    if build_target not in available_targets:
        if "build" in available_targets:
            build_target = "build"
            logger.info(f"Compile target not found, using 'build' instead")
        else:
            error_msg = (
                f"Error: Neither 'compile' nor 'build' targets found in Makefile. Available targets are:\n"
                + "\n".join(f"- {target}" for target in sorted(available_targets))
            )
            ctx.error(error_msg)
            logger.error("No suitable build target found in Makefile")
            return error_msg

    ctx.info(
        f"Building Nextflow from source in {NEXTFLOW_DIR} using 'make {build_target}'"
    )
    logger.info(f"Building using 'make {build_target}'")

    try:
        process = subprocess.run(
            ["make", build_target],
            capture_output=True,
            text=True,
            cwd=NEXTFLOW_DIR,
        )

        if process.returncode != 0:
            error_msg = f"Build failed with exit code {process.returncode}:\nStdout: {process.stdout}\nStderr: {process.stderr}"
            ctx.error(error_msg)
            logger.error(f"Build failed with exit code {process.returncode}")
            logger.debug(f"Stdout: {process.stdout}")
            logger.debug(f"Stderr: {process.stderr}")
            return error_msg

        success_msg = f"Build succeeded:\n{process.stdout}"
        ctx.info("Build completed successfully")
        logger.info("Build completed successfully")
        return success_msg
    except Exception as e:
        error_msg = f"Exception during build: {str(e)}"
        ctx.error(error_msg)
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        return error_msg


@mcp.tool()
def run_integration_tests(ctx: Context) -> str:
    """
    Run Nextflow integration tests.

    Returns:
        Test results
    """
    ctx.info(f"Running integration tests in {NEXTFLOW_DIR}")
    logger.info(f"Running integration tests in {NEXTFLOW_DIR}")

    try:
        process = subprocess.run(
            ["make", "test"],
            capture_output=True,
            text=True,
            cwd=NEXTFLOW_DIR,
        )

        if process.returncode != 0:
            error_msg = f"Integration tests failed with exit code {process.returncode}:\nStdout: {process.stdout}\nStderr: {process.stderr}"
            ctx.error(error_msg)
            logger.error(
                f"Integration tests failed with exit code {process.returncode}"
            )
            logger.debug(f"Stdout: {process.stdout}")
            logger.debug(f"Stderr: {process.stderr}")
            return error_msg

        success_msg = f"Integration tests completed:\n{process.stdout}"
        ctx.info("Integration tests completed successfully")
        logger.info("Integration tests completed successfully")
        return success_msg
    except Exception as e:
        error_msg = f"Exception running integration tests: {str(e)}"
        ctx.error(error_msg)
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        return error_msg


@mcp.tool()
def get_nextflow_version() -> str:
    """
    Get the current Nextflow version.

    Returns:
        Nextflow version information
    """
    logger.info(f"Getting Nextflow version from {NEXTFLOW_DIR}")

    try:
        process = subprocess.run(
            ["./nextflow", "-version"],
            capture_output=True,
            text=True,
            cwd=NEXTFLOW_DIR,
        )

        if process.returncode != 0:
            error_msg = f"Error getting version. Exit code {process.returncode}: {process.stderr}"
            logger.error(error_msg)
            return error_msg

        version_info = process.stdout.strip()
        logger.info(f"Successfully retrieved Nextflow version")
        logger.debug(f"Version info: {version_info}")
        return version_info
    except Exception as e:
        error_msg = f"Exception getting Nextflow version: {str(e)}"
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        return error_msg


@mcp.resource("docs://{topic}")
def get_nextflow_docs(topic: str) -> str:
    """
    Retrieve documentation about a specific Nextflow development topic.

    Args:
        topic: The documentation topic to retrieve

    Returns:
        Documentation content
    """
    # Map of topics to their documentation content
    docs = {
        "testing": """
# Nextflow Testing Guidelines

Nextflow tests are organized into the following categories:
- Unit tests: Test individual components
- Integration tests: Test the workflow system
- Functional tests: Test complete pipeline execution

## Running Tests
- Unit tests: `make test`
- Integration tests: `make integration-tests`
- Specific test: `./gradlew test --tests TestName`
""",
        "contributing": """
# Contributing to Nextflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests for your changes
5. Run tests with `make test`
6. Submit a pull request

See the full guidelines at: https://www.nextflow.io/docs/latest/developer/index.html
""",
    }

    return docs.get(topic, f"Documentation for '{topic}' not found.")


@mcp.prompt()
def debug_error(error: str) -> str:
    """
    Create a prompt to help debug Nextflow errors.

    Args:
        error: The error message to debug

    Returns:
        A prompt for debugging the error
    """
    return f"""
I'm encountering the following error while developing Nextflow:

{error}


Please help me understand:
1. What might be causing this error
2. How to fix it
3. Any relevant parts of the Nextflow codebase I should investigate
"""


@mcp.tool()
def run_development_nextflow(ctx: Context, command: str = "") -> str:
    """
    Run the development version of Nextflow using launch.sh script.

    Args:
        command: Optional Nextflow command/parameters to run (e.g., "run hello.nf", "-version")
        ctx: MCP context for logging (optional)

    Returns:
        The output from the Nextflow execution
    """
    # First check if launch.sh exists
    launch_script = os.path.join(NEXTFLOW_DIR, "launch.sh")

    log_info = ctx.info if ctx else logger.info
    log_error = ctx.error if ctx else logger.error

    log_info(f"Checking for launch.sh at {launch_script}")
    logger.info(f"Checking for launch.sh at {launch_script}")

    if not os.path.isfile(launch_script):
        error_msg = f"Error: launch.sh script not found at {launch_script}. Make sure the Nextflow directory is correct."
        log_error(error_msg)
        logger.error(error_msg)
        return error_msg

    # Check if compilation is needed first
    log_info("Checking if compilation is needed before running Nextflow")
    logger.info("Checking if compilation is needed before running Nextflow")
    available_targets = get_makefile_targets()

    if "compile" in available_targets:
        try:
            log_info("Compiling Nextflow before running")
            logger.info("Compiling Nextflow before running")

            # Capture stderr separately for better error reporting
            process = subprocess.run(
                ["make", "compile"], capture_output=True, text=True, cwd=NEXTFLOW_DIR
            )

            if process.returncode != 0:
                error_msg = f"Failed to compile Nextflow before running:\nExit code: {process.returncode}\nStdout: {process.stdout}\nStderr: {process.stderr}"
                log_error(error_msg)
                logger.error(f"Compilation failed with exit code {process.returncode}")
                logger.debug(f"Stdout: {process.stdout}")
                logger.debug(f"Stderr: {process.stderr}")
                return error_msg

        except Exception as e:
            error_msg = f"Exception during compilation: {str(e)}"
            log_error(error_msg)
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            return error_msg

    # Run Nextflow using launch.sh
    cmd_str = "./launch.sh " + command if command else "./launch.sh"
    log_info(f"Running development Nextflow with command: {cmd_str}")
    logger.info(f"Running development Nextflow with command: {cmd_str}")

    try:
        cmd = ["./launch.sh"]
        if command:
            # Split the command string into arguments
            cmd.extend(command.split())

        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=NEXTFLOW_DIR,
        )

        if process.returncode != 0:
            error_msg = f"Development Nextflow execution failed with exit code {process.returncode}:\nStdout: {process.stdout}\nStderr: {process.stderr}"
            log_error(error_msg)
            logger.error(
                f"Nextflow execution failed with exit code {process.returncode}"
            )
            logger.debug(f"Stdout: {process.stdout}")
            logger.debug(f"Stderr: {process.stderr}")
            return error_msg

        success_msg = f"Development Nextflow execution succeeded:\n{process.stdout}"
        log_info("Nextflow execution completed successfully")
        logger.info("Nextflow execution completed successfully")
        return success_msg

    except Exception as e:
        error_msg = f"Exception during Nextflow execution: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        return error_msg


@mcp.tool()
def run_plugin_test(ctx: Context, module: str, class_name: str | None = None) -> str:
    """
    Run tests for a specific Nextflow plugin or module.

    Args:
        module: The module to test (e.g., "nextflow", "plugins:nf-amazon")
        class_name: Optional specific test class or method (e.g., "nextflow.util.CacheTest" or "nextflow.util.CacheTest.testMethod")
        ctx: MCP context for logging (optional)

    Returns:
        The output from the test execution
    """
    log_info = ctx.info if ctx else logger.info
    log_error = ctx.error if ctx else logger.error

    log_info(
        f"Preparing to run tests for module: {module}"
        + (f", class: {class_name}" if class_name else "")
    )
    logger.info(
        f"Running plugin test with module={module}"
        + (f", class={class_name}" if class_name else "")
    )

    # Build the command
    cmd = ["make", "test"]

    # Add module parameter
    cmd.extend([f"module={module}"])

    # Add class parameter if provided
    if class_name:
        cmd.extend([f"class={class_name}"])

    log_info(f"Executing command: {' '.join(cmd)}")
    logger.info(f"Executing: {' '.join(cmd)}")

    try:
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=NEXTFLOW_DIR,
        )

        if process.returncode != 0:
            error_msg = f"Plugin test failed with exit code {process.returncode}:\nStdout: {process.stdout}\nStderr: {process.stderr}"
            log_error(error_msg)
            logger.error(f"Plugin test failed with exit code {process.returncode}")
            logger.debug(f"Stdout: {process.stdout}")
            logger.debug(f"Stderr: {process.stderr}")
            return error_msg

        success_msg = f"Plugin test completed successfully:\n{process.stdout}"
        log_info(
            f"Plugin test for {module}"
            + (f" class {class_name}" if class_name else "")
            + " completed successfully"
        )
        logger.info("Plugin test completed successfully")
        return success_msg

    except Exception as e:
        error_msg = f"Exception during plugin test: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        return error_msg


if __name__ == "__main__":
    try:
        logger.info("Starting Nextflow Developer Tools MCP")
        mcp.run()
    except Exception as e:
        logger.critical(f"Fatal error in MCP: {str(e)}")
        logger.debug(traceback.format_exc())
        raise
