from flask import Flask, request, render_template, send_file
import pandas as pd
import os
import time
from ortools.sat.python import cp_model

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    start_time = time.time()

    # Retrieve user inputs
    file = request.files['file']
    target_sum = float(request.form['target_sum'])
    tolerance = float(request.form['tolerance'])
    max_combination_size = int(request.form['max_combination_size'])
    max_solutions = int(request.form['max_solutions'])
    solver_timeout = float(request.form['solver_timeout'])

    # Read input file
    df = pd.read_excel(file)
    numbers = df.iloc[:, 0].tolist()

    # Initialize OR-Tools Model
    model = cp_model.CpModel()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = solver_timeout

    # Variables
    selection_vars = []
    for i in range(len(numbers)):
        var = model.NewBoolVar(f'x_{i}')
        selection_vars.append(var)

    # Constraint: Selected numbers must sum to target ± tolerance
    model.Add(sum(numbers[i] * selection_vars[i] for i in range(len(numbers))) >= target_sum - tolerance)
    model.Add(sum(numbers[i] * selection_vars[i] for i in range(len(numbers))) <= target_sum + tolerance)

    # Constraint: Limit number of selected numbers
    model.Add(sum(selection_vars) <= max_combination_size)

    # Solution Collector
    class SolutionPrinter(cp_model.CpSolverSolutionCallback):
        def __init__(self, selection_vars, numbers):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.selection_vars = selection_vars
            self.numbers = numbers
            self.solutions = []
        
        def on_solution_callback(self):
            solution = [self.numbers[i] for i in range(len(self.numbers)) if self.Value(self.selection_vars[i])]
            self.solutions.append(solution)
            if len(self.solutions) >= max_solutions:
                self.StopSearch()

    solution_printer = SolutionPrinter(selection_vars, numbers)
    status = solver.SearchForAllSolutions(model, solution_printer)

    # Save solutions to Excel
    result_filename = "solution.xlsx"
    with pd.ExcelWriter(result_filename, engine="xlsxwriter") as writer:
        for idx, solution in enumerate(solution_printer.solutions):
            pd.DataFrame(solution, columns=["Solution Values"]).to_excel(writer, sheet_name=f'Solution {idx + 1}', index=False)

    execution_time = round(time.time() - start_time, 4)
    return render_template('result.html', execution_time=execution_time)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
