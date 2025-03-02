from flask import Flask, request, render_template, send_file, url_for
from ortools.sat.python import cp_model
import pandas as pd
import time
import os
import tempfile

# Initialize Flask
app = Flask(__name__)

# Use temporary folders for uploads and results
UPLOAD_FOLDER = tempfile.mkdtemp()
RESULTS_FOLDER = tempfile.mkdtemp()

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
    max_combination_size = request.form["max_combination_size"]
    target_sum = request.form["target_sum"]
    tolerance = request.form["tolerance"]
    max_solutions = request.form["max_solutions"]
    solver_timeout = request.form["solver_timeout"]

    # Convert user input to correct types
    try:
        max_combination_size = int(max_combination_size)
        target_sum = float(target_sum)
        tolerance = float(tolerance)
        max_solutions = int(max_solutions)
        solver_timeout = float(solver_timeout)
    except ValueError:
        return "Invalid input for one or more fields.", 400

    df = pd.read_excel(file_path)

    if selected_column not in df.columns:
        return "Invalid column selection", 400

    nums = df[selected_column].dropna().tolist()

    # Reduce problem size to prevent Render from killing process
    if len(nums) > 500:
        nums = nums[:500]  # Keep first 500 numbers

    # Debug: Print information before optimization
    print(f"Target sum: {target_sum}, Tolerance: {tolerance}")
    print(f"Max combination size: {max_combination_size}")
    print(f"Max solutions requested: {max_solutions}")
    print(f"Solver timeout: {solver_timeout} seconds")
    print(f"Filtered dataset size: {len(nums)}")

    model = cp_model.CpModel()
    x = [model.NewBoolVar(f"x{i}") for i in range(len(nums))]

    # Scaling factor to avoid float precision issues
    scaling_factor = 100
    int_nums = [int(num * scaling_factor) for num in nums]
    int_target_sum = int(target_sum * scaling_factor)
    int_tolerance = int(tolerance * scaling_factor)

    total_sum = sum(x[i] * int_nums[i] for i in range(len(int_nums)))

    model.Add(total_sum >= int_target_sum - int_tolerance)
    model.Add(total_sum <= int_target_sum + int_tolerance)

    model.Add(sum(x) <= max_combination_size)
    model.Minimize(sum(x))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = solver_timeout

    solutions = []
    start_time = time.time()

    for i in range(max_solutions):
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            solution = [nums[i] for i in range(len(nums)) if solver.Value(x[i]) == 1]
            
            if solution in solutions:
                continue  # Skip duplicate solutions
            
            solutions.append(solution)
            print(f"Solution {len(solutions)}: {solution}")

            # Prevent duplicate solutions by adding constraint
            model.Add(sum(x[j] for j in range(len(nums)) if solver.Value(x[j]) == 1) <= max_combination_size - 1)
        else:
            break  # Stop if no more solutions are found

    end_time = time.time()

    if len(solutions) == 0:
        return render_template("result.html", error_message="No valid solutions found.")

    # Save multiple solutions to an Excel file (each on its own sheet)
    result_filename = os.path.join(RESULTS_FOLDER, "solutions.xlsx")
    with pd.ExcelWriter(result_filename, engine='openpyxl') as writer:
        for i, solution in enumerate(solutions):
            selected_rows = df[df[selected_column].isin(solution)]
            selected_rows.to_excel(writer, sheet_name=f"Solution {i+1}", index=False)

    return render_template(
        "result.html",
        achieved_sum="Multiple solutions found",
        exec_time=round(end_time - start_time, 4),
        download_link=url_for("download_file", filename="solutions.xlsx", _external=True),
    )

@app.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join(RESULTS_FOLDER, filename)

    if not os.path.exists(file_path):
        return "File not found", 404

    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
