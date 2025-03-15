# UW GRACE: Grant Review Automation for Compliance Excellence

## Table of Contents

- [Context](#context)
- [Project Overview](#project-overview)
- [Getting Started](#getting-started)
- [Autofiller Architecture](#autofiller-architecture)
- [Chatbot Assistant Architecture](#chatbot-assistant-architecture)
- [Repo Structure](#repo-structure)
- [ERM Shorthand Reference](#erm-shorthand-reference)

## Context

The University of Washington's Office of Sponsored Programs (OSP) works with UW primary investigators (PIs) to manage grants, contracts, and other sources of funding for their research activites. Part of OSP's work is to process **no cost extensions (NCEs)** – requests by PIs to extend the length of a grant/contract without modifying funding commitments. NCEs may or may not be subject to approval by the sponsor of a grant. Program Coordinators (PCs) within OSP are responsible for reviewing PI requests for no cost extension and filling out a form called the **extension review matrix (ERM)**, which helps OSP decide whether sponsor approval is required.

## Project Overview

Our goal was to **establish a proof of concept for process automations to streamline PCs' NCE review workflow.** Before this project, PCs manually completed the Extension Review Matrix (ERM), looking up each review item individually. While some items required careful assessment, others were straightforward attributes that could be pulled directly from existing databases.

To design our solution, we thought of the ERM as containing two types of items:

- **Structured items** – objective attributes of a grant (e.g., budget details) that PCs previously had to look up and enter manually.
- **Unstructured items** – more complex elements requiring interpretation, such as reviewing contract terms to determine if sponsors explicitly require extension approval.

To streamline the process, we aimed to:

1. **Automate structured items** by developing an autofill feature that pre-fills the ERM using university database records.
2. **Assist with unstructured items** by integrating a virtual assistant powered by a large language model (LLM), enabling PCs to quickly locate relevant document sections and ask content-related questions.

To ensure usability, we collaborated closely with a program coordinator in the Office of Sponsored Programs (OSP) and conducted user interviews with managers. These conversations helped us ensure that UW-GRACE uses relevant data, accurately replicates real-life workflows, and aligns the tool's outputs with the way PCs make decisions.

## Getting Started

UW-GRACE is currently in the proof-of-concept phase. In this stage, we are only able to provide functionality to users affiliated with the University of Washington who have already been provisioned with permissions to access certain university IT resources. If you believe you fall into this category, please contact the contributors to this repository or [SSEC](https://escience.washington.edu/software-engineering/ssec/) to coordinate access. If you do not have the required permissions, you will not be able to run GRACE.

To get started with UW-GRACE, you first need to install Docker.

On Mac OS, open the Terminal and run:
`brew install docker`

(Note: if you encounter errors running the commands below, you may also need to install [Docker Desktop](https://www.docker.com/products/docker-desktop/))

On Windows, please install Docker Desktop and enable wsl integration. See [here](https://www.docker.com/get-started/) for more info.

Once you've completed those steps, open the Terminal (Mac OS) or Command Prompt (Windows). Navigate to the folder where you'd like to store this project. [Clone this repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository). Then, navigate to the top-level folder in this repo and run `./deploy/build.sh`

This will build containers that store the dependencies GRACE relies on and automatically and run the app. When you run this command, you should get a message that looks like:

```
frontend-1  |   You can now view your Streamlit app in your browser.
frontend-1  |
frontend-1  |   Local URL: http://localhost:8501
frontend-1  |   Network URL: http://172.18.0.3:8501
frontend-1  |   External URL: http://24.19.202.153:8501
```

Follow the Local URL (you should be able to Ctrl+Clickt the link) to open the app in the browser.

## Autofiller Architecture

At the highest level, the Autofiller portion of the GRACE application is organized as follows.

#### Data Layer

- Retrieves relevant data from the university’s databases using SQL queries.
- Uses SQLAlchemy to convert the database output into a Python-friendly format.
- Passes the processed data to the application layer as input.

#### Application Layer

- Processes data from the data layer, applies business logic, and generates responses for each question in the Extension Review Matrix (ERM).

#### Presentation Layer

- The user interface is a web application built with Streamlit, a Python package that simplifies the creation of interactive web UIs.
- While the frontend is ultimately rendered in HTML and JavaScript, we do not develop it directly in these languages.

## Chatbot Assistant Architecture

At the highest level, the Chatbot Assistant portion of the GRACE application is organized as follows.

#### Data Layer

- The `Retriever` class fetches relevant documents based on the user's query.
- This layer also manages the creation and retrieval of vector stores for efficient document retrieval.

#### Application Layer

- The `LanguageModel` class loads and utilizes language models for generating responses.
- Provides endpoints for document retrieval and response generation using FastAPI.
- Configures and runs the backend server using FastAPI to handle API requests.

## Repo Structure

### `src` Folder Summary

This is the main development folder

## `osp_nce`

- **`__init__.py`**: Initializes the `osp_nce` package.

## `backend`

### Data Layer

- **`queries`**: Contains SQL query files for interacting with the database.
  - **`nonprod_rad.sql`**: Contains SQL queries for retrieving data from the database.
- **`sql_connector.py`**: Contains the `SQLConnector` class for database interactions.
- **`sharepoint_connector.py`**: Contains the `SharepointConnector` class for interacting with SharePoint.

### Application Layer

- **`__init__.py`**: Initializes the `backend` package.
- **`wsgi.py`**: Contains the FastAPI application setup and endpoint definitions.
- **`autofiller.py`**: Contains the `ERMAutoFiller` class for autofilling the Extension Review Matrix (ERM).

## `frontend`

### Presentation Layer

- **`app.py`**: Main entry point for the Streamlit frontend application.
- **`chatbot_page.py`**: Contains the chatbot page implementation.
- **`form_page.py`**: Contains the form page implementation.

## `llm_backend_vm`

### Dedicated LLM Environment

- **`docker-compose.yml`**: Docker Compose configuration for the LLM backend.
- **`Dockerfile`**: Dockerfile for building the LLM backend.
- **`pixi.lock`**: Lock file for Pixi dependencies.
- **`pixi.toml`**: Configuration file for Pixi dependencies.

### Data Layer

- **`retriever.py`**: Contains the `Retriever` class for document retrieval.

### Application Layer

- **`language_model.py`**: Contains the `LanguageModel` class for loading and using language models.
- **`serve`**: Contains server-related files for the LLM backend.
- **`tests`**: Contains test files for the LLM backend.
  - **`test_retriever.py`**: Contains tests for the `Retriever` class.

## `shared`

- **`__init__.py`**: Initializes the `shared` package.
- **`forms.py`**: Contains form-related utilities.
- **`templates`**: Contains template files.
  - **`extension_review_matrix_fillable_form.json`**: JSON template for the Extension Review Matrix (ERM).

## `deploy`

The bash script in this folder installs software and libraries that the end user will need to run the GRACE Streamlit web app. The script:

- Installs the correct version of Python, if needed.
- Installs the poetry package manager, if needed, and uses it to load the right packages to run the web app.
- Allows the user to specify environment variables (which they need to connect to databases which the app depends on).
- Kills any processes running on the port needed to listen for API calls.
- Launches the Streamlit application.

This script represents a streamlined way to launch the web app without requiring end users to configure the computing environment.

## `eda`

This folder documents queries we performed to **explore** the datasets on which the GRACE web app depends, mostly `RADDB`. The purpose is to understand the data and ensure that the application layer correctly anticipates the format and conventions of data it ingests. Queries in this folder **do not contribute to the function of the application**.

## [Reference]: ERM Shorthand

Throughout our codebase, we refer to items that appear on the extension review matrix (ERM). These are verbose, so we usually abbreviate them. The table below specifies abbreviations.

`ri` stands for "Review Item". Review items are enumerated in the order they appear on the ERM. The review items below are from the Spring 2025 version of the ERM; this may be updated in the future.

| Code Abbreviation | Form Text                                                                    |
| ----------------- | ---------------------------------------------------------------------------- |
| `mod-worktag-id`  | Mod/Worktag ID:                                                              |
| `pi_name`         | PI Name                                                                      |
| `ri1`             | SFI Current?                                                                 |
| `ri2`             | Remaining Balance $$:                                                        |
| `ri3`             | Is the award in deficit?                                                     |
| `ri4`             | Is the balance greater than 25% of the total award?                          |
| `ri5`             | Award lines listed or "extend all" indicated?                                |
| `ri6`             | Temporary request?                                                           |
| `ri7`             | New cost share?                                                              |
| `ri8`             | Human Subjects?                                                              |
| `ri9`             | Animal Use?                                                                  |
| `ri10`            | Prior approval required?                                                     |
| `ri11`            | Has the project previously been extended? Is this an NIH 2nd+ extension?     |
| `ri12`            | Is the request to extend within Sponsor's required timeframe?                |
| `ri13`            | Is this a federal contract?                                                  |
| `ri14`            | For federal contracts only: is FAR clause 52.222-54 incorporated (e-verify)? |
| `ri15`            | Fixed Price terms?                                                           |
| `ri16`            | Paid in full?                                                                |
| `ri17`            | All deliverables submitted?                                                  |
| `review_notes`    | Review Notes                                                                 |
