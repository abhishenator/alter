"""
ALTER CLI - Command-line interface for ALTER system.

Provides commands for:
- User initialization and setup
- Running meta-loop cycles
- Managing goals and purpose
- Constitution management
- Daily planning and reflections
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from pathlib import Path
import time
from datetime import datetime, date
from typing import Optional

# Load .env file if present
from pathlib import Path as _P
_env_file = _P(__file__).resolve().parents[2] / ".env"
if _env_file.exists():
    import os as _os
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                _os.environ.setdefault(_k.strip(), _v.strip())

from alter.core.user_model import UserModel, Goal
from alter.core.state import SystemState
from alter.core.meta_loop import MetaLoop
from alter.core.constitution import Constitution

app = typer.Typer(
    name="alter",
    help="ALTER - Adaptive Life Transformation & Evolution Runtime",
    add_completion=False
)
console = Console()


# Helper Functions

def get_user_path(user_id: str) -> Path:
    """Get the path to user data directory."""
    return Path(f"data/user_data/{user_id}")


def load_user_and_state(user_id: str) -> tuple[UserModel, SystemState, MetaLoop]:
    """Load user, state, and initialize meta-loop."""
    try:
        user = UserModel.load(user_id)
        state = SystemState.load(user_id)
        constitution = Constitution.load()
        meta_loop = MetaLoop(state=state, constitution=constitution)
        return user, state, meta_loop
    except FileNotFoundError:
        console.print(f"[red]Error: User '{user_id}' not found. Run 'alter init' first.[/red]")
        raise typer.Exit(1)


def save_user_and_state(user: UserModel, state: SystemState) -> None:
    """Save user and state to disk."""
    user.save()
    state.save()


# Commands

@app.command()
def init(
    user_id: str = typer.Option(
        ...,
        "--user-id",
        "-u",
        prompt="User ID (e.g., your name)",
        help="Unique identifier for this user"
    ),
    purpose: Optional[str] = typer.Option(
        None,
        "--purpose",
        "-p",
        help="Your life purpose statement"
    )
):
    """
    Initialize ALTER for a new user.

    Creates user profile, loads default constitution, and sets up system state.
    """
    user_path = get_user_path(user_id)

    if user_path.exists():
        overwrite = typer.confirm(f"User '{user_id}' already exists. Overwrite?")
        if not overwrite:
            console.print("[yellow]Initialization cancelled.[/yellow]")
            raise typer.Exit(0)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Initializing ALTER...", total=None)

        # Create user
        user = UserModel.create_new(user_id=user_id)

        if purpose:
            user.set_purpose(purpose)

        # Create system state
        state = SystemState.create(user_model=user)

        # Save
        user.save()
        state.save()

        progress.update(task, completed=True)

    console.print()
    console.print(Panel.fit(
        f"[green]✓ ALTER initialized successfully![/green]\n\n"
        f"User ID: [cyan]{user_id}[/cyan]\n"
        f"Purpose: [yellow]{purpose or 'Not set yet'}[/yellow]\n\n"
        f"Next steps:\n"
        f"  • Set your purpose: [dim]alter purpose set[/dim]\n"
        f"  • Add goals: [dim]alter goal add[/dim]\n"
        f"  • Run your first cycle: [dim]alter cycle run[/dim]",
        title="🎉 Welcome to ALTER",
        border_style="green"
    ))


@app.command()
def status(
    user_id: str = typer.Option("default", "--user-id", "-u", help="User ID")
):
    """
    Show current system status and life state overview.
    """
    user, state, meta_loop = load_user_and_state(user_id)

    # Header
    console.print()
    console.print(Panel.fit(
        f"[cyan bold]{user.user_id}[/cyan bold]",
        title="ALTER Status",
        border_style="cyan"
    ))
    console.print()

    # Purpose
    console.print("[bold]Life Purpose:[/bold]")
    if user.purpose_statement:
        console.print(f"  {user.purpose_statement}")
    else:
        console.print("  [dim]Not set - use 'alter purpose set' to define your purpose[/dim]")
    console.print()

    # Goals
    active_goals = user.get_active_goals()
    console.print(f"[bold]Active Goals:[/bold] {len(active_goals)}")

    if active_goals:
        for i, goal in enumerate(active_goals[:5], 1):
            console.print(f"  {i}. [{goal.domain}] {goal.description} ({goal.time_horizon})")
        if len(active_goals) > 5:
            console.print(f"  [dim]... and {len(active_goals) - 5} more[/dim]")
    else:
        console.print("  [dim]No active goals - use 'alter goal add' to create goals[/dim]")
    console.print()

    # Meta-loop stats
    console.print("[bold]Meta-Loop:[/bold]")
    console.print(f"  Cycles completed: {state.meta_state.cycle_count}")
    if state.meta_state.last_execution:
        console.print(f"  Last execution: {state.meta_state.last_execution.strftime('%Y-%m-%d %H:%M')}")
    console.print()

    # Life domains
    constitution = Constitution.load()
    domains = constitution.get_life_domains()

    console.print("[bold]Life Domains:[/bold]")
    for domain in domains[:5]:
        console.print(f"  • {domain.name}")
    console.print()


@app.command()
def cycle(
    user_id: str = typer.Option("default", "--user-id", "-u", help="User ID")
):
    """
    Run a complete meta-loop cycle (Reflect → Reason → Plan → Execute → Evolve).
    """
    user, state, meta_loop = load_user_and_state(user_id)

    console.print()
    console.print("[bold cyan]Running Meta-Loop Cycle[/bold cyan]")
    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Reflect
        task = progress.add_task("Phase 1/5: Reflecting on life state...", total=None)
        reflection = meta_loop.reflect()
        time.sleep(0.5)
        progress.update(task, completed=True)

        # Reason
        task = progress.add_task("Phase 2/5: Reasoning about priorities...", total=None)
        reasoning = meta_loop.reason()
        time.sleep(0.5)
        progress.update(task, completed=True)

        # Plan
        task = progress.add_task("Phase 3/5: Planning strategies and tasks...", total=None)
        plan = meta_loop.plan()
        time.sleep(0.5)
        progress.update(task, completed=True)

        # Execute
        task = progress.add_task("Phase 4/5: Dispatching agents...", total=None)
        execution = meta_loop.execute(plan.agent_missions)
        time.sleep(0.5)
        progress.update(task, completed=True)

        # Evolve
        task = progress.add_task("Phase 5/5: Evolving and learning...", total=None)
        evolution = meta_loop.evolve([])
        time.sleep(0.5)
        progress.update(task, completed=True)

        # Update state
        state.meta_state.cycle_count += 1
        state.meta_state.last_execution = datetime.now()

    console.print()
    console.print(Panel.fit(
        f"[green]✓ Cycle completed successfully![/green]\n\n"
        f"Strategies created: {len(plan.strategies)}\n"
        f"Tasks generated: {len(plan.tasks)}\n"
        f"Agents dispatched: {len(execution.agents_dispatched)}\n\n"
        f"Run [cyan]alter plan-day[/cyan] to see your daily plan.",
        title="Cycle Complete",
        border_style="green"
    ))
    console.print()

    # Save state
    save_user_and_state(user, state)


@app.command("plan-day")
def plan_day(
    user_id: str = typer.Option("default", "--user-id", "-u", help="User ID"),
    date_str: Optional[str] = typer.Option(None, "--date", "-d", help="Date (YYYY-MM-DD)")
):
    """
    Generate daily tactical plan with prioritized tasks.
    """
    user, state, meta_loop = load_user_and_state(user_id)

    target_date = date_str or datetime.now().date().isoformat()

    console.print()
    console.print(f"[bold cyan]Daily Plan - {target_date}[/bold cyan]")
    console.print()

    # Run daily planning
    result = meta_loop.run_daily_planning()

    if result.daily_plan and result.daily_plan.get("tasks"):
        table = Table(title="Today's Tasks", box=box.ROUNDED)
        table.add_column("Priority", style="cyan", width=8)
        table.add_column("Task", style="white")
        table.add_column("Domain", style="yellow", width=12)
        table.add_column("Est. Time", style="green", width=10)

        for i, task in enumerate(result.daily_plan["tasks"], 1):
            table.add_row(
                f"#{i}",
                task["task"],
                task["domain"],
                f"{task['estimated_hours']}h"
            )

        console.print(table)
    else:
        console.print("[yellow]No tasks scheduled for today. Add some goals first![/yellow]")

    console.print()

    # Save state
    save_user_and_state(user, state)


@app.command("plan-week")
def plan_week(
    user_id: str = typer.Option("default", "--user-id", "-u", help="User ID")
):
    """
    Run weekly strategic reflection and generate insights.
    """
    user, state, meta_loop = load_user_and_state(user_id)

    console.print()
    console.print("[bold cyan]Weekly Strategic Reflection[/bold cyan]")
    console.print()

    result = meta_loop.run_weekly_reflection()

    if result.weekly_insights:
        console.print(Panel(
            f"[bold]Key Insights:[/bold]\n\n" +
            "\n".join(f"  • {insight}" for insight in result.weekly_insights.get("key_insights", [])),
            title="Weekly Reflection",
            border_style="cyan"
        ))

    console.print()

    # Save state
    save_user_and_state(user, state)


@app.command("plan-month")
def plan_month(
    user_id: str = typer.Option("default", "--user-id", "-u", help="User ID")
):
    """
    Run monthly strategic planning and goal review.
    """
    user, state, meta_loop = load_user_and_state(user_id)

    console.print()
    console.print("[bold cyan]Monthly Strategic Planning[/bold cyan]")
    console.print()

    result = meta_loop.run_monthly_planning()

    if result.goal_adjustments:
        console.print("[bold]Goal Adjustments:[/bold]")
        for adjustment in result.goal_adjustments:
            console.print(f"  • {adjustment}")

    console.print()

    # Save state
    save_user_and_state(user, state)


# Goal Management

goal_app = typer.Typer(help="Manage goals")
app.add_typer(goal_app, name="goal")


@goal_app.command("add")
def goal_add(
    description: str = typer.Argument(..., help="Goal description"),
    domain: str = typer.Option(..., "--domain", "-d", help="Life domain (health, wealth, relationships, etc.)"),
    time_horizon: str = typer.Option("quarter", "--horizon", "-h", help="Time horizon (life, 5_year, 1_year, quarter, month, week, day)"),
    user_id: str = typer.Option("default", "--user-id", "-u", help="User ID")
):
    """
    Add a new goal.
    """
    user, state, _ = load_user_and_state(user_id)

    import uuid
    goal = Goal(
        id=str(uuid.uuid4()),
        domain=domain,
        description=description,
        time_horizon=time_horizon
    )

    user.add_goal(goal)
    save_user_and_state(user, state)

    console.print(f"[green]✓ Goal added successfully![/green]")
    console.print(f"  Domain: {domain}")
    console.print(f"  Horizon: {time_horizon}")
    console.print(f"  Description: {description}")


@goal_app.command("list")
def goal_list(
    user_id: str = typer.Option("default", "--user-id", "-u", help="User ID"),
    domain: Optional[str] = typer.Option(None, "--domain", "-d", help="Filter by domain"),
    horizon: Optional[str] = typer.Option(None, "--horizon", "-h", help="Filter by time horizon")
):
    """
    List all goals.
    """
    user, _, _ = load_user_and_state(user_id)

    goals = user.get_active_goals()

    if domain:
        goals = [g for g in goals if g.domain == domain]

    if horizon:
        goals = [g for g in goals if g.time_horizon == horizon]

    if not goals:
        console.print("[yellow]No goals found.[/yellow]")
        return

    table = Table(title="Goals", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=8)
    table.add_column("Domain", style="cyan", width=12)
    table.add_column("Horizon", style="yellow", width=10)
    table.add_column("Description", style="white")
    table.add_column("Status", style="green", width=10)

    for goal in goals:
        table.add_row(
            goal.id[:8],
            goal.domain,
            goal.time_horizon,
            goal.description,
            goal.status
        )

    console.print()
    console.print(table)
    console.print()


@goal_app.command("complete")
def goal_complete(
    goal_id: str = typer.Argument(..., help="Goal ID (first 8 characters)"),
    user_id: str = typer.Option("default", "--user-id", "-u", help="User ID"),
    outcome: str = typer.Option("success", "--outcome", "-o", help="Outcome (success, partial, failure)")
):
    """
    Mark a goal as completed.
    """
    user, state, _ = load_user_and_state(user_id)

    # Find goal by partial ID
    goal = None
    for g in user.goals:
        if g.id.startswith(goal_id):
            goal = g
            break

    if not goal:
        console.print(f"[red]Goal '{goal_id}' not found.[/red]")
        raise typer.Exit(1)

    user.complete_goal(goal.id, outcome=outcome)
    save_user_and_state(user, state)

    console.print(f"[green]✓ Goal completed![/green]")
    console.print(f"  {goal.description}")
    console.print(f"  Outcome: {outcome}")


# Purpose Management

purpose_app = typer.Typer(help="Manage life purpose")
app.add_typer(purpose_app, name="purpose")


@purpose_app.command("set")
def purpose_set(
    purpose: str = typer.Argument(..., help="Your life purpose statement"),
    user_id: str = typer.Option("default", "--user-id", "-u", help="User ID")
):
    """
    Set or update your life purpose.
    """
    user, state, _ = load_user_and_state(user_id)

    user.set_purpose(purpose)
    save_user_and_state(user, state)

    console.print()
    console.print(Panel.fit(
        f"[green]✓ Purpose set successfully![/green]\n\n"
        f"[yellow]{purpose}[/yellow]",
        title="Life Purpose",
        border_style="green"
    ))
    console.print()


@purpose_app.command("show")
def purpose_show(
    user_id: str = typer.Option("default", "--user-id", "-u", help="User ID")
):
    """
    Show current life purpose.
    """
    user, _, _ = load_user_and_state(user_id)

    console.print()
    if user.purpose_statement:
        console.print(Panel(
            f"[yellow]{user.purpose_statement}[/yellow]",
            title="Your Life Purpose",
            border_style="cyan"
        ))
    else:
        console.print("[yellow]Purpose not set. Use 'alter purpose set' to define it.[/yellow]")
    console.print()


# Constitution Management

constitution_app = typer.Typer(help="Manage constitution")
app.add_typer(constitution_app, name="constitution")


@constitution_app.command("show")
def constitution_show():
    """
    Show current constitution principles.
    """
    constitution = Constitution.load()

    console.print()
    console.print(Panel.fit(
        f"Version: {constitution.version}\n"
        f"Type: {constitution.constitution_type}",
        title="Constitution",
        border_style="cyan"
    ))
    console.print()

    table = Table(title="Core Principles", box=box.ROUNDED)
    table.add_column("Principle", style="cyan", width=20)
    table.add_column("Weight", style="yellow", width=8)
    table.add_column("Rules", style="white")

    for principle in constitution.core_principles:
        rules_text = "\n".join(f"• {rule}" for rule in principle.rules[:3])
        if len(principle.rules) > 3:
            rules_text += f"\n... and {len(principle.rules) - 3} more"

        table.add_row(
            principle.name,
            str(principle.weight),
            rules_text
        )

    console.print(table)
    console.print()


@constitution_app.command("validate")
def constitution_validate(
    file_path: str = typer.Argument(..., help="Path to constitution YAML file")
):
    """
    Validate a custom constitution file.
    """
    try:
        constitution = Constitution.load(Path(file_path))
        console.print(f"[green]✓ Constitution is valid![/green]")
        console.print(f"  Version: {constitution.version}")
        console.print(f"  Principles: {len(constitution.core_principles)}")
        console.print(f"  Life Domains: {len(constitution.life_domains)}")
    except Exception as e:
        console.print(f"[red]✗ Constitution validation failed:[/red]")
        console.print(f"  {str(e)}")
        raise typer.Exit(1)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    reload: bool = typer.Option(False, help="Auto-reload on code changes"),
    consciousness: bool = typer.Option(True, "--consciousness/--no-consciousness", "-c", help="Enable consciousness engine (on by default)"),
    user_id: str = typer.Option("default", "--user-id", "-u", help="User ID for consciousness"),
    provider: str = typer.Option("anthropic", "--provider", help="LLM provider (anthropic, openai)"),
    model: Optional[str] = typer.Option(None, "--model", help="LLM model name"),
):
    """Start the ALTER web server with optional consciousness engine."""
    import os
    import uvicorn

    # Configure consciousness via environment variables (read by app lifespan)
    if consciousness:
        os.environ["ALTER_CONSCIOUSNESS"] = "1"
        os.environ["ALTER_USER_ID"] = user_id
        os.environ["ALTER_LLM_PROVIDER"] = provider
        if model:
            os.environ["ALTER_LLM_MODEL"] = model

    consciousness_info = ""
    if consciousness:
        consciousness_info = (
            f"\n[bold green]Consciousness: ON[/bold green]\n"
            f"User: [cyan]{user_id}[/cyan] | Provider: [cyan]{provider}[/cyan]"
            f"{f' | Model: [cyan]{model}[/cyan]' if model else ''}"
        )
    else:
        consciousness_info = "\nConsciousness: [dim]OFF (use -c to enable)[/dim]"

    console.print(Panel(
        f"[bold]ALTER Web Server[/bold]\n"
        f"Running at [cyan]http://localhost:{port}[/cyan]\n"
        f"API docs at [cyan]http://localhost:{port}/docs[/cyan]"
        f"{consciousness_info}",
        title="ALTER",
        border_style="green"
    ))
    uvicorn.run(
        "alter.api.app:app",
        host=host,
        port=port,
        reload=reload,
    )


# Entry point
if __name__ == "__main__":
    app()
