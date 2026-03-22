from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-wukong",
    version="1.0.0",
    description="CLI harness for Wukong Accounting (悟空财务) — command-line interface to the finance REST API",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=[
        "click>=8.0.0",
        "prompt-toolkit>=3.0.0",
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-wukong=cli_anything.wukong.wukong_cli:main",
        ],
    },
    package_data={
        "cli_anything.wukong": ["skills/*.md"],
    },
    python_requires=">=3.10",
)
