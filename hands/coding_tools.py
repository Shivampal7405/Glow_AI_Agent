"""
Coding Tools - Project creation and code generation
"""

import os
import subprocess
from pathlib import Path
from typing import Optional


def create_project(name: str, project_type: str = "python", location: Optional[str] = None) -> str:
    """
    Create a new project with proper structure

    Args:
        name: Project name
        project_type: Type of project (python, node, react, etc.)
        location: Optional location (defaults to Documents)

    Returns:
        Status message
    """
    try:
        if location is None:
            location = str(Path.home() / "Documents" / "Projects")

        project_path = os.path.join(location, name)

        # Create base directory
        os.makedirs(project_path, exist_ok=True)

        if project_type.lower() == "python":
            # Create Python project structure
            os.makedirs(os.path.join(project_path, "src"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "tests"), exist_ok=True)

            # Create basic files
            with open(os.path.join(project_path, "README.md"), "w") as f:
                f.write(f"# {name}\n\nA Python project.\n")

            with open(os.path.join(project_path, "requirements.txt"), "w") as f:
                f.write("# Project dependencies\n")

            with open(os.path.join(project_path, "src", "__init__.py"), "w") as f:
                f.write("")

            with open(os.path.join(project_path, "src", "main.py"), "w") as f:
                f.write('def main():\n    print("Hello, World!")\n\nif __name__ == "__main__":\n    main()\n')

        elif project_type.lower() in ["node", "javascript", "js"]:
            # Initialize npm project
            subprocess.run(
                ["npm", "init", "-y"],
                cwd=project_path,
                shell=True,
                capture_output=True
            )

            # Create basic structure
            os.makedirs(os.path.join(project_path, "src"), exist_ok=True)

            with open(os.path.join(project_path, "src", "index.js"), "w") as f:
                f.write('console.log("Hello, World!");\n')

        elif project_type.lower() in ["react", "reactjs"]:
            # Use create-react-app
            subprocess.run(
                ["npx", "create-react-app", name],
                cwd=location,
                shell=True
            )
            return f"Created React project at {project_path}"

        else:
            # Generic project
            with open(os.path.join(project_path, "README.md"), "w") as f:
                f.write(f"# {name}\n\nProject created by GLOW.\n")

        return f"Successfully created {project_type} project at {project_path}"

    except Exception as e:
        return f"Error creating project: {str(e)}"


def write_file(file_path: str = None, filename: str = None, content: str = "", append: bool = False, **kwargs) -> str:
    """
    Write content to a file

    Args:
        file_path: Path to the file
        filename: Alias for file_path
        content: Content to write
        append: Whether to append (True) or overwrite (False)

    Returns:
        Status message
    """
    try:
        # Handle aliases
        target_path = file_path or filename or kwargs.get('path')
        if not target_path:
            return "Error: file_path or filename required"

        # Create parent directories if needed
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)

        mode = "a" if append else "w"
        with open(target_path, mode) as f:
            f.write(content)

        action = "Appended to" if append else "Wrote"
        return f"{action} file: {target_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def read_file(file_path: str) -> str:
    """
    Read content from a file

    Args:
        file_path: Path to the file

    Returns:
        File content or error message
    """
    try:
        with open(file_path, "r") as f:
            content = f.read()
        return f"Content of {file_path}:\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


def open_in_vscode(path: str = None, **kwargs) -> str:
    """
    Open a file or folder in VS Code

    Args:
        path: Path to file or folder

    Returns:
        Status message
    """
    try:
        # Handle aliases
        target_path = path or kwargs.get('file_path') or kwargs.get('folder_path')
        if not target_path:
            return "Error: path required"

        subprocess.Popen(["code", target_path], shell=True)
        return f"Opened in VS Code: {target_path}"
    except Exception as e:
        return f"Error opening in VS Code: {str(e)}"


def run_python_script(script_path: str, args: Optional[str] = None) -> str:
    """
    Run a Python script

    Args:
        script_path: Path to the Python script
        args: Optional command-line arguments

    Returns:
        Script output or error message
    """
    try:
        cmd = ["python", script_path]
        if args:
            cmd.extend(args.split())

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        output = f"Exit code: {result.returncode}\n\n"
        output += f"STDOUT:\n{result.stdout}\n\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}"

        return output
    except subprocess.TimeoutExpired:
        return "Script execution timed out (30s limit)"
    except Exception as e:
        return f"Error running script: {str(e)}"


