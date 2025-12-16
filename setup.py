from setuptools import setup, find_packages

setup(
    name="ai-orchestrator",
    version="0.1.0",
    description="Professional AI Agent Orchestrator System",
    author="AI Systems Architect",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "typing-extensions>=4.8.0"
    ],
    test_suite="tests",
)


