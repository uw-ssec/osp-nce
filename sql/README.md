# SQL Queries

This folder represents the core of the application's database layer. The queries in this folder access the non-production verison of the `RADDB` and the employee data warehouse (`EDW`) and return data from these databases for processing by the application layer. 

With minor exceptions, we try to avoid including business logic in these queries to keep code modular and maintainable. Instead, methods in the application layer – contained in the [`src`](../src/) folder – transform the database output into answers to questions on the [extension review matrix](../assets/nsf_prior_approval_matrix.pdf).