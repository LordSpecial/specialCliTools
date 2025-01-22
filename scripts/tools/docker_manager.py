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
            4: ("Show Stats", lambda: self.show_stats(container)),
            5: ("Execute Command", lambda: self.execute_command(container)),
            6: ("Show Container Info", lambda: self.show_container_info(container)),
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
                action_func()

                if choice in [1, 2]:
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
        try:
            stats = container.stats(stream=False)

            table = Table(show_header=True, header_style="header", title="Container Statistics")
            table.add_column("Metric", style="info")
            table.add_column("Value", style="data")

            # CPU Usage calculation with safety checks
            try:
                cpu_stats = stats.get("cpu_stats", {})
                precpu_stats = stats.get("precpu_stats", {})

                cpu_usage = cpu_stats.get("cpu_usage", {})
                precpu_usage = precpu_stats.get("cpu_usage", {})

                cpu_delta = cpu_usage.get("total_usage", 0) - precpu_usage.get("total_usage", 0)
                system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get("system_cpu_usage", 0)

                # Get number of CPUs
                num_cpus = len(cpu_usage.get("percpu_usage", [])) if cpu_usage.get("percpu_usage") else 1

                if system_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * 100.0 * num_cpus
                else:
                    cpu_percent = 0.0

                table.add_row("CPU Usage", f"{cpu_percent:.2f}%")
            except Exception as e:
                table.add_row("CPU Usage", "N/A (Error calculating CPU usage)")

            # Memory Usage calculation with safety checks
            try:
                memory_stats = stats.get("memory_stats", {})
                memory_usage = memory_stats.get("usage", 0) / (1024 * 1024)  # Convert to MB
                memory_limit = memory_stats.get("limit", 0) / (1024 * 1024)  # Convert to MB

                if memory_limit > 0:
                    memory_percent = (memory_usage / memory_limit) * 100
                else:
                    memory_percent = 0.0

                table.add_row(
                    "Memory Usage",
                    f"{memory_usage:.1f}MB / {memory_limit:.1f}MB ({memory_percent:.1f}%)"
                )
            except Exception as e:
                table.add_row("Memory Usage", "N/A (Error calculating memory usage)")

            # Network calculations with safety checks
            try:
                networks = stats.get("networks", {})
                if "eth0" in networks:
                    rx_bytes = networks["eth0"].get("rx_bytes", 0)
                    tx_bytes = networks["eth0"].get("tx_bytes", 0)
                    table.add_row(
                        "Network I/O",
                        f"↓ {self._format_bytes(rx_bytes)} ↑ {self._format_bytes(tx_bytes)}"
                    )
                else:
                    # Try to get the first available network interface
                    first_interface = next(iter(networks.values()), {})
                    rx_bytes = first_interface.get("rx_bytes", 0)
                    tx_bytes = first_interface.get("tx_bytes", 0)
                    table.add_row(
                        "Network I/O",
                        f"↓ {self._format_bytes(rx_bytes)} ↑ {self._format_bytes(tx_bytes)}"
                    )
            except Exception as e:
                table.add_row("Network I/O", "N/A (Error calculating network I/O)")

            console.print("\n")
            console.print(table)
            console.print("\n")

        except Exception as e:
            console.print(f"[error]Error showing container stats: {str(e)}[/]")

            # Debug information
            console.print("[info]Available stats keys:[/]")
            try:
                console.print(", ".join(stats.keys()))
            except:
                console.print("[error]Could not access stats keys[/]")

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
        console.print("IS this working?")
        info = container.attrs
        
        table = Table(show_header=True, header_style="header", title="Container Information")
        table.add_column("Property", style="info")
        table.add_column("Value", style="data")

        table.add_row("ID", info['Id'][:12])
        table.add_row("Name", info['Name'].lstrip('/'))
        table.add_row("Image", info['Config']['Image'])
        table.add_row("Status", info['State']['Status'])
	# Handle created time safely
        created = info.get('Created')
        if created:
            try:
                # Handle string timestamp
                if isinstance(created, str):
                    created_time = datetime.fromisoformat(created.replace('Z', '+00:00'))
                # Handle integer timestamp
                else:
                    created_time = datetime.fromtimestamp(created)
                table.add_row("Created", created_time.strftime("%Y-%m-%d %H:%M:%S"))
            except (ValueError, TypeError):
                table.add_row("Created", "Invalid date format")
        else:
            table.add_row("Created", "N/A")

        # Handle IP address safely
        network_settings = info.get('NetworkSettings', {})
        ip_address = network_settings.get('IPAddress', '')
        if not ip_address and network_settings.get('Networks'):
            # Try to get IP from first network interface
            first_network = next(iter(network_settings['Networks'].values()))
            ip_address = first_network.get('IPAddress', 'N/A')
        table.add_row("IP Address", ip_address or 'N/A')

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
