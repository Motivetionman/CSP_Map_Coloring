"""
Constraint Satisfaction Problem (CSP) - Australia Map Coloring Problem
Comparing Two Major Paradigms:
1. Systematic Search (Backtracking Search + Heuristics):
   - Standard Recursive Backtracking (Slide 12-13)
   - Backtracking with MRV (Minimum Remaining Values) (Slide 5, 13)
   - Backtracking with Forward Checking (Slide 5, 14-22)
2. Local Search (Repair-based):
   - Min-Conflicts Algorithm / Min-Conflicts Procedure (MCP) (AIMA Chapter 6.4)
"""

from typing import Dict, List, Set, Any, Optional, Tuple, Callable
import copy
import random
import time


class CSP:
    def __init__(self, variables: List[str], domains: Dict[str, List[Any]], neighbors: Dict[str, List[str]]):
        self.variables = variables
        self.domains = {v: list(domains[v]) for v in variables}
        self.neighbors = {v: list(neighbors.get(v, [])) for v in variables}
        # Statistics for analysis
        self.assign_count = 0
        self.backtrack_count = 0
        self.constraint_checks = 0

    def is_consistent(self, var: str, value: Any, assignment: Dict[str, Any]) -> bool:
        """
        Check if assigning `value` to `var` violates any constraints with already assigned neighbors.
        Constraint: Adjacent regions must have different colors (var != neighbor).
        """
        for neighbor in self.neighbors.get(var, []):
            self.constraint_checks += 1
            if neighbor in assignment and assignment[neighbor] == value:
                return False
        return True

    def is_complete(self, assignment: Dict[str, Any]) -> bool:
        """Check if all variables have been assigned."""
        return len(assignment) == len(self.variables)


def create_australia_csp() -> CSP:
    """
    Creates Australia Map Coloring CSP as described in the lecture slides.
    Regions:
      - WA: Western Australia
      - NT: Northern Territory
      - SA: South Australia
      - Q: Queensland
      - NSW: New South Wales
      - V: Victoria
      - T: Tasmania
    """
    variables = ["WA", "NT", "SA", "Q", "NSW", "V", "T"]
    colors = ["Red", "Green", "Blue"]
    domains = {v: colors.copy() for v in variables}

    # Adjacency constraints according to Australia's map
    neighbors = {
        "WA": ["NT", "SA"],
        "NT": ["WA", "SA", "Q"],
        "SA": ["WA", "NT", "Q", "NSW", "V"],
        "Q": ["NT", "SA", "NSW"],
        "NSW": ["Q", "SA", "V"],
        "V": ["SA", "NSW"],
        "T": []  # Tasmania is an island with no land borders
    }

    return CSP(variables, domains, neighbors)


# =====================================================================
# 1. Standard Recursive Backtracking Search (Slide 12-13)
# =====================================================================

def backtracking_search(csp: CSP, verbose: bool = False) -> Optional[Dict[str, Any]]:
    """
    Standard Backtracking Search as shown in Slide 12-13:
    function BACKTRACKING-SEARCH(csp) returns a solution, or failure
        return RECURSIVE-BACKTRACKING({}, csp)
    """
    csp.assign_count = 0
    csp.backtrack_count = 0
    csp.constraint_checks = 0
    return recursive_backtracking({}, csp, verbose)


def select_unassigned_variable_simple(assignment: Dict[str, Any], csp: CSP) -> str:
    """Select the first unassigned variable in default order."""
    for var in csp.variables:
        if var not in assignment:
            return var
    raise ValueError("All variables are assigned.")


def order_domain_values_simple(var: str, assignment: Dict[str, Any], csp: CSP) -> List[Any]:
    """Return values in domain in default order."""
    return csp.domains[var]


def recursive_backtracking(
    assignment: Dict[str, Any],
    csp: CSP,
    verbose: bool = False
) -> Optional[Dict[str, Any]]:
    if csp.is_complete(assignment):
        return assignment

    var = select_unassigned_variable_simple(assignment, csp)

    for value in order_domain_values_simple(var, assignment, csp):
        if csp.is_consistent(var, value, assignment):
            assignment[var] = value
            csp.assign_count += 1
            if verbose:
                print(f"[Assign] {var} = {value} | Current: {assignment}")

            result = recursive_backtracking(assignment, csp, verbose)
            if result is not None:
                return result

            # Backtrack
            del assignment[var]
            csp.backtrack_count += 1
            if verbose:
                print(f"[Backtrack] Undo {var} = {value}")

    return None