def install_package(package_name: str, package_manager: str = "pip") -> str:
    """
    Install a package using pip or npm

    Args:
        package_name: Name of the package
        package_manager: 'pip' or 'npm'

    Returns:
        Status message
    """
    try:
        if package_manager.lower() == "pip":
            cmd = ["pip", "install", package_name]
        elif package_manager.lower() == "npm":
            cmd = ["npm", "install", package_name]
        else:
            return f"Unknown package manager: {package_manager}"

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            return f"Successfully installed {package_name} using {package_manager}"
        else:
            return f"Error installing {package_name}:\n{result.stderr}"

    except Exception as e:
        return f"Error installing package: {str(e)}"


def create_snake_game(folder_path: str) -> str:
    """
    Create a complete snake game in Python

    Args:
        folder_path: Path to create the game in

    Returns:
        Status message
    """
    snake_code = '''import pygame
import random

# Initialize Pygame
pygame.init()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Screen dimensions
WIDTH = 600
HEIGHT = 400
CELL_SIZE = 20

# Create screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game - GLOW")

# Clock
clock = pygame.time.Clock()

class Snake:
    def __init__(self):
        self.positions = [(WIDTH // 2, HEIGHT // 2)]
        self.direction = (CELL_SIZE, 0)
        self.grow = False

    def move(self):
        head_x, head_y = self.positions[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        self.positions.insert(0, new_head)
        if not self.grow:
            self.positions.pop()
        else:
            self.grow = False

    def change_direction(self, direction):
        # Prevent reversing
        if (direction[0] * -1, direction[1] * -1) != self.direction:
            self.direction = direction

    def check_collision(self):
        head = self.positions[0]
        # Wall collision
        if (head[0] < 0 or head[0] >= WIDTH or
            head[1] < 0 or head[1] >= HEIGHT):
            return True
        # Self collision
        if head in self.positions[1:]:
            return True
        return False

    def draw(self):
        for pos in self.positions:
            pygame.draw.rect(screen, GREEN, (*pos, CELL_SIZE, CELL_SIZE))

class Food:
    def __init__(self):
        self.position = self.random_position()

    def random_position(self):
        x = random.randint(0, (WIDTH - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
        y = random.randint(0, (HEIGHT - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
        return (x, y)

    def draw(self):
        pygame.draw.rect(screen, RED, (*self.position, CELL_SIZE, CELL_SIZE))

def main():
    snake = Snake()
    food = Food()
    score = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    snake.change_direction((0, -CELL_SIZE))
                elif event.key == pygame.K_DOWN:
                    snake.change_direction((0, CELL_SIZE))
                elif event.key == pygame.K_LEFT:
                    snake.change_direction((-CELL_SIZE, 0))
                elif event.key == pygame.K_RIGHT:
                    snake.change_direction((CELL_SIZE, 0))

        snake.move()

        # Check food collision
        if snake.positions[0] == food.position:
            snake.grow = True
            food.position = food.random_position()
            score += 10

        # Check game over
        if snake.check_collision():
            print(f"Game Over! Score: {score}")
            running = False

        # Draw everything
        screen.fill(BLACK)
        snake.draw()
        food.draw()

        # Draw score
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(10)

    pygame.quit()

if __name__ == "__main__":
    main()
'''

    try:
        os.makedirs(folder_path, exist_ok=True)
        game_path = os.path.join(folder_path, "snake_game.py")

        with open(game_path, "w") as f:
            f.write(snake_code)

        # Also create a requirements file
        req_path = os.path.join(folder_path, "requirements.txt")
        with open(req_path, "w") as f:
            f.write("pygame>=2.5.0\n")

        return f"Created snake game at {game_path}. Install pygame with: pip install pygame"
    except Exception as e:
        return f"Error creating snake game: {str(e)}"


if __name__ == "__main__":
    # Test coding tools
    print(create_project("TestProject", "python"))
