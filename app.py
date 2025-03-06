from flask import Flask, request, send_file, render_template
import pandas as pd
import ortools.sat.python.cp_model as cp_model
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def find_combinations(numbers, target, max_numbers, tolerance):
    model = cp_model.CpModel()
    n = len(numbers)

    # Boolean variables for selection
    selection = [model.NewBoolVar(f'select_{i}') for i in range(n)]

    # Constraints
    model.Add(sum(numbers[i] * selection[i] for i in range(n)) >= target - tolerance)
    model.Add(sum(numbers[i] * selection[i] for i in range(n)) <= target + tolerance)
    model.Add(sum(selection) <= max_numbers)

    # Solver
    solver = cp_model.CpSolver()
    solution_list = []

    class SolutionCollector(cp_model.CpSolverSolutionCallback):
        def __init__(self, selection, numbers):
            super().__init__()
            self.selection = selection
            self.numbers = numbers
            self.solutions = []

        def OnSolutionCallback(self):
            selected = [self.numbers[i] for i in range(len(self.numbers)) if self.Value(self.selection[i])]
            self.solutions.append(selected)

    collector = SolutionCollector(selection, numbers)
    solver.SearchForAllSolutions(model, collector)

    return collector.solutions

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        target = float(request.form["target"])
        max_numbers = int(request.form["max_numbers"])
        tolerance = float(request.form["tolerance"])
        column_name = request.form["column"]

        if file:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            df = pd.read_excel(file_path)

            if column_name not in df.columns:
                return "Invalid column selected. Please try again."

            numbers = df[column_name].dropna().tolist()
            solutions = find_combinations(numbers, target, max_numbers, tolerance)

            # Save results to an Excel file
            result_df = pd.DataFrame({f"Solution {i+1}": solution for i, solution in enumerate(solutions)})
            output_path = os.path.join(UPLOAD_FOLDER, "solutions.xlsx")
            result_df.to_excel(output_path, index=False)

            return send_file(output_path, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
