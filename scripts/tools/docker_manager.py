#!/usr/bin/env python3
import docker
import sys
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

# Initialize Rich console with custom theme
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "success": "green",
    "title": "blue",
    "header": "cyan",
    "data": "white"
})

console = Console(theme=custom_theme)

class DockerContainerManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            console.print(f"[error]Error connecting to Docker daemon: {e}[/]")
            sys.exit(1)

    def list_containers(self):
        """List all running containers with numbered indices."""
        containers = self.client.containers.list()
        if not containers:
            console.print("[warning]No running containers found.[/]")
            return None

        table = Table(show_header=True, header_style="header")
        table.add_column("Index", style="info", justify="right")
        table.add_column("Name", style="success")
        table.add_column("Image", style="info")
        table.add_column("Status", style="warning")
        table.add_column("ID", style="data")

        for idx, container in enumerate(containers, 1):
            name = container.name
            image = container.image.tags[0] if container.image.tags else "None"
            status = container.status
            container_id = container.short_id
            table.add_row(str(idx), name, image, status, container_id)

        console.print("\n")
        console.print(table)
        console.print("\n")
        return containers

    def container_actions(self, container):
        """Display and handle actions for a selected container."""
        actions = {
            1: ("Stop Container", container.stop),
            2: ("Restart Container", container.restart),
            3: ("Show Logs", lambda: console.print(container.logs().decode())),
            4: ("Show Stats", self.show_stats),
            5: ("Execute Command", self.execute_command),
            6: ("Show Container Info", self.show_container_info),
            7: ("Back to Container List", lambda: None)
        }

        while True:
            console.print(Panel(
                f"Container: {container.name}",
                style="title"
            ))
            
            for num, (action, _) in actions.items():
                console.print(f"[info]{num}.[/] [data]{action}[/]")

           try:
                choice = input("\nSelect action (1-7): ")
                if not choice.strip():
                    continue
                    
                choice = int(choice)
                if choice not in actions:
                    console.print("[error]Invalid choice. Please try again.[/]")
                    continue

                if choice == 7:
                    break

                action_name, action_func = actions[choice]
                if choice in [4, 5]:
                    action_func(container)
                else:
                    action_func()
                    console.print(f"[success]\n{action_name} completed successfully.[/]")

            except ValueError:
                console.print("[error]Please enter a valid number.[/]")
            except docker.errors.APIError as e:
                console.print(f"[error]Docker API Error: {e}[/]")
            except Exception as e:
                console.print(f"[error]Error: {e}[/]")

            input("\nPress Enter to continue...")
            os.system('clear')

    def show_stats(self, container):
        """Display container resource usage statistics."""
        stats = container.stats(stream=False)
        
        # CPU usage calculation
        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                   stats["precpu_stats"]["cpu_usage"]["total_usage"]
        system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                      stats["precpu_stats"]["system_cpu_usage"]
        cpu_percent = (cpu_delta / system_delta) * 100 * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"])

        # Memory usage calculation
        memory_usage = stats["memory_stats"]["usage"] / (1024 * 1024)  # Convert to MB
        memory_limit = stats["memory_stats"]["limit"] / (1024 * 1024)  # Convert to MB
        memory_percent = (memory_usage / memory_limit) * 100

        # Network calculations
        rx_bytes = stats['networks']['eth0']['rx_bytes']
        tx_bytes = stats['networks']['eth0']['tx_bytes']

        table = Table(show_header=True, header_style="header", title="Container Statistics")
        table.add_column("Metric", style="info")
        table.add_column("Value", style="data")

        table.add_row("CPU Usage", f"{cpu_percent:.2f}%")
        table.add_row(
            "Memory Usage", 
            f"{memory_usage:.1f}MB / {memory_limit:.1f}MB ({memory_percent:.1f}%)"
        )
        table.add_row(
            "Network I/O", 
            f"↓ {self._format_bytes(rx_bytes)} ↑ {self._format_bytes(tx_bytes)}"
        )

        console.print("\n")
        console.print(table)
        console.print("\n")

    def execute_command(self, container):
        """Execute a command inside the container."""
        command = input("\nEnter command to execute: ")
        try:
            exit_code, output = container.exec_run(command)
            console.print(Panel(
                output.decode(),
                title=f"Command output (exit code {exit_code})",
                style="title"
            ))
        except docker.errors.APIError as e:
            console.print(f"[error]Error executing command: {e}[/]")

    def show_container_info(self, container):
        """Display detailed container information."""
        info = container.attrs
        
        table = Table(show_header=True, header_style="header", title="Container Information")
        table.add_column("Property", style="info")
        table.add_column("Value", style="data")

        table.add_row("ID", info['Id'][:12])
        table.add_row("Name", info['Name'].lstrip('/'))
        table.add_row("Image", info['Config']['Image'])
        table.add_row("Status", info['State']['Status'])
        table.add_row("Created", str(datetime.fromtimestamp(info['Created'])))
        table.add_row("IP Address", info['NetworkSettings']['IPAddress'])

        console.print("\n")
        console.print(table)

        # Show ports in a separate table if there are any port bindings
        port_bindings = info['HostConfig']['PortBindings']
        if port_bindings:
            port_table = Table(
                show_header=True, 
                header_style="header", 
                title="Port Mappings"
            )
            port_table.add_column("Container Port", style="info")
            port_table.add_column("Host Port", style="data")

            for port, bindings in port_bindings.items():
                if bindings:
                    port_table.add_row(port, bindings[0]['HostPort'])

            console.print("\n")
            console.print(port_table)
        console.print("\n")

    @staticmethod
    def _format_bytes(bytes_value):
        """Format bytes into human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024:
                return f"{bytes_value:.2f}{unit}"
            bytes_value /= 1024
        return f"{bytes_value:.2f}TB"

def main():
    manager = DockerContainerManager()
    
    while True:
        os.system('clear')
        console.print("[title]Docker Container Manager[/]")
        console.print("=" * 40)
        
        containers = manager.list_containers()
        if not containers:
            if input("\nPress Enter to refresh or 'q' to quit: ").lower() == 'q':
                break
            continue

        try:
            choice = input("\nSelect container number (or 'q' to quit): ")
            if choice.lower() == 'q':
                break

            container_index = int(choice) - 1
            if 0 <= container_index < len(containers):
                manager.container_actions(containers[container_index])
            else:
                console.print("[error]Invalid container number. Please try again.[/]")
                input("\nPress Enter to continue...")
        except ValueError:
            console.print("[error]Please enter a valid number.[/]")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