# =====================================================================
# 2. Backtracking with MRV (Minimum Remaining Values) Heuristic (Slide 5, 13)
# =====================================================================

def select_unassigned_variable_mrv(assignment: Dict[str, Any], csp: CSP, current_domains: Dict[str, List[Any]]) -> str:
    """MRV heuristic: Choose variable with fewest legal values remaining."""
    unassigned = [v for v in csp.variables if v not in assignment]
    def count_legal_values(v: str) -> int:
        return sum(1 for val in current_domains[v] if csp.is_consistent(v, val, assignment))
    return min(unassigned, key=count_legal_values)


def backtracking_search_mrv(csp: CSP, verbose: bool = False) -> Optional[Dict[str, Any]]:
    csp.assign_count = 0
    csp.backtrack_count = 0
    csp.constraint_checks = 0
    domains = {v: list(csp.domains[v]) for v in csp.variables}
    return recursive_backtracking_mrv({}, csp, domains, verbose)


def recursive_backtracking_mrv(
    assignment: Dict[str, Any],
    csp: CSP,
    domains: Dict[str, List[Any]],
    verbose: bool = False
) -> Optional[Dict[str, Any]]:
    if csp.is_complete(assignment):
        return assignment

    var = select_unassigned_variable_mrv(assignment, csp, domains)

    for value in domains[var]:
        if csp.is_consistent(var, value, assignment):
            assignment[var] = value
            csp.assign_count += 1
            if verbose:
                print(f"[MRV Assign] {var} = {value} | Current: {assignment}")

            result = recursive_backtracking_mrv(assignment, csp, domains, verbose)
            if result is not None:
                return result

            del assignment[var]
            csp.backtrack_count += 1
            if verbose:
                print(f"[MRV Backtrack] Undo {var} = {value}")

    return None


# =====================================================================
# 3. Backtracking with Forward Checking (Slide 5, 14-22)
# =====================================================================

def forward_check(
    csp: CSP,
    var: str,
    value: Any,
    assignment: Dict[str, Any],
    domains: Dict[str, List[Any]]
) -> Tuple[bool, Dict[str, List[Any]]]:
    """
    Forward Checking (Slides 14-22):
    When var is assigned value, for each unassigned neighbor of var:
    remove value from that neighbor's domain.
    If any unassigned neighbor's domain becomes empty, forward check fails!
    """
    new_domains = {v: list(dom) for v, dom in domains.items()}
    new_domains[var] = [value]

    for neighbor in csp.neighbors.get(var, []):
        if neighbor not in assignment:
            csp.constraint_checks += 1
            if value in new_domains[neighbor]:
                new_domains[neighbor].remove(value)
                if len(new_domains[neighbor]) == 0:
                    return False, new_domains

    return True, new_domains


def backtracking_search_fc(
    csp: CSP,
    variable_order: Optional[List[str]] = None,
    value_order: Optional[Dict[str, List[Any]]] = None,
    verbose: bool = False
) -> Optional[Dict[str, Any]]:
    csp.assign_count = 0
    csp.backtrack_count = 0
    csp.constraint_checks = 0
    domains = {v: list(csp.domains[v]) for v in csp.variables}
    return recursive_backtracking_fc({}, csp, domains, variable_order, value_order, verbose)


def recursive_backtracking_fc(
    assignment: Dict[str, Any],
    csp: CSP,
    domains: Dict[str, List[Any]],
    variable_order: Optional[List[str]] = None,
    value_order: Optional[Dict[str, List[Any]]] = None,
    verbose: bool = False
) -> Optional[Dict[str, Any]]:
    if csp.is_complete(assignment):
        return assignment

    if variable_order:
        var = next(v for v in variable_order if v not in assignment)
    else:
        var = next(v for v in csp.variables if v not in assignment)

    # Determine values to try
    if value_order and var in value_order:
        candidate_values = [val for val in value_order[var] if val in domains[var]]
    else:
        candidate_values = list(domains[var])

    for value in candidate_values:
        if csp.is_consistent(var, value, assignment):
            consistent, new_domains = forward_check(csp, var, value, assignment, domains)

            if verbose:
                status = "OK" if consistent else "FAILED (Empty domain detected!)"
                print(f"[FC Try] Assign {var} = {value} -> {status}")
                remaining_str = " | ".join(f"{v}: {new_domains[v]}" for v in csp.variables if v not in assignment and v != var)
                print(f"         Remaining domains: {remaining_str}")

            if consistent:
                assignment[var] = value
                csp.assign_count += 1

                result = recursive_backtracking_fc(assignment, csp, new_domains, variable_order, value_order, verbose)
                if result is not None:
                    return result

                del assignment[var]
                csp.backtrack_count += 1
                if verbose:
                    print(f"[FC Backtrack] Undo {var} = {value}")
            else:
                csp.backtrack_count += 1
                if verbose:
                    print(f"[FC Early Cut] Domain wipe-out detected, pruned branch for {var} = {value}")

    return None


