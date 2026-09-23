"""
Constraint Satisfaction Problem (CSP) - Map Coloring Problem
Based on Lecture Slides:
- Variables: WA, NT, SA, Q, NSW, V, T
- Domains: {Red, Green, Blue}
- Binary Constraints: Adjacent regions must not have the same color
- Search Algorithms:
  1. Simple Recursive Backtracking Search (Slide 12-13)
  2. Backtracking with MRV (Minimum Remaining Values) (Slide 5, 13)
  3. Backtracking with Forward Checking (Slide 5, 14-22)
"""

from typing import Dict, List, Set, Any, Optional, Tuple, Callable
import copy


class CSP:
    def __init__(self, variables: List[str], domains: Dict[str, List[Any]], neighbors: Dict[str, List[str]]):
        self.variables = variables
        self.domains = {v: list(domains[v]) for v in variables}
        self.neighbors = {v: list(neighbors.get(v, [])) for v in variables}
        # Statistics for analysis
        self.assign_count = 0
        self.backtrack_count = 0

    def is_consistent(self, var: str, value: Any, assignment: Dict[str, Any]) -> bool:
        """
        Check if assigning `value` to `var` violates any constraints with already assigned neighbors.
        Constraint: Adjacent regions must have different colors (var != neighbor).
        """
        for neighbor in self.neighbors.get(var, []):
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
    """
    Recursive Backtracking algorithm (Slide 12-13):
    1. if assignment is complete then return assignment
    2. var <- SELECT-UNASSIGNED-VARIABLE(Variables[csp], assignment, csp)
    3. for each value in ORDER-DOMAIN-VALUES(var, assignment, csp) do
    4.   if value is consistent with assignment according to Constraints[csp] then
    5.     add {var = value} to assignment
    6.     result <- RECURSIVE-BACKTRACKING(assignment, csp)
    7.     if result != failure then return result
    8.     remove {var = value} from assignment
    9. return failure
    """
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
    """
    MRV heuristic: Choose the variable with the fewest legal values remaining.
    """
    unassigned = [v for v in csp.variables if v not in assignment]
    # Find min remaining legal values
    def count_legal_values(v: str) -> int:
        return sum(1 for val in current_domains[v] if csp.is_consistent(v, val, assignment))

    return min(unassigned, key=count_legal_values)


def backtracking_search_mrv(csp: CSP, verbose: bool = False) -> Optional[Dict[str, Any]]:
    csp.assign_count = 0
    csp.backtrack_count = 0
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
            if value in new_domains[neighbor]:
                new_domains[neighbor].remove(value)
                # If domain becomes empty, failure (triggers backtracking immediately!)
                if len(new_domains[neighbor]) == 0:
                    return False, new_domains

    return True, new_domains


def backtracking_search_fc(
    csp: CSP,
    variable_order: Optional[List[str]] = None,
    value_order: Optional[Dict[str, List[Any]]] = None,
    verbose: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Backtracking Search with Forward Checking.
    If variable_order is given (e.g. ['WA', 'Q', 'V', ...]), it follows that order.
    If value_order is given, it tries values in that specified order per variable.
    """
    csp.assign_count = 0
    csp.backtrack_count = 0
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

    # Determine domain exploration order
    if value_order and var in value_order:
        values_to_try = [v for v in value_order[var] if v in domains[var]]
    else:
        values_to_try = list(domains[var])

    for value in values_to_try:
        if csp.is_consistent(var, value, assignment):
            # Try forward checking
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
    Step-by-step walkthrough reproducing Slides 14-22:
    - Slide 15: Assign WA = Red
    - Slide 16: Assign Q = Green
    - Slide 17: Assign V = Blue
    - Slides 18-22: SA domain is wiped out (len=0) because SA is adjacent to WA, Q, and V!
      Forward Checking detects this empty domain immediately and triggers Backtrack.
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


def validate_solution(assignment: Dict[str, Any], csp: CSP) -> Tuple[bool, List[str]]:
    """Validates whether a solution satisfies all CSP constraints."""
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
    print("=" * 60)
    print("1. Standard Backtracking Search (Slides 12-13)")
    print("=" * 60)
    csp1 = create_australia_csp()
    sol1 = backtracking_search(csp1, verbose=True)
    valid1, errs1 = validate_solution(sol1, csp1)
    print(f"\nSolution: {sol1}")
    print(f"Valid: {valid1}, Assignments: {csp1.assign_count}, Backtracks: {csp1.backtrack_count}\n")

    print("=" * 60)
    print("2. Backtracking Search with MRV Heuristic (Slide 5)")
    print("=" * 60)
    csp2 = create_australia_csp()
    sol2 = backtracking_search_mrv(csp2, verbose=True)
    valid2, errs2 = validate_solution(sol2, csp2)
    print(f"\nSolution: {sol2}")
    print(f"Valid: {valid2}, Assignments: {csp2.assign_count}, Backtracks: {csp2.backtrack_count}\n")

    print("=" * 60)
    print("3. Demonstration of Slide 14-22 (Forward Checking & Backtrack)")
    print("=" * 60)
    # (A) Explicit step-by-step walkthrough of Slide 14-22
    demonstrate_slide_14_to_22()

    # (B) Running FC Search with Slide 14-22 path (WA=Red, Q=Green, V=Blue) to show branch pruning & backtrack
    print("-" * 60)
    print("Executing Backtracking Search FC with Slide 14-22 path:")
    print("Variable order: WA, Q, V, NSW, NT, SA, T")
    print("Value priority: WA=[Red], Q=[Green, Red, Blue], V=[Blue, Red, Green]")
    print("-" * 60)
    csp3 = create_australia_csp()
    slide_order = ["WA", "Q", "V", "NSW", "NT", "SA", "T"]
    slide_values = {
        "WA": ["Red", "Green", "Blue"],
        "Q": ["Green", "Red", "Blue"],
        "V": ["Blue", "Red", "Green"]
    }
    sol3 = backtracking_search_fc(csp3, variable_order=slide_order, value_order=slide_values, verbose=True)
    valid3, errs3 = validate_solution(sol3, csp3)
    print(f"\nSolution: {sol3}")
    print(f"Valid: {valid3}, Assignments: {csp3.assign_count}, Backtracks: {csp3.backtrack_count}\n")
