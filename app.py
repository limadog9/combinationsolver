from flask import Flask, request, render_template, send_file, url_for
from ortools.sat.python import cp_model
import pandas as pd
import time
import os

# Initialize Flask
app = Flask(__name__)

# Ensure necessary folders exist
UPLOAD_FOLDER = "/app/uploads"  # Use /app to make it Cloud Run compatible
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

        # Filter out unnamed columns
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
    max_solutions = int(request.form["max_solutions"])  # Get max solutions from user

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
    solver.parameters.max_time_in_seconds = 60.0  # Allow more time for multiple solutions

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
            if len(self.solutions) >= self.max_solutions:
                self.StopSearch()  # Stop once we hit max solutions

    solution_printer = SolutionPrinter(x, nums, max_solutions)

    solver.SearchForAllSolutions(model, solution_printer)

    if not solution_printer.solutions:
        return render_template("result.html", error_message="No valid solutions found.")

    # Save each solution on its own Excel sheet
    result_filename = os.path.join("/app", "solution.xlsx")
    with pd.ExcelWriter(result_filename, engine="xlsxwriter") as writer:
        for idx, solution in enumerate(solution_printer.solutions):
            solution_df = df[df[selected_column].isin(solution)]
            solution_df.to_excel(writer, sheet_name=f"Solution {idx+1}", index=False)

    return render_template(
        "result.html",
        achieved_sum="Multiple solutions found!",
        exec_time="N/A",
        download_link=url_for("download_file", filename="solution.xlsx", _external=True),
    )

@app.route("/download/<filename>")
def download_file(filename):
    """ Allow the user to download the generated Excel file. """
    file_path = os.path.join("/app", filename)  # Ensure correct path

    if not os.path.exists(file_path):
        print(f"❌ Error: File {file_path} not found!")  # Debugging Step
        return f"File not found: {file_path}", 404

    print(f"✅ Serving file: {file_path}")  # Debugging Step
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
