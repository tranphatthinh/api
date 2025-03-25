document.getElementById("loginForm").addEventListener("submit", function (event) {
    event.preventDefault();

    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;

    fetch("http://127.0.0.1:5000/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ email: email, password: password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.api_key) {
            console.log("API Key nhận được:", data.api_key);
            window.location.href = `/g/${data.api_key}`; // Chuyển trang với API Key
        } else {
            alert("Đăng nhập thất bại!");
        }
    })
    .catch(error => console.error("Lỗi:", error));
});