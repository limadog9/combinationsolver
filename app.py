from flask import Flask, request, render_template, send_file, url_for
from ortools.sat.python import cp_model
import pandas as pd
import os
import time

# Initialize Flask
app = Flask(__name__)

# Ensure results folder exists
RESULTS_FOLDER = "results"
os.makedirs(RESULTS_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file uploaded", 400
        file = request.files["file"]
        
        file_path = os.path.join(RESULTS_FOLDER, file.filename)
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
    model.Minimize(sum(x))

    solver = cp_model.CpSolver()
    start_time = time.time()
    status = solver.Solve(model)
    end_time = time.time()

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        solution = [nums[i] for i in range(len(nums)) if solver.Value(x[i]) == 1]
        achieved_sum = sum(solution)
        exec_time = round(end_time - start_time, 4)

        selected_rows = df[df[selected_column].isin(solution)]
        selected_rows = selected_rows.loc[:, ~selected_rows.columns.str.startswith("Unnamed")]

        result_filename = os.path.join(RESULTS_FOLDER, "solution.xlsx")
        selected_rows.to_excel(result_filename, index=False)

        return render_template(
            "result.html",
            achieved_sum=achieved_sum,
            exec_time=exec_time,
            download_link=url_for("download_file", filename="solution.xlsx", _external=True),
        )
    else:
        return render_template(
            "result.html",
            error_message="No valid solution found.",
        )

@app.route("/download/<filename>")
def download_file(filename):
    """ Allow the user to download the generated Excel file. """
    file_path = os.path.join(RESULTS_FOLDER, filename)

    if not os.path.exists(file_path):
        return "File not found", 404

    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
