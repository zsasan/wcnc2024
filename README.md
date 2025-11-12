Joint Network Slicing, Routing, and In-Network Computing (WF-JSRIN)

This repo implements the problem studied in the paper: joint network slicing, routing, and in-network computing to (i) maximize accepted users and (ii) minimize energy/cost, under E2E delay and capacity constraints.

What’s inside

MILP (Optimal) with PySCIPOpt

Two variants:

Opt-IN: allows in-network computation on intermediate nodes

Opt-C: cloud-only (all processing at the cloud node)

WF-JSRIN (Heuristic): fast, near-optimal water-filling–based algorithm

Random: baseline allocator


Objective: maximize accepted users – total energy/cost.

Code map (typical)

static_graph() – build base (in-network) graph with capacities/delays/costs

cloud_graph(G) – cloud-only variant (Opt-C)

slice_generator(G, M, users_per_slice) – make users & all simple paths (src=1 → cloud=4)

solve_ec_model(G, slices, f) – MILP (Opt-IN / Opt-C depending on graph)

solve_heuristic(G, slices, f) – WF-JSRIN

solve_random(G, slices, f) – baseline

Results are appended to output3.txt (accepted users, total cost/energy, bandwidth, runtime).



Requirements

Python 3.8+

networkx

pyscipopt (needs SCIP installed/configured)

Standard libs: random, time, itertools


Install (example):

python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install networkx pyscipopt      # after installing SCIP

Quick start
python main.py


What it does:

Builds graphs, generates slices/users/paths

Runs Opt-IN, Opt-C, WF-JSRIN, Random

Writes metrics to output.txt



Citation

If you use this code, please cite the paper:

Sasan, Zeinab, et al. "Joint network slicing, routing, and in-network computing for energy-efficient 6g." 2024 IEEE Wireless Communications and Networking Conference (WCNC). IEEE, 2024.
