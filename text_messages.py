import subprocess
import time
from datetime import datetime
import re
import os
import tempfile
import argparse

# Configuration
SESSION = "ollama-agents"
PANE_MAN = "0.0"
PANE_WOMAN = "0.1"
LINES = 300
PROMPT_MARKER = ">>> Send a message"
THINK_END_MARKER = "</think>"

# Command line arguments
parser = argparse.ArgumentParser(description="Run a text message conversation simulation between two AI agents.")
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
args = None  # Will be initialized in main()

# Personalities will be formatted with the user's chosen scenario
ROLE_MAN_TEMPLATE = (
    "Role-play this scenario: {scenario}."
    "IMPORTANT: Keep your message around 2-4 SENTENCES. Be conversational and casual. Use more daily vocabulary and slangs. "
    "Prepend a \"👨 Him:\" prefix to the full message before sending it"
    "Use emojis to express your emotions and feelings."
    "CRITICAL: ONLY output the exact words you are saying with NO PUNCTUATION AT ALL. Do NOT include any narration, description, formatting, character names, "
    "or dialogue tags. Don't use asterisks, quotes, periods, commas or any other formatting or punctuation. Just output plain text as if you're speaking. "
    "FIRST MESSAGE: You should start the conversation in a way that relates to the scenario."
    
)

ROLE_WOMAN_TEMPLATE = (
    "Role-play this scenario: {scenario}."
    "First, wait for the man to start the conversation. "
    "IMPORTANT: Keep your message around 2-4 SENTENCES. Be conversational and casual. Use more daily vocabulary and slangs. "
    "Prepend a \"👩 Her:\" prefix to the full message before sending it"
    "Use emojis to express your emotions and feelings."
    "CRITICAL: ONLY output the exact words you are saying with NO PUNCTUATION AT ALL. Do NOT include any narration, description, formatting, character names, "
    "or dialogue tags. Don't use asterisks, quotes, periods, commas or any other formatting or punctuation. Just output plain text as if you're speaking."
)

# State
last_sender = "M"  # M for Man, W for Woman
last_response = ""
topic = ""  # Will be set based on user input

def print_colored(text, color="green"):
    """
    Print text with ANSI color codes.
    
    Args:
        text (str): The text to print.
        color (str): Color name (red, green, yellow, blue, etc.)
    """
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "grey": "\033[90m",  # Light grey
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")

def log(msg, color=None, force_show=False):
    """
    Log a message with a timestamp.
    
    Args:
        msg (str): The message to log.
        color (str, optional): Color to use for the message.
        force_show (bool, optional): Show the message even when verbose mode is off.
    """
    global args
    if not args or args.verbose or force_show:
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        if color:
            print_colored(f"{timestamp} {msg}", color)
        else:
            print(f"{timestamp} {msg}")

