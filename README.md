# UW GRACE: Grant Review Automation for Compliance Excellence


### Context

The University of Washington's Office of Sponsored Programs (OSP) works with UW primary investigators (PIs) to manage grants, contracts, and other sources of funding for their research activites. Part of OSP's work is to process **no cost extensions (NCEs)** – requests by PIs to extend the length of a grant/contract without modifying funding commitments. NCEs may or may not be subject to approval by the sponsor of a grant. Program Coordinators (PCs) within OSP are responsible for reviewing PI requests for no cost extension and filling out an extension review matrix (ERM), which helps OSP decide whether sponsor approval is required.

### Goals

The goal of this project is to **establish proof of concept for process automations aimed at streamlining Program Coordinators' NCE review process.** When this project began, PCs worked from a blank copy of the Extension Review Matrix form during each review. While some items on the form require careful assessment and consideration by PCs, others are straightforward and objective attributes of the grant which is under review. Prior to this project, PCs had to look up the answer to each review item on the ERM individually. After the automations are completed, PCs will start their workflow with a **partially pre-filled version of the extension review matrix.**

## Getting Started 

First you need to install the docker CLI 
on mac: 
brew install docker 

(Note: if you encounter errors running the commands below, you may also need to install [Docker Desktop])(https://www.docker.com/products/docker-desktop/))

on windows:
Install Docker Desktop and enable  wsl integration.

Look here for more info: [link](https://www.docker.com/get-started/)

Then, run `./deploy/build.sh`

This will build the containers and run the app 

### Repo Structure

#### `src`

This is the main development folder.

### Application Architecture

#### Data Layer
- Retrieves relevant data from the university’s databases using SQL queries.
- Uses SQLAlchemy to convert the database output into a Python-friendly format.
- Passes the processed data to the application layer as input.
#### Application Layer
- Processes data from the data layer, applies business logic, and generates responses for each question in the Extension Review Matrix (ERM).
#### Presentation Layer
- The user interface is a web application built with Streamlit, a Python package that simplifies the creation of interactive web UIs.
- While the frontend is ultimately rendered in HTML and JavaScript, we do not develop it directly in these languages.

```
+---------------------------+
|  Presentation Layer       |
|  (Streamlit Web UI)       |
+---------------------------+
            │  
            ▼  
+---------------------------+
|  Application Layer        |
|  (Business Logic)         |
|  - Processes data         |
|  - Generates ERM answers |
+---------------------------+
            │  
            ▼  
+---------------------------+
|  Data Layer               |
|  (University Databases)   |
|  - SQL Queries            |
|  - SQLAlchemy for ORM     |
+---------------------------+
```

#### `src/backend/libs`

This folder contains methods for:
- backend functionality
    - connects to the PI form (an `xls` file stored in Sharepoint) 
    - connects to the `RADDB` and `EDW` SQL databases
- business logic functionality
    - transforms data extracted from the data sources into answers to ERM questions
    - delivers the answers as a `JSON` to the frontend

Methods defined in this folder serve as helper methods in the [main application flow](../serve/).

#### `shared`

Provides utility functions for resolving paths and directories within the project, such as obtaining the project root, SQL directory, and data directory paths.


#### `sql`

This folder represents the core of the application's database layer. The queries in this folder access the non-production verison of the `RADDB` and the employee data warehouse (`EDW`) and return data from these databases for processing by the application layer. 

With minor exceptions, we try to avoid including business logic in these queries to keep code modular and maintainable. Instead, methods in the application layer – contained in the [`src`](../src/) folder – transform the database output into answers to questions on the [extension review matrix](../assets/nsf_prior_approval_matrix.pdf).

#### `deploy`

The bash script in this folder installs software and libraries that the end user will need to run the GRACE streamlit web app. The script:

- installs the correct version of Python, if needed 
- installs the poetry package manager, if needed, and uses it to load the right packages to run the web app
- allows the user to specify environment variables (which they need to connect to databases which the app depends on)
- kills any processes running on the port needed to listen for API calls
- launches the Streamlit application

This script represents a streamlined way to launch the web app without requiring end users to configure the computing environment.

#### `assets`

Contains references and miscellaneous assets related to the project.


#### `eda`

This folder documents queries we performed to **explore** the datasets on which the GRACE web app depends, mostly `RADDB`. The purpose is to understand the data and ensure that the application layer correctly anticipates the format and conventions of data it ingests. Queries in this folder **do not contribute to the function of the application**.