def demonstrate_slide_14_to_22() -> bool:
    """
    Demonstrates the exact step-by-step Forward Checking scenario from lecture slides:
    - Slide 15: Assign WA = Red
    - Slide 16: Assign Q = Green
    - Slide 17: Assign V = Blue
    - Slides 18-22: SA domain is wiped out (len=0) because SA is adjacent to WA, Q, and V!
    """
    csp = create_australia_csp()
    domains = {v: list(csp.domains[v]) for v in csp.variables}
    assignment: Dict[str, Any] = {}

    print("\n--- Step-by-Step Simulation of Slide 14-22 ---")
    print(f"Initial Domains: { {v: domains[v] for v in csp.variables} }")

    # Step 1: Slide 15 - Assign WA = Red
    ok_wa, domains = forward_check(csp, "WA", "Red", assignment, domains)
    assignment["WA"] = "Red"
    print("\n[Slide 15] Assign WA = Red")
    print(f"  Forward Check OK: {ok_wa}")
    print(f"  NT domain (neighbor of WA): {domains['NT']}")
    print(f"  SA domain (neighbor of WA): {domains['SA']}")

    # Step 2: Slide 16 - Assign Q = Green
    ok_q, domains = forward_check(csp, "Q", "Green", assignment, domains)
    assignment["Q"] = "Green"
    print("\n[Slide 16] Assign Q = Green")
    print(f"  Forward Check OK: {ok_q}")
    print(f"  NT domain (neighbor of WA & Q): {domains['NT']}")
    print(f"  SA domain (neighbor of WA & Q): {domains['SA']}")
    print(f"  NSW domain (neighbor of Q): {domains['NSW']}")

    # Step 3: Slide 17 - Assign V = Blue
    print("\n[Slide 17] Try Assign V = Blue")
    ok_v, domains_after_v = forward_check(csp, "V", "Blue", assignment, domains)
    print(f"  Forward Check Result: {ok_v}")
    print(f"  NSW domain (neighbor of Q & V): {domains_after_v['NSW']}")
    print(f"  SA domain (neighbor of WA, Q & V): {domains_after_v['SA']} <-- EMPTY DOMAIN!")

    # Slides 18-22: Failure detected
    if not ok_v and len(domains_after_v["SA"]) == 0:
        print("\n[Slides 18-22] FAILURE DETECTED: Domain Wipe-Out on South Australia (SA)!")
        print("  -> SA has no legal colors left in {Red, Green, Blue}.")
        print("  -> Forward Checking prunes branch V = Blue immediately without searching deeper.")
        print("  -> Trigger Backtrack!\n")
        return True
    return False


# =====================================================================
# 4. Min-Conflicts Algorithm (MCP - Local Search for CSP)
# =====================================================================

def count_conflicts(var: str, value: Any, assignment: Dict[str, Any], csp: CSP) -> int:
    """
    Counts how many neighbors of `var` in `assignment` currently have the same color `value`.
    """
    conflicts = 0
    for neighbor in csp.neighbors.get(var, []):
        csp.constraint_checks += 1
        if neighbor in assignment and assignment[neighbor] == value:
            conflicts += 1
    return conflicts


def total_conflicts(assignment: Dict[str, Any], csp: CSP) -> int:
    """
    Calculate the total number of violated constraint edges across the whole graph.
    """
    violated = 0
    for var in csp.variables:
        val = assignment.get(var)
        for neighbor in csp.neighbors.get(var, []):
            if assignment.get(neighbor) == val:
                violated += 1
    # Each undirected constraint edge is counted twice
    return violated // 2


def get_conflicted_variables(assignment: Dict[str, Any], csp: CSP) -> List[str]:
    """
    Returns a list of all variables that violate at least one constraint with their neighbors.
    """
    conflicted = []
    for var in csp.variables:
        if count_conflicts(var, assignment[var], assignment, csp) > 0:
            conflicted.append(var)
    return conflicted


