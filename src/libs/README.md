# `src`

This folder contains methods for:
- backend functionality
    - connects to the PI form (an `xls` file stored in Sharepoint) 
    - connects to the `RADDB` and `EDW` SQL databases
- business logic functionality
    - transforms data extracted from the data sources into answers to ERM questions
    - delivers the answers as a `JSON` to the frontend

Methods defined in this folder serve as helper methods in the [main application flow](../serve/).