function addConstraint() {
    let filePath = document.querySelector('input[name="file_path"]').value;
    if (!filePath) {
        alert("Please upload a file first.");
        return;
    }

    let constraintDiv = document.createElement("div");
    constraintDiv.className = "form-group";

    // Fetch available headers from dataset
    fetch(`/get_columns?file_path=${encodeURIComponent(filePath)}`)
        .then(response => response.json())
        .then(columns => {
            if (columns.length === 0) {
                alert("No valid columns found. Ensure your file has headers.");
                return;
            }

            let select = document.createElement("select");
            select.name = "constraint_column[]";

            columns.forEach(column => {
                let option = document.createElement("option");
                option.value = column;
                option.textContent = column;
                select.appendChild(option);
            });

            constraintDiv.appendChild(select);

            constraintDiv.innerHTML += `
                <select name="constraint_operator[]">
                    <option value="=">=</option>
                    <option value="<"><</option>
                    <option value=">">></option>
                    <option value="<="><=</option>
                    <option value=">=">>=</option>
                    <option value="!=">!=</option>
                </select>
                <input type="text" name="constraint_value[]" placeholder="Enter Value">
                <button type="button" class="remove-btn" onclick="removeConstraint(this)">❌ Remove</button>
            `;

            document.getElementById("constraints").appendChild(constraintDiv);
        })
        .catch(error => console.error("Error fetching columns:", error));
}

function removeConstraint(button) {
    button.parentNode.remove();
}
