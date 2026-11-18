#!/usr/bin/env python
import sys
import warnings

from market_research_agent.crew import MarketResearchAgent

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crew.
    """
    # Ensure reports directory exists before crew writes output
    import pathlib
    pathlib.Path("reports").mkdir(parents=True, exist_ok=True)

    inputs = {
        "product_idea": "An AI powered tool that summarizes youtube videos on my channel and posts the summary on various social media platforms like LinkedIn, Instagram, Facebook, X, WhatsApp",
    }

    try:
        MarketResearchAgent().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

