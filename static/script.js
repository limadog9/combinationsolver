function addConstraint() {
    let div = document.createElement("div");
    div.className = "form-group";
    div.innerHTML = `
        <select name="constraint_column[]">
            <option value="">Select Column</option>
            <option value="column1">Column 1</option>
            <option value="column2">Column 2</option>
        </select>
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
    document.getElementById("constraints").appendChild(div);
}

function removeConstraint(button) {
    button.parentNode.remove();
}
