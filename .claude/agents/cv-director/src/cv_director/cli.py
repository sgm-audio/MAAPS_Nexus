"""
Command-line interface for CV Director
"""

import sys
import typer
from rich.console import Console
from rich.table import Table
from typing import List, Optional
from loguru import logger

# Initialize Typer app and Rich console
app = typer.Typer(
    name="cv-director",
    help="Semantic Multi-Camera Switching with Computer Vision",
    add_completion=False,
)
console = Console()


@app.command()
def direct(
    cameras: List[str] = typer.Argument(
        ...,
        help="Camera sources (RTSP URLs, device indices, or video files)",
    ),
    audio_device: str = typer.Option(
        "default",
        "--audio",
        "-a",
        help="Audio input device name or index",
    ),
    profile: str = typer.Option(
        "Dynamic_Podcast",
        "--profile",
        "-p",
        help="Director profile (Dynamic_Podcast, Static_Interview)",
    ),
    obs_host: str = typer.Option(
        "localhost",
        "--obs-host",
        help="OBS WebSocket host",
    ),
    obs_port: int = typer.Option(
        4455,
        "--obs-port",
        help="OBS WebSocket port",
    ),
    obs_password: Optional[str] = typer.Option(
        None,
        "--obs-password",
        help="OBS WebSocket password",
    ),
    visualization: bool = typer.Option(
        False,
        "--viz",
        "-v",
        help="Show debug visualization window",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose logging (DEBUG level)",
    ),
):
    """
    Start the CV Director to automatically switch between cameras

    Examples:

        # Run with 3 RTSP cameras
        cv-director direct rtsp://cam1 rtsp://cam2 rtsp://cam3

        # Run with USB cameras
        cv-director direct 0 1 2 --profile Static_Interview

        # With visualization and verbose logging
        cv-director direct 0 1 2 --viz --verbose
    """
    # Configure logging
    log_level = "DEBUG" if verbose else "INFO"
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=log_level,
    )

    console.print("\n[bold cyan]CV Director - Semantic Multi-Camera Switching[/bold cyan]\n")

    # Display configuration
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Cameras", f"{len(cameras)} cameras")
    for i, cam in enumerate(cameras):
        table.add_row(f"  Camera {i}", cam)
    table.add_row("Audio Device", audio_device)
    table.add_row("Profile", profile)
    table.add_row("OBS Host", f"{obs_host}:{obs_port}")
    table.add_row("Visualization", "Enabled" if visualization else "Disabled")
    table.add_row("Verbose", "Enabled" if verbose else "Disabled")

    console.print(table)
    console.print()

    try:
        # Import here to provide clear error if not implemented
        from .director_main import CVDirector

        logger.info("Initializing CV Director...")
        director = CVDirector(
            camera_sources=cameras,
            audio_device=audio_device,
            profile=profile,
            obs_host=obs_host,
            obs_port=obs_port,
            obs_password=obs_password,
            visualization=visualization,
        )

        logger.info("Starting director pipeline...")
        import asyncio
        asyncio.run(director.start())

    except ImportError:
        console.print("[bold red]Error:[/bold red] CVDirector not yet implemented")
        console.print("[yellow]The director_main.py module needs to be created[/yellow]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping CV Director...[/yellow]")
        logger.info("Received keyboard interrupt, shutting down")
    except Exception as e:
        console.print(f"\n[bold red]Error during processing:[/bold red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def profiles():
    """
    List all available director profiles with their settings
    """
    console.print("\n[bold cyan]Available Director Profiles[/bold cyan]\n")

    try:
        from .profiles import list_profiles, get_profile

        profile_names = list_profiles()

        for name in profile_names:
            profile = get_profile(name)

            table = Table(title=f"[bold]{profile.name}[/bold]")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Description", profile.description)
            table.add_row("", "")
            table.add_row("[bold]Detection[/bold]", "")
            table.add_row("  Audio Weight", f"{profile.detector.audio_weight:.2f}")
            table.add_row("  Visual Weight", f"{profile.detector.visual_weight:.2f}")
            table.add_row("  VAD Aggressiveness", str(profile.detector.vad_aggressiveness))
            table.add_row("", "")
            table.add_row("[bold]Switching Rules[/bold]", "")
            table.add_row("  Min Dwell Time", f"{profile.rules.min_dwell_time:.1f}s")
            table.add_row("  Max Dwell Time", f"{profile.rules.max_dwell_time:.1f}s")
            table.add_row("  Switch Threshold", f"{profile.rules.switch_threshold:.2f}")
            table.add_row("  Hysteresis", f"{profile.rules.hysteresis:.2f}")
            table.add_row("  Variety Bonus", f"{profile.rules.variety_bonus:.2f}")

            console.print(table)
            console.print()

    except ImportError:
        console.print("[bold red]Error:[/bold red] Profiles module not yet implemented")
        console.print("[yellow]The profiles.py module needs to be created[/yellow]")
        raise typer.Exit(1)


@app.command()
def info():
    """
    Show system information (OpenCV, MediaPipe, GPU availability)
    """
    console.print("\n[bold cyan]CV Director System Information[/bold cyan]\n")

    table = Table()
    table.add_column("Component", style="cyan")
    table.add_column("Version/Status", style="green")

    # Python version
    import platform
    table.add_row("Python", platform.python_version())

    # OpenCV
    try:
        import cv2
        table.add_row("OpenCV", cv2.__version__)
    except ImportError:
        table.add_row("OpenCV", "[red]Not installed[/red]")

    # MediaPipe
    try:
        import mediapipe as mp
        table.add_row("MediaPipe", mp.__version__)
    except ImportError:
        table.add_row("MediaPipe", "[red]Not installed[/red]")

    # webrtcvad
    try:
        import webrtcvad
        table.add_row("webrtcvad", "Installed")
    except ImportError:
        table.add_row("webrtcvad", "[red]Not installed[/red]")

    # OBS WebSocket
    try:
        import obswebsocket
        version = getattr(obswebsocket, '__version__', 'Installed')
        table.add_row("obs-websocket-py", version)
    except ImportError:
        table.add_row("obs-websocket-py", "[red]Not installed[/red]")

    # CUDA availability (if applicable)
    try:
        import cv2
        cuda_available = cv2.cuda.getCudaEnabledDeviceCount() > 0
        if cuda_available:
            table.add_row("CUDA", f"[green]Available ({cv2.cuda.getCudaEnabledDeviceCount()} devices)[/green]")
        else:
            table.add_row("CUDA", "[yellow]Not available (CPU only)[/yellow]")
    except:
        table.add_row("CUDA", "[yellow]Not available (CPU only)[/yellow]")

    console.print(table)
    console.print()


if __name__ == "__main__":
    app()