def tmux_session_exists(name: str) -> bool:
    """
    Check if a tmux session with the given name exists.
    
    Args:
        name (str): The name of the tmux session.
        
    Returns:
        bool: True if the session exists, False otherwise.
    """
    return subprocess.run(["tmux", "has-session", "-t", name],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

def bootstrap_tmux(force=False):
    """
    Bootstrap a tmux session with panes for multiple Ollama models.
    
    This function creates a new tmux session with two panes in a horizontal split
    (one above the other), each running Gemma but with different personalities.
    
    Args:
        force (bool, optional): If True, kill any existing session with the same name.
                               If False, skip bootstrap if session exists. Defaults to False.
    """
    if tmux_session_exists(SESSION):
        if force:
            subprocess.run(["tmux", "kill-session", "-t", SESSION])
        else:
            log(f"⚠️ Session '{SESSION}' already exists. Skipping bootstrap.", "grey")
            return

    log("🛠️ Bootstrapping tmux session and launching models...", "grey")
    subprocess.run(["tmux", "new-session", "-d", "-s", SESSION])
    
    # Create horizontal split (top/bottom) instead of vertical (left/right)
    subprocess.run(["tmux", "split-window", "-v", "-t", SESSION])
    
    # Start Gemma in both panes with different roles
    subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.0", "ollama run gemma3:4b", "C-m"])
    subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:0.1", "ollama run gemma3:4b", "C-m"])
    log("✅ Models launched. Waiting 2 seconds for them to initialize...", "green")
    time.sleep(2)

def send_to_pane(pane: str, message: str):
    """
    Send a message to a tmux pane.
    
    Args:
        pane (str): The identifier of the tmux pane (e.g., "0.0").
        message (str): The message to send.
    """
    log(f"📤 Sending message (length: {len(message)})", "grey")
    
    # For very long or complex messages, fall back to the buffer method
    if len(message) > 1000 or '\n' in message:
        # Create a temporary file for the message
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
            temp_path = temp.name
            temp.write(message)
        
        try:
            # Use tmux load-buffer and paste-buffer for reliable sending of multiline content
            log(f"📤 Using buffer method for long/complex message", "grey")
            
            # Load the message into tmux buffer
            subprocess.run(["tmux", "load-buffer", temp_path], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Paste the buffer into the target pane
            subprocess.run(["tmux", "paste-buffer", "-t", f"{SESSION}:{pane}"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
    else:
        # Use send-keys with literal flag for simpler messages
        log(f"📤 Using direct send-keys for simple message", "grey")
        subprocess.run(["tmux", "send-keys", "-l", "-t", f"{SESSION}:{pane}", message],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Send an Enter key to submit the message
    subprocess.run(["tmux", "send-keys", "-t", f"{SESSION}:{pane}", "C-m"],
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_pane_output(pane: str) -> list[str]:
    """
    Get the current output of a tmux pane.
    
    Args:
        pane (str): The identifier of the tmux pane (e.g., "0.0").
        
    Returns:
        list[str]: The output as a list of lines.
    """
    result = subprocess.run(["tmux", "capture-pane", "-pt", f"{SESSION}:{pane}", "-S", f"-{LINES}"],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return result.stdout.strip().splitlines()

def count_prompts(lines: list[str]) -> int:
    """
    Count how many prompt markers appear in the given lines.
    
    Args:
        lines (list[str]): A list of text lines.
        
    Returns:
        int: The number of lines containing the prompt marker.
    """
    return sum(1 for line in lines if PROMPT_MARKER in line)

def wait_for_prompt(pane: str, base_prompt_count: int, settle_loops=3, sleep_secs=1.0) -> list[str]:
    """
    Wait for a new prompt to appear in a tmux pane.
    
    This function continuously checks the output of a tmux pane until a new prompt appears
    and the output stabilizes (stops changing).
    
    Args:
        pane (str): The identifier of the tmux pane (e.g., "0.0").
        base_prompt_count (int): The baseline number of prompts to compare against.
        settle_loops (int, optional): Number of consecutive stable checks required. Defaults to 3.
        sleep_secs (float, optional): Time to sleep between checks. Defaults to 1.0.
        
    Returns:
        list[str]: The stabilized output as a list of lines.
    """
    stable_count = 0
    last_output = []

    log(f"⏳ Waiting for new >>> prompt in pane {pane}...", "grey")

    while True:
        lines = get_pane_output(pane)
        current_prompt_count = count_prompts(lines)

        if current_prompt_count > base_prompt_count:
            if lines == last_output:
                stable_count += 1
                if stable_count >= settle_loops:
                    return lines
            else:
                stable_count = 0
                last_output = lines

        time.sleep(sleep_secs)

def extract_response(lines: list[str]) -> str:
    """
    Extract the model's response from tmux pane output.
    
    This function extracts the most recent response from the model,
    typically found before the prompt marker. The response is the content
    between the last two >>> markers.
    
    Args:
        lines (list[str]): The output lines from a tmux pane.
        
    Returns:
        str: The extracted response, or an empty string if no response could be extracted.
    """
    # Find the indices of prompt markers (lines containing ">>> Send a message")
    prompt_indices = [i for i, line in enumerate(lines) if PROMPT_MARKER in line]
    
    if not prompt_indices:
        return ""
    
    # Get the last prompt index
    last_prompt_idx = prompt_indices[-1]
    
    # Find all command markers (lines starting with ">>>")
    command_markers = [i for i in range(last_prompt_idx) if i > 0 and 
                      lines[i].strip().startswith(">>>")]
    
    # Filter out the prompt markers from command markers
    command_markers = [i for i in command_markers if PROMPT_MARKER not in lines[i]]
    
    if len(command_markers) < 1:
        # No command markers found, use beginning of visible text
        start_idx = 0
    else:
        # Get the most recent command marker before the prompt
        start_idx = max(marker for marker in command_markers if marker < last_prompt_idx) + 1
    
    # Extract lines between the last command marker and the prompt
    response_lines = lines[start_idx:last_prompt_idx]
    
    # Skip empty lines at the beginning
    while response_lines and not response_lines[0].strip():
        response_lines.pop(0)
    
    # Skip empty lines at the end
    while response_lines and not response_lines[-1].strip():
        response_lines.pop()
    
    # Process the lines to extract content after the prefixes and remove continuation markers
    cleaned_lines = []
    found_prefix = False
    actual_response = []
    
    # First, join all lines to handle cases where the prefix is split across lines
    full_text = " ".join([line.strip() for line in response_lines])
    
    # Look for the prefixes in the full text
    him_prefix_pos = full_text.find("👨 Him:")
    her_prefix_pos = full_text.find("👩 Her:")
    
    if him_prefix_pos >= 0:
        # Extract everything after "👨 Him:"
        extracted_text = full_text[him_prefix_pos + len("👨 Him:"):].strip()
        found_prefix = True
    elif her_prefix_pos >= 0:
        # Extract everything after "👩 Her:"
        extracted_text = full_text[her_prefix_pos + len("👩 Her:"):].strip()
        found_prefix = True
    
    if found_prefix:
        # Remove any continuation markers
        extracted_text = extracted_text.replace("...", " ")
        return extracted_text
    else:
        # Process the original response if no prefix is found
        for i, line in enumerate(response_lines):
            # Remove leading '...' that indicates line continuation in the terminal
            if line.strip().startswith("..."):
                line = line.replace("...", " ", 1).lstrip()
            cleaned_lines.append(line)
        
        # Join the remaining lines to form the response
        return "".join(cleaned_lines)

def relay_response(from_pane, to_pane, from_name, sender_flag):
    """
    Relay a response from one model to another.
    
    This function waits for a response from the source model, extracts it,
    logs it, and sends it to the target model.
    
    Args:
        from_pane (str): The source tmux pane identifier (e.g., "0.0").
        to_pane (str): The target tmux pane identifier (e.g., "0.1").
        from_name (str): A display name for the source model (for logging).
        sender_flag (str): The flag to set for last_sender after relaying.
    """
    global last_response, last_sender
    base_prompt_count = count_prompts(get_pane_output(from_pane))
    
    log(f"🔄 Waiting for response from {from_name} (current prompt count: {base_prompt_count})", "grey")
    lines = wait_for_prompt(from_pane, base_prompt_count)
    log(f"📝 Got {len(lines)} lines of output from {from_name}", "grey")
    
    response = extract_response(lines)
    
    if not response:
        log(f"⚠️ Could not extract response from {from_name}", "red")
        return
        
    if response == last_response:
        log(f"🔄 Duplicate response detected from {from_name}, skipping relay", "grey")
        return
    
    # Use colors appropriate for each agent
    color = "blue" if from_name.startswith("👨") else "green"
    log(f"{from_name} ➤", color, force_show=True)
    print_colored(response, color)
    print()  # Add an empty line for better readability
    
    # Log the exact content being sent for debugging
    log(f"📤 Sending to other agent (length: {len(response)}, lines: {response.count('\n')+1})", "grey")
    
    # Send the response as a single message
    send_to_pane(to_pane, response)
    last_response = response
    last_sender = sender_flag

def cleanup_tmux():
    """
    Kill the tmux session if it exists.
    """
    if tmux_session_exists(SESSION):
        log(f"🧹 Cleaning up tmux session '{SESSION}'...", "grey")
        subprocess.run(["tmux", "kill-session", "-t", SESSION], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        log(f"No tmux session '{SESSION}' to clean up.", "grey")

def main():
    """
    Main function to run the text message conversation conversation between two AI models.
    
    This function bootstraps the tmux session, initializes the models with their roles,
    and has the man agent initiate the conversation.
    """
    global last_sender, last_response, topic, args
    try:
        # Parse command-line arguments
        args = parser.parse_args()
        # Prompt the user for a scenario
        print_colored("Welcome to AI text message conversation Simulator!", "cyan")
        scenario = input("Enter a scenario for them to role-play (e.g., 'planning a first date', 'discussing weekend plans'): ").strip()
        if not scenario:
            scenario = "meeting for coffee after matching on a dating app"  # Default if nothing entered
            print_colored(f"No scenario provided, using default: {scenario}", "grey")
        else:
            print_colored(f"Starting a text message conversation with this scenario: {scenario}!", "green")
        # Format the role prompts with the chosen scenario
        ROLE_MAN = ROLE_MAN_TEMPLATE.format(scenario=scenario)
        ROLE_WOMAN = ROLE_WOMAN_TEMPLATE.format(scenario=scenario)
        bootstrap_tmux(force=False)
        log(f"💕 Setting up a text message conversation with scenario: {scenario}...", "grey")
        # Send role instructions to both agents
        send_to_pane(PANE_MAN, ROLE_MAN)
        send_to_pane(PANE_WOMAN, ROLE_WOMAN)
        time.sleep(5)
        # Wait for both models to be ready before starting the conversation
        log("⏳ Waiting for both personas to be ready...", "grey")
        # Wait for the man model to be ready
        log("⏳ Waiting for the man to be ready...", "grey")
        while True:
            lines = get_pane_output(PANE_MAN)
            if any(PROMPT_MARKER in line for line in lines):
                log("✅ Man is ready to start the conversation.", "grey")
                break
            time.sleep(1)
        # Wait for the woman model to be ready
        log("⏳ Waiting for the woman to be ready...", "grey")
        while True:
            lines = get_pane_output(PANE_WOMAN)
            if any(PROMPT_MARKER in line for line in lines):
                log("✅ Woman is ready to receive the conversation.", "grey")
                break
            time.sleep(1)
        log("📱 text message conversation is connecting...", "grey")
        # Have the man initiate the conversation naturally
        log(f"👨 Man is starting the conversation about {scenario}...", "grey")
        send_to_pane(PANE_MAN, f"Start the text message conversation about this scenario: {scenario}.")
        # Wait for the man's first message and send it to the woman
        relay_response(PANE_MAN, PANE_WOMAN, "👨 Him", "W")
        # Main conversation loop
        while True:
            try:
                if last_sender == "M":
                    relay_response(PANE_MAN, PANE_WOMAN, "👨 Him", "W")
                else:
                    relay_response(PANE_WOMAN, PANE_MAN, "👩 Her", "M")
            except KeyboardInterrupt:
                log("👋 text message conversation ended.", "grey")
                break
    finally:
        cleanup_tmux()

if __name__ == "__main__":
    main()
