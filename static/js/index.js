async function create_user_account(event, formElement) {
    event.preventDefault();

    const formData = new FormData(formElement);
    const urlEncodedData = new URLSearchParams();

    formData.forEach((value, key) => {
        urlEncodedData.append(key, value); // Transformation en application/x-www-form-urlencoded
    });

    const response = await fetch('http://localhost/create_user/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: urlEncodedData.toString(),
    });

    const result = await response.json();
    console.log(result);
}

