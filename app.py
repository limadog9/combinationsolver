from flask import Flask, request, render_template, send_from_directory, url_for
from ortools.sat.python import cp_model
import pandas as pd
import time
import os

# ✅ Flask app must be defined BEFORE routes
app = Flask(__name__)

UPLOAD_FOLDER = "/app/uploads"
RESULTS_FOLDER = "/app/results"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file uploaded", 400
        file = request.files["file"]
        
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        df = pd.read_excel(file_path)

        valid_columns = [col for col in df.columns if not col.startswith("Unnamed")]

        return render_template("select_column.html", columns=valid_columns, file_path=file_path)

    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    file_path = request.form["file_path"]
    selected_column = request.form["selected_column"]
    max_combination_size = int(request.form["max_combination_size"])
    target_sum = float(request.form["target_sum"])
    tolerance = float(request.form["tolerance"])
    max_solutions = int(request.form["max_solutions"])

    df = pd.read_excel(file_path)

    if selected_column not in df.columns:
        return "Invalid column selection", 400

    nums = df[selected_column].dropna().tolist()

    model = cp_model.CpModel()
    x = [model.NewBoolVar(f"x{i}") for i in range(len(nums))]

    scaling_factor = 100
    int_nums = [int(num * scaling_factor) for num in nums]
    int_target_sum = int(target_sum * scaling_factor)
    int_tolerance = int(tolerance * scaling_factor)

    total_sum = sum(x[i] * int_nums[i] for i in range(len(int_nums)))

    model.Add(total_sum >= int_target_sum - int_tolerance)
    model.Add(total_sum <= int_target_sum + int_tolerance)
    model.Add(sum(x) <= max_combination_size)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0

    print("🚀 Solver started...")

    class SolutionPrinter(cp_model.CpSolverSolutionCallback):
        def __init__(self, x_vars, numbers, max_solutions):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.x_vars = x_vars
            self.numbers = numbers
            self.solutions = []
            self.max_solutions = max_solutions

        def OnSolutionCallback(self):
            solution = [self.numbers[i] for i in range(len(self.x_vars)) if self.Value(self.x_vars[i]) == 1]
            self.solutions.append(solution)
            print(f"✅ Found solution {len(self.solutions)}: {solution}")
            if len(self.solutions) >= self.max_solutions:
                self.StopSearch()

    solution_printer = SolutionPrinter(x, nums, max_solutions)

    solver.SearchForAllSolutions(model, solution_printer)

    if not solution_printer.solutions:
        print("❌ No valid solutions found!")
        return render_template("result.html", error_message="No valid solutions found.")

    print(f"✅ Total solutions found: {len(solution_printer.solutions)}")

    # Ensure the results folder exists
    os.makedirs(RESULTS_FOLDER, exist_ok=True)

    result_filename = os.path.join(RESULTS_FOLDER, "solution.xlsx")
    with pd.ExcelWriter(result_filename, engine="xlsxwriter") as writer:
        for idx, solution in enumerate(solution_printer.solutions):
            solution_df = df[df[selected_column].isin(solution)]
            solution_df.to_excel(writer, sheet_name=f"Solution {idx+1}", index=False)

    print(f"✅ File saved at: {result_filename}")

    return render_template(
        "result.html",
        achieved_sum=f"{len(solution_printer.solutions)} solutions found!",
        exec_time="Check logs for time",
        download_link=url_for("download_file", filename="solution.xlsx", _external=True),
    )

@app.route("/download/<filename>")
def download_file(filename):
    """ Ensure file is served correctly with explicit headers. """
    file_path = os.path.join(RESULTS_FOLDER, filename)

    if not os.path.exists(file_path):
        print(f"❌ Error: File {file_path} not found!")
        return f"File not found: {file_path}", 404

    print(f"✅ Serving file: {file_path}")

    return send_from_directory(
        RESULTS_FOLDER,
        filename,
        as_attachment=True
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
