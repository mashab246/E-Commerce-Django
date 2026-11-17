const form = document.getElementById("productForm");
const extraFields = document.getElementById("extraFields");
const messageBox = document.getElementById("stockMessage");
const productTableBody = document.getElementById("productTableBody");
const categorySelect = document.getElementById("productType");

// 1. Get all form fields, including inputs, textarea and select.
function getInputFields() {
    return form.querySelectorAll("input, textarea, select");
}

// 2. Check whether a field is empty.
function isEmpty(field) {
    return field.value.trim() === "";
}

// 3. Get the name of a field from its label.
function getFieldName(field) {
    const label = form.querySelector(`label[for="${field.id}"]`);

    if (label) {
        return label.textContent.trim().replace(/:$/, "");
    }

    return field.name || field.id || "Unnamed field";
}

// 4. Find all empty fields.
function findEmptyFields() {
    const fields = getInputFields();
    const emptyFields = [];

    for (let i = 0; i < fields.length; i++) {
        const field = fields[i];

        if (isEmpty(field)) {
            emptyFields.push(getFieldName(field));
        }
    }

    return emptyFields;
}

// 5. Display an error message.
function showError(emptyFields) {
    messageBox.className = "error";
    messageBox.textContent =
        "Product not added. Please fill in: " +
        emptyFields.join(", ") + ".";
}

// 6. Display a success message.
function showSuccess() {
    messageBox.className = "success";
    messageBox.textContent = "Product added successfully!";
}

// 7. Display fields depending on the selected category.
function displayCategoryFields() {
    const category = categorySelect.value;

    // Clear the previous category fields.
    extraFields.replaceChildren();

    if (category === "") {
        return;
    }

    let fieldLabel = "";
    let fieldId = "";

    if (category === "electronics") {
        fieldLabel = "Warranty Period (months)";
        fieldId = "warranty";
    } else if (category === "clothes") {
        fieldLabel = "Clothing Size";
        fieldId = "clothingSize";
    } else if (category === "shoes") {
        fieldLabel = "Shoe Size";
        fieldId = "shoeSize";
    }

    if (fieldId === "") {
        return;
    }

    const group = document.createElement("div");
    group.className = "form-group";

    const label = document.createElement("label");
    label.htmlFor = fieldId;
    label.textContent = fieldLabel;

    const input = document.createElement("input");
    input.id = fieldId;
    input.name = fieldId;
    input.required = true;

    if (category === "electronics") {
        input.type = "number";
        input.min = "0";
        input.step = "1";
    } else {
        input.type = "text";
    }

    group.append(label, input);
    extraFields.appendChild(group);
}

// 8. Generate the next product ID.
function generateProductId() {
    let highestId = 0;

    const rows = productTableBody.querySelectorAll("tr");

    rows.forEach(function (row) {
        const idText = row.cells[0]?.textContent.trim();
        const match = idText?.match(/^P(\d+)$/);

        if (match) {
            highestId = Math.max(highestId, Number(match[1]));
        }
    });

    return "P" + String(highestId + 1).padStart(3, "0");
}

// 9. Format the price in Ugandan shillings.
function formatPrice(price) {
    return "UGX " + Number(price).toLocaleString("en-UG");
}

// 10. Add a product to the table.
function addProduct() {
    const productName = document.getElementById("productName").value.trim();
    const brand = document.getElementById("brand").value.trim();
    const description = document.getElementById("description").value.trim();
    const price = document.getElementById("price").value;
    const stock = document.getElementById("stock").value;
    const vendor = document.getElementById("vendor").value.trim();

    const categoryText =
        categorySelect.options[categorySelect.selectedIndex].text;

    const productId = generateProductId();

    const row = document.createElement("tr");

    const values = [
        productId,
        productName,
        brand,
        formatPrice(price),
        stock,
        vendor,
        categoryText
    ];

    values.forEach(function (value) {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.appendChild(cell);
    });

    productTableBody.appendChild(row);

    // Keep description and category-specific information available on the row without adding more visible columns.
    row.dataset.description = description;

    const categoryField = extraFields.querySelector("input");

    if (categoryField) {
        row.dataset[categoryField.id] = categoryField.value.trim();
    }
}

// 11. Handle form submission.
function handleSubmit(event) {
    event.preventDefault();

    const emptyFields = findEmptyFields();

    if (emptyFields.length > 0) {
        showError(emptyFields);
        return;
    }

    // Check that price and stock are valid non-negative numbers.
    const price = Number(document.getElementById("price").value);
    const stock = Number(document.getElementById("stock").value);

    if (
        !Number.isFinite(price) ||
        price < 0 ||
        !Number.isFinite(stock) ||
        stock < 0 ||
        !Number.isInteger(stock)
    ) {
        messageBox.className = "error";
        messageBox.textContent =
            "Price must be non-negative and stock must be a non-negative whole number.";
        return;
    }

    addProduct();
    showSuccess();

    // Reset the form and remove category-specific fields.
    form.reset();
    extraFields.replaceChildren();
}

// 12. Listen for category changes.
categorySelect.addEventListener("change", displayCategoryFields);

// 13. Listen for form submission.
form.addEventListener("submit", handleSubmit);
