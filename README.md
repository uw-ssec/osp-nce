# UW GRACE: Grant Review Automation for Compliance Excellence


### Context

The University of Washington's Office of Sponsored Programs (OSP) works with UW primary investigators (PIs) to manage grants, contracts, and other sources of funding for their research activites. Part of OSP's work is to process **no cost extensions (NCEs)** – requests by PIs to extend the length of a grant/contract without modifying funding commitments. NCEs may or may not be subject to approval by the sponsor of a grant. Program Coordinators (PCs) within OSP are responsible for reviewing PI requests for no cost extension and filling out an extension review matrix (ERM), which helps OSP decide whether sponsor approval is required.

### Goals

The goal of this project is to **establish proof of concept for process automations aimed at streamlining Program Coordinators' NCE review process.** When this project began, PCs worked from a blank copy of the Extension Review Matrix form during each review. While some items on the form require careful assessment and consideration by PCs, others are straightforward and objective attributes of the grant which is under review. Prior to this project, PCs had to look up the answer to each review item on the ERM individually. After the automations are completed, PCs will start their workflow with a **partially pre-filled version of the extension review matrix.**

## Getting Started 

First you need to install the docker CLI 
on mac: 
brew install docker 

on windows:
Good luck.

Look here for more info: [link](https://www.docker.com/get-started/)

Then, in the project root 
`docker build -t {your_docker_image_name} .`
Once this has been done you now have an image of this directory!

To set off a container with this image use:
`docker run -p 8000:8000 -p 8501:8501 :{your_docker_image_name}`