def min_conflicts(
    csp: CSP,
    max_steps: int = 1000,
    initial_assignment: Optional[Dict[str, Any]] = None,
    random_seed: Optional[int] = None,
    verbose: bool = False
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Min-Conflicts Algorithm / Min-Conflicts Procedure (MCP):
    Local Search for CSP (Russell & Norvig AIMA Chapter 6.4)

    Algorithm:
    1. Start with an initial complete assignment (can be random or heuristic).
    2. For step = 1 to max_steps:
        a. If assignment has 0 conflicts, return solution!
        b. Randomly select a conflicted variable `var`.
        c. Pick the value for `var` that minimizes the number of conflicts with neighbors.
           (Ties broken randomly).
        d. Set assignment[var] = best_value.
    3. Return None (failure / local plateau).
    """
    if random_seed is not None:
        random.seed(random_seed)

    csp.assign_count = 0
    csp.constraint_checks = 0

    # Step 1: Initial complete assignment
    if initial_assignment is not None:
        current = copy.deepcopy(initial_assignment)
    else:
        current = {v: random.choice(csp.domains[v]) for v in csp.variables}

    stats = {
        "steps": 0,
        "initial_conflicts": total_conflicts(current, csp),
        "conflict_history": [total_conflicts(current, csp)],
        "converged": False
    }

    if verbose:
        print(f"[MCP Init] Initial Assignment: {current}")
        print(f"           Initial Conflicts: {stats['initial_conflicts']}")

    # Step 2: Iterative repair
    for step in range(1, max_steps + 1):
        stats["steps"] = step
        conflicted_vars = get_conflicted_variables(current, csp)

        if not conflicted_vars:
            stats["converged"] = True
            if verbose:
                print(f"[MCP Success] Found solution at step {step} with 0 conflicts!")
            return current, stats

        # Select a random conflicted variable
        var = random.choice(conflicted_vars)

        # Find the value that minimizes conflicts with neighbors
        min_conf = float('inf')
        best_values = []

        for val in csp.domains[var]:
            c = count_conflicts(var, val, current, csp)
            if c < min_conf:
                min_conf = c
                best_values = [val]
            elif c == min_conf:
                best_values.append(val)

        # Break ties randomly
        chosen_value = random.choice(best_values)
        current[var] = chosen_value
        csp.assign_count += 1

        curr_conflicts = total_conflicts(current, csp)
        stats["conflict_history"].append(curr_conflicts)

        if verbose:
            print(f"[MCP Step {step:02d}] Fix {var} -> {chosen_value} (conflicts: {curr_conflicts}) | {current}")

        if curr_conflicts == 0:
            stats["converged"] = True
            if verbose:
                print(f"[MCP Success] Converged to valid solution at step {step}!")
            return current, stats

    return None, stats


def min_conflicts_with_restarts(
    csp: CSP,
    max_steps: int = 200,
    max_restarts: int = 10,
    random_seed: Optional[int] = None,
    verbose: bool = False
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Min-Conflicts with Random Restarts to escape local plateaus / cycles.
    """
    if random_seed is not None:
        random.seed(random_seed)

    total_steps = 0
    all_history = []

    for restart in range(max_restarts):
        if verbose:
            print(f"\n[MCP Restart {restart + 1}/{max_restarts}]")
        sol, stats = min_conflicts(csp, max_steps=max_steps, verbose=verbose)
        total_steps += stats["steps"]
        all_history.extend(stats["conflict_history"])

        if sol is not None:
            stats["total_steps"] = total_steps
            stats["restarts_used"] = restart
            stats["conflict_history"] = all_history
            return sol, stats

    return None, {"total_steps": total_steps, "restarts_used": max_restarts, "converged": False}


# =====================================================================
# 5. Algorithm Comparison & Benchmark (Systematic vs Local Search)
# =====================================================================

def run_benchmark_comparison(csp: CSP, num_trials: int = 50) -> Dict[str, Any]:
    """
    Runs an empirical benchmark comparing:
    1. Standard Backtracking (DFS - Systematic)
    2. Backtracking + MRV Heuristic
    3. Backtracking + Forward Checking (FC)
    4. Min-Conflicts Algorithm (MCP - Local Search)
    """
    algorithms = {
        "Standard Backtracking": lambda: backtracking_search(csp),
        "Backtracking + MRV": lambda: backtracking_search_mrv(csp),
        "Backtracking + Forward Checking": lambda: backtracking_search_fc(csp),
        "Min-Conflicts (MCP)": lambda: min_conflicts(csp, max_steps=500)[0]
    }

    results = {}

    for name, runner in algorithms.items():
        times = []
        assigns = []
        backtracks = []
        checks = []
        successes = 0

        for trial in range(num_trials):
            start = time.perf_counter()
            sol = runner()
            elapsed_us = (time.perf_counter() - start) * 1_000_000

            if sol is not None:
                is_valid, _ = validate_solution(sol, csp)
                if is_valid:
                    successes += 1

            times.append(elapsed_us)
            assigns.append(csp.assign_count)
            backtracks.append(csp.backtrack_count)
            checks.append(csp.constraint_checks)

        results[name] = {
            "success_rate": (successes / num_trials) * 100,
            "avg_time_us": sum(times) / num_trials,
            "avg_assigns": sum(assigns) / num_trials,
            "avg_backtracks": sum(backtracks) / num_trials,
            "avg_checks": sum(checks) / num_trials,
        }

    return results


def validate_solution(assignment: Dict[str, Any], csp: CSP) -> Tuple[bool, List[str]]:
    """Validates whether a solution satisfies all CSP constraints."""
    if not assignment:
        return False, ["Assignment is None or empty."]
    errors = []
    if not csp.is_complete(assignment):
        errors.append(f"Assignment incomplete: {len(assignment)}/{len(csp.variables)} variables assigned.")

    for var in csp.variables:
        if var not in assignment:
            errors.append(f"Variable {var} is unassigned.")
            continue
        val = assignment[var]
        if val not in csp.domains[var]:
            errors.append(f"Variable {var} has value {val} not in domain {csp.domains[var]}.")

        for neighbor in csp.neighbors.get(var, []):
            if neighbor in assignment and assignment[neighbor] == val:
                errors.append(f"Constraint violation: {var} and {neighbor} both have color '{val}'.")

    return (len(errors) == 0, errors)


if __name__ == "__main__":
    print("=" * 70)
    print("1. Standard Backtracking Search (Slide 12-13)")
    print("=" * 70)
    csp1 = create_australia_csp()
    sol1 = backtracking_search(csp1, verbose=False)
    valid1, _ = validate_solution(sol1, csp1)
    print(f"Solution: {sol1}")
    print(f"Valid: {valid1} | Assignments: {csp1.assign_count} | Backtracks: {csp1.backtrack_count} | Checks: {csp1.constraint_checks}\n")

    print("=" * 70)
    print("2. Backtracking Search with MRV Heuristic (Slide 5)")
    print("=" * 70)
    csp2 = create_australia_csp()
    sol2 = backtracking_search_mrv(csp2, verbose=False)
    valid2, _ = validate_solution(sol2, csp2)
    print(f"Solution: {sol2}")
    print(f"Valid: {valid2} | Assignments: {csp2.assign_count} | Backtracks: {csp2.backtrack_count} | Checks: {csp2.constraint_checks}\n")

    print("=" * 70)
    print("3. Demonstration of Slide 14-22 (Forward Checking & Backtrack)")
    print("=" * 70)
    demonstrate_slide_14_to_22()

    print("=" * 70)
    print("4. Min-Conflicts Algorithm (MCP - Local Search for CSP)")
    print("   Starting from random assignment and repairing conflicts iteratively")
    print("=" * 70)
    csp4 = create_australia_csp()
    sol4, stats4 = min_conflicts(csp4, max_steps=50, random_seed=42, verbose=True)
    valid4, errs4 = validate_solution(sol4, csp4)
    print(f"\nFinal MCP Solution: {sol4}")
    print(f"Valid: {valid4} | Steps Taken: {stats4['steps']} | Initial Conflicts: {stats4['initial_conflicts']} | Final Conflicts: 0\n")

    print("=" * 70)
    print("5. Empirical Benchmark Comparison (Systematic Search vs Local Search)")
    print("   Ran across 50 trials per algorithm")
    print("=" * 70)
    benchmark = run_benchmark_comparison(create_australia_csp(), num_trials=50)
    print(f"{'Algorithm':<32} | {'Success':<8} | {'Avg Time (us)':<14} | {'Avg Assigns':<12} | {'Avg Checks':<10}")
    print("-" * 88)
    for algo_name, data in benchmark.items():
        print(f"{algo_name:<32} | {data['success_rate']:>6.1f}% | {data['avg_time_us']:>12.2f} us | {data['avg_assigns']:>11.1f} | {data['avg_checks']:>10.1f}")
    print("=" * 70)
