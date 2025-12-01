document.getElementById('todo-form').addEventListener('submit', function(e) {
    // 1. STOP the form from reloading the page
    e.preventDefault();

    const contentInput = document.getElementById('content');
    const content = contentInput.value;

    // 2. Send the "Text Message" (Fetch Request)
    fetch('/api/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 'content': content })
    })
    .then(response => response.json()) // 3. Read the receipt
    .then(data => {
        // 4. If the server says "success", draw the new row manually
        if (data.result === 'success') {
            const table = document.getElementById('todo-table');
            // Create a new empty row at the bottom of the table
            const newRow = table.insertRow(-1); 

            // Create three empty cells
            const cell1 = newRow.insertCell(0);
            const cell2 = newRow.insertCell(1);
            const cell3 = newRow.insertCell(2);

            // Fill them with the data from the receipt
            cell1.innerHTML = data.content;
            cell2.innerHTML = data.date;
            
            // Re-create the links using the new ID
            cell3.innerHTML = `<a href="/delete/${data.id}">Delete</a> <br> <a href="/update/${data.id}">Update</a>`;

            // Clear the input box so it looks fresh
            contentInput.value = '';
        }
    });
});