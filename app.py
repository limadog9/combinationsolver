from flask import Flask, request, render_template, send_file, url_for
import pandas as pd
import os
import time
from ortools.sat.python import cp_model

app = Flask(__name__)

RESULTS_FOLDER = "results"
os.makedirs(RESULTS_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    start_time = time.time()

    file = request.files['file']
    target_sum = float(request.form['target_sum'])
    tolerance = float(request.form['tolerance'])
    max_combination_size = int(request.form['max_combination_size'])
    max_solutions = int(request.form['max_solutions'])
    solver_timeout = float(request.form['solver_timeout'])

    df = pd.read_excel(file)
    numbers = df.iloc[:, 0].tolist()

    model = cp_model.CpModel()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = solver_timeout

    selection_vars = [model.NewBoolVar(f'x_{i}') for i in range(len(numbers))]

    model.Add(sum(numbers[i] * selection_vars[i] for i in range(len(numbers))) >= target_sum - tolerance)
    model.Add(sum(numbers[i] * selection_vars[i] for i in range(len(numbers))) <= target_sum + tolerance)
    model.Add(sum(selection_vars) <= max_combination_size)

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
    solver.SearchForAllSolutions(model, solution_printer)

    result_filename = os.path.join(RESULTS_FOLDER, "solution.xlsx")
    with pd.ExcelWriter(result_filename, engine="xlsxwriter") as writer:
        for idx, solution in enumerate(solution_printer.solutions):
            pd.DataFrame(solution, columns=["Solution Values"]).to_excel(writer, sheet_name=f'Solution {idx + 1}', index=False)

    execution_time = round(time.time() - start_time, 4)
    return render_template('result.html', execution_time=execution_time, download_link=url_for('download_file', filename="solution.xlsx", _external=True))

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(RESULTS_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
