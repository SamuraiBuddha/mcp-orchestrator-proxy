from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-orchestrator-proxy",
    version="0.1.0",
    author="Jordan Ehrig",
    author_email="jordan@example.com",
    description="MCP Orchestrator with full execution proxy - spawns and controls MCP servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SamuraiBuddha/mcp-orchestrator-proxy",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "mcp>=0.9.1",
        "sentence-transformers>=2.2.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-orchestrator-proxy=mcp_orchestrator_proxy.server:main",
        ],
    },
    include_package_data=True,
    package_data={
        "mcp_orchestrator_proxy": ["config/*.json"],
    },
)