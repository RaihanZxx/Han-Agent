<div align="center">
  <h1>HanAgent v2.3.0</h1>
  <p><strong>Your Autonomous AI Pair Programmer, Right in Your Terminal.</strong></p>
  <p>Powered by Google's Gemini Pro, HanAgent is designed to tackle complex coding tasks, debug issues, and manage file systems through an iterative, self-correcting loop.</p>
  
  <p>
    <a href="https://github.com/RaihanZxx/Han-Agent/blob/main/LICENSE"><img src="https://img.shields.io/github/license/RaihanZxx/Han-Agent?style=for-the-badge&color=blue" alt="License"></a>
    <img src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python" alt="Python Version">
    <img src="https://img.shields.io/badge/Powered%20by-Gemini-blueviolet?style=for-the-badge&logo=google" alt="Powered by Gemini">
  </p>
</div>

> HanAgent isn't just a chatbot. It's a digital collaborator that lives in your workspace. It understands your goals, breaks them down into actionable steps, interacts with your files, executes commands, and learns from the results. If it hits an error, it tries to fix it. If it succeeds, it moves on.

---

## ✨ Key Capabilities

*   **Autonomous Planning**: Creates detailed, step-by-step plans before executing a task.
*   **Full Filesystem Access**: Can create, read, write, and manage files and directories within its secure workspace.
*   **Command Execution**: Runs shell commands (`python`, `git`, `javac`, `gradle`, etc.) to build, test, and run code.
*   **Self-Correction**: Analyzes `stdout` and `stderr` from commands to debug and retry on failure.
*   **Modular Knowledge**: Easily extend its expertise by adding simple `.txt` instruction files in the `prompt/` directory.
*   **Interactive Loop**: You can watch it work, and it will ask for clarification if it gets stuck.

---

## 🖼️ Previews

# Below are some previews of Compound Interest in action:
**Main Menu:**

<img src="https://github.com/RaihanZxx/Han-Agent/blob/main/previews%2Fpreviews1.png" width="400">

**Created Module KernelSU:**

<img src="https://github.com/RaihanZxx/Han-Agent/blob/main/previews%2Fpreviews2.png" width="400">

---

### 🚀 Quick Start

Get HanAgent running in under 2 minutes.

**1. Clone the repository:**
```bash
git clone https://github.com/RaihanZxx/Han-Agent.git
cd Han-Agent
```



**2. Set up your environment:**
install dependency
```bash
apt install python3 python3-pip python3-venv
```

Buat dan aktifkan virtual environment (direkomendasikan)
```bash
python3 -m venv venv
source venv/bin/activate
```

Install pip
```bash
pip install -r requirements.txt
```

**3. Configure your API Key:**
Dapatkan API Key dari Google AI Studio Free: https://aistudio.google.com/app/apikey
Tambahkan kunci API Anda Buka file .env dan masukkan kunci Anda.

**4. Run the Agent!**
```bash
python main.py
```

Sekarang Anda bisa mulai memberikan tugas kepada HanAgent!

---

## 🧠 The Core Loop: Plan, Execute, Reflect

HanAgent operates on a continuous feedback loop:

1️⃣ Plan: Analyzes the user's request. If it's a task requiring tools, it generates a detailed, step-by-step plan.

2️⃣ Execute: It takes the first step of its plan and calls the necessary tool (e.g., write_file or execute_command).

3️⃣ Reflect & Debug: It carefully examines the output of the tool. Was there an error? Is the output what was expected? Based on this reflection, it decides whether to try a different approach, modify its plan, or continue to the next step.

🔁 Iterate: The loop continues until the task is marked TUGAS SELESAI or it requires human intervention.

🔧 Extending the Agent's Knowledge

HanAgent's power comes from its modular prompts. You can teach it new skills without changing any code.

Simply add a new .txt file to the prompt/ directory. For example, to make the agent an expert in deploying with Docker, you could create _docker_guide.txt with your specific instructions and best practices. The agent will automatically load and incorporate this knowledge into its "brain" on the next run.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m 'Add YourFeature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a pull request.

---

## 📬 Contact

For questions or feedback, reach out via GitHub Issues or contact the maintainer at:
- <img src="https://img.shields.io/badge/Telegram-%40HanSoBored-0088cc?style=flat-square&logo=telegram" alt="Telegram" height="20">
- <img src="https://img.shields.io/badge/Email-raihanzxzy%40gmail.com-d14836?style=flat-square&logo=gmail" alt="Email" height="20">

---