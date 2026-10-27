"""Optional local NLP solve, not a dispatch qualification or AC replay."""
import argparse
import pyomo.environ as pyo
from pyomo.opt import check_optimal_termination
from build_acopf import main as build


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--solver', default='ipopt')
    args = parser.parse_args()
    model = build()
    # The original physical tap is continuous during assembly. Fix its declared
    # neutral value for this small continuous-NLP example; no integer recovery.
    for port in model.PORT:
        for t in model.T:
            model.tap[port,t].fix(model._ports[port]['neutral_position'])
    solver = pyo.SolverFactory(args.solver)
    if not solver.available(False):
        raise SystemExit(f'Solver {args.solver!r} is not installed. Build examples need no solver.')
    result = solver.solve(model, load_solutions=False)
    if not check_optimal_termination(result):
        raise SystemExit(f'Solve did not terminate optimally: {result.solver.termination_condition}')
    model.solutions.load_from(result)
    print('Objective:', pyo.value(model.obj))
    print('A solver termination is not independent physical validation.')


if __name__ == '__main__':
    main()
