from typing import List
import google.ai.generativelanguage as glm

def read_todo_list(file_path: str = "/MyProject/Han-Agent/han_workspace/todo.md") -> str:
    """Reads the content of the todo.md file.

    Args:
        file_path: The absolute path to the todo.md file.

    Returns:
        The content of the todo.md file.
    """
    try:
        with open(file_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "todo.md not found."

def add_todo_item(item: str, file_path: str = "/MyProject/Han-Agent/han_workspace/todo.md"):
    """Adds a new item to the todo.md file.

    Args:
        item: The todo item to add.
        file_path: The absolute path to the todo.md file.
    """
    with open(file_path, "a") as f:
        f.write(f"- [ ] {item}\n")
    return f"Added: {item}"

def mark_todo_item_done(item_index: int, file_path: str = "/MyProject/Han-Agent/han_workspace/todo.md"):
    """Marks a todo item as done in the todo.md file.

    Args:
        item_index: The 1-based index of the todo item to mark as done.
        file_path: The absolute path to the todo.md file.
    """
    with open(file_path, "r") as f:
        lines = f.readlines()

    if 0 < item_index <= len(lines):
        line = lines[item_index - 1]
        if line.strip().startswith("- [ ]"):
            lines[item_index - 1] = line.replace("- [ ]", "- [x]", 1)
            with open(file_path, "w") as f:
                f.writelines(lines)
            return f"Marked item {item_index} as done."
        else:
            return f"Item {item_index} is not an uncompleted todo item."
    else:
        return f"Invalid item index: {item_index}"

todo_manager_tool_definitions = glm.Tool(
    function_declarations=[
        glm.FunctionDeclaration(
            name="read_todo_list",
            description="Reads the content of the todo.md file.",
            parameters=glm.Schema(
                type=glm.Type.OBJECT,
                properties={
                    "file_path": glm.Schema(type=glm.Type.STRING, description="The absolute path to the todo.md file.")
                },
                required=[],
            ),
        ),
        glm.FunctionDeclaration(
            name="add_todo_item",
            description="Adds a new item to the todo.md file.",
            parameters=glm.Schema(
                type=glm.Type.OBJECT,
                properties={
                    "item": glm.Schema(type=glm.Type.STRING, description="The todo item to add."),
                    "file_path": glm.Schema(type=glm.Type.STRING, description="The absolute path to the todo.md file.")
                },
                required=["item"],
            ),
        ),
        glm.FunctionDeclaration(
            name="mark_todo_item_done",
            description="Marks a todo item as done in the todo.md file.",
            parameters=glm.Schema(
                type=glm.Type.OBJECT,
                properties={
                    "item_index": glm.Schema(type=glm.Type.INTEGER, description="The 1-based index of the todo item to mark as done."),
                    "file_path": glm.Schema(type=glm.Type.STRING, description="The absolute path to the todo.md file.")
                },
                required=["item_index"],
            ),
        ),
    ]
)

todo_manager_functions = {
    "read_todo_list": read_todo_list,
    "add_todo_item": add_todo_item,
    "mark_todo_item_done": mark_todo_item_done,
}