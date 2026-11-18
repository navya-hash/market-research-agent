# MarketReserachAgent Crew

Welcome to the MarketReserachAgent Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/market_reserach_agent/config/agents.yaml` to define your agents
- Modify `src/market_reserach_agent/config/tasks.yaml` to define your tasks
- Modify `src/market_reserach_agent/crew.py` to add your own logic, tools and specific args
- Modify `src/market_reserach_agent/main.py` to add custom inputs for your agents and tasks

## Running the Project

### Option 1: Interactive Streamlit Web UI (Recommended)
You can launch the web interface to input product ideas, configure models, watch live agent execution logs, and review/download reports:

```bash
# Using the run script (Windows)
run_ui.bat

# Or directly with python/streamlit
.venv\Scripts\streamlit run app.py
```

Open your browser at `http://localhost:8501`.

### Multi-User Authentication
The web app includes multi-user login and registration powered by `streamlit-authenticator`:
- **Self-Service Registration**: New users can click the **📝 Create Account** tab directly on the web interface, register their details, and immediately sign in.
- **Pre-configured Accounts** (stored with secure bcrypt hashes in `config/auth.yaml`):
  - **Admin**: Username: `admin` | Password: `adminpassword123`
  - **Analyst**: Username: `analyst` | Password: `analystpassword123`
- **Admin CLI Management**: To manually add or list users via command line:
  ```bash
  .venv\Scripts\python manage_users.py add <username> <password> <email> <first_name> <last_name> [role]
  .venv\Scripts\python manage_users.py list
  ```
- **Optional Toggle**: To bypass authentication during local development, set `ENABLE_AUTH=false` in `.env`.

### Option 2: Command Line (CLI)
To run the crew from the command line:

```bash
.venv\Scripts\python -m market_research_agent.main
```
or:
```bash
crewai run
```

## Understanding Your Crew

The market_reserach_agent Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the MarketReserachAgent Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
