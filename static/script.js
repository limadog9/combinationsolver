function addConstraint() {
    let constraintDiv = document.createElement("div");
    constraintDiv.className = "form-group";

    // Fetch available headers from dataset
    fetch('/get_columns')
        .then(response => response.json())
        .then(columns => {
            let select = document.createElement("select");
            select.name = "constraint_column[]";

            columns.forEach(column => {
                let option = document.createElement("option");
                option.value = column;
                option.textContent = column;
                select.appendChild(option);
            });

            constraintDiv.innerHTML = `
                <label>Column:</label>
            `;
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
        });
}

function removeConstraint(button) {
    button.parentNode.remove();
}
