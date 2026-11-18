from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Optional
from crewai import LLM
import os
from dotenv import load_dotenv
from crewai_tools import SeleniumScrapingTool, SerperDevTool , ScrapeWebsiteTool

load_dotenv()

def get_default_llm() -> LLM:
    return LLM(model=os.getenv("MODEL", "openai/gpt-oss-120b"))

llm = get_default_llm()

web_search_tool = SerperDevTool()
selenium_scraper = SeleniumScrapingTool()
web_scraping_tool=ScrapeWebsiteTool()
toolkit = [web_search_tool,web_scraping_tool, selenium_scraper]


@CrewBase
class MarketResearchAgent():
    """MarketResearchAgent crew - conducts comprehensive market research for AI product ideas."""

    agents: List[BaseAgent]
    #configuration files
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm: Optional[LLM] = None):
        super().__init__()
        self.llm = llm or get_default_llm()

    @agent
    def market_research_specialist(self)->Agent:
        return Agent(
            config=self.agents_config['market_research_specialist'],
            tools=toolkit,
            llm=self.llm
        )
    
    @agent
    def competitive_intelligence_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["competitive_intelligence_analyst"],
            tools=toolkit,
            llm=self.llm
        )
        
    @agent
    def customer_insights_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["customer_insights_researcher"],
            tools=toolkit,
            llm=self.llm
        )
        
    @agent
    def product_strategy_advisor(self) -> Agent:
        return Agent(
            config=self.agents_config["product_strategy_advisor"],
            tools=toolkit,
            llm=self.llm
        )
        
    @agent
    def business_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["business_analyst"],
            tools=toolkit,
            llm=self.llm
        )
        
    # ================ Tasks ======================
    
    @task
    def market_research_task(self) -> Task:
        return Task(
            config=self.tasks_config["market_research_task"]
        )
        
    @task
    def competitive_intelligence_task(self) -> Task:
        return Task(
            config=self.tasks_config["competitive_intelligence_task"],
            context=[self.market_research_task()]
        )
        
    @task
    def customer_insights_task(self) -> Task:
        return Task(
            config=self.tasks_config["customer_insights_task"],
            context=[self.market_research_task(),
                     self.competitive_intelligence_task()]
        )
        
    @task
    def product_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config["product_strategy_task"],
            context=[self.market_research_task(),
                     self.competitive_intelligence_task(),
                     self.customer_insights_task()]
        )
        
    @task
    def business_analyst_task(self) -> Task:
        return Task(
            config=self.tasks_config["business_analyst_task"],
            context=[self.market_research_task(),
                     self.competitive_intelligence_task(),
                     self.customer_insights_task(),
                     self.product_strategy_task()],
            output_file="reports/report.md"
        )
        
    # ================= Crew ===========================
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential
        )