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
