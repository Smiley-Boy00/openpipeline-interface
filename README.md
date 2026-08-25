# 📦 OpenPipeline Interface

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Maya](https://img.shields.io/badge/Autodesk_Maya-Integration-37A5CC?logo=autodesk&logoColor=white)](https://www.autodesk.com/products/maya/)
[![Unreal Engine](https://img.shields.io/badge/Unreal_Engine-Integration-0E1128?logo=unrealengine&logoColor=white)](https://www.unrealengine.com/)
[![OpenUSD](https://img.shields.io/badge/OpenUSD-_Integration-4B8BBE)](https://openusd.org/)
[![Status](https://img.shields.io/badge/Status-Active_Development-orange)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()

> *The Python-based development interface for building and connecting DCC, pipeline, and production tools across Maya, Unreal Engine, OpenUSD, and other creative applications.*


## 🌟 Highlights

- Modular architecture for DCC and pipeline integrations.
- Cross-application tooling for Maya, Unreal Engine, and OpenUSD.
- Adaptable integration for additional software, APIs, and DCC applications.
- CLI-driven project and environment management.
- Reusable tools, packages and modules.
- Practical pipeline development patterns for solo and small-team workflows.


## ℹ️ Overview

A development interface for pipeline integration, designed to connect software, DCCs, and APIs through structured scripts and commands. </br>
OPI provides a sandbox for building, testing, and adapting custom development and production workflows.


## 🚀 Usage Examples

*Use commands for maya to interact with the interface scripts.
E.g. automatically create a maya .mod file:*

```bash
opi maya mod --make-mod ~/Developer/Pipeline/Maya/2026/modules
```
*Result:*
```bash
# ~/Developer/Pipeline/Maya/2026/modules/OPMaya.mod
+ OpenPipeline 0.1.0
PYTHONPATH +:= src
```



## ⬇️ Installation guide
### * Pre-requisites 
*Verify the list before installing/configuring OpenPipeline in your system.*</br>
Windows/Linux/MacOS:</br>
• Python >= 3.13 </br>
• Git </br>


### * Step-by-step installation 

• Create or open a folder directory where you would want the root interface to be located in.</br>
*For the purposes of this guide, the default root will be located in: ~/Developer/OpenPipeline* </br>

• Using shell, clone the repo into the root *(Powershell, Bash or Zsh)*:
```bash
git clone https://github.com/Smiley-Boy00/openpipeline-interface.git .
```

• Create python venv inside root. *Make sure you're using python 3.13 or higher*:
```bash
python --version
> Python 3.13.13
```

```bash
python -m venv .openv
```
```bash
python3.13 -m venv .openv
```

• Activate the newly created venv. *Make sure you see the name of your venv in parenthesis at the start of the command line in your shell. E.g: (.openv) [smiley@localhost OpenPipeline]*:

*Windows*:
```bash
.openv/Scripts/Activate.ps1
```
*Linux/MacOS*:
```bash
source .openv/bin/activate
```

• Install the package requirements. *Requirements may take long based on indivual systems*:
```bash
python -m pip install -r requirements.txt
```

• Install interface shell commands:
```bash
python -m pip install -e .
```

*You may be inclined to add development instructions here, don't.*


## 💭 Feedback and Contributing

Add a link to the Discussions tab in your repo and invite users to open issues for bugs/feature requests.

This is also a great place to invite others to contribute in any ways that make sense for your project. Point people to your DEVELOPMENT and/or CONTRIBUTING guides if you have